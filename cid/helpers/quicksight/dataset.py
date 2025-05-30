import logging
from uuid import uuid4
from copy import deepcopy

import yaml

from cid.helpers.quicksight.resource import CidQsResource

logger = logging.getLogger(__name__)


class Dataset(CidQsResource):

    def __init__(self, raw: dict, qs=None, athena=None) -> None:
        super().__init__(raw)
        self.qs = qs

    def describe(self) -> str:
        if not self.qs:
            raise Exception('Need to define me with qs')
        self.raw = self.qs.client.describe_data_set(AwsAccountId=self.account_id, DataSetId=self.id).get('DataSet')
        return self

    @property
    def id(self) -> str:
        return self.get_property('DataSetId')

    @property
    def columns(self) -> list:
        if not 'OutputColumns' in self.raw: self.describe()
        return self.get_property('OutputColumns')

    @property
    def datasources(self) -> list:
        if not 'PhysicalTableMap' in self.raw: self.describe()
        _datasources = []
        try:
            for table_map in self.raw.get('PhysicalTableMap', {}).values():
                ds = table_map.get('RelationalTable', {}).get(
                    'DataSourceArn', '').split('/')[-1]
                if ds:
                    _datasources.append(ds)
        except Exception as e:
            logger.debug(e, exc_info=True)
        return sorted(list(set(_datasources)))

    @property
    def schemas(self) -> list:
        if not 'PhysicalTableMap' in self.raw: self.describe()
        schemas = []
        try:
            for table_map in self.get_property('PhysicalTableMap').values():
                schema = table_map.get(
                    'RelationalTable', {}).get('Schema', None)
                if schema:
                    schemas.append(schema)
        except Exception as e:
            logger.debug(e, exc_info=True)
        return sorted(list(set(schemas)))

    @staticmethod
    def patch(dataset, custom_fields={}, athena=None):
        ''' patch dataset to add custom fields and all athena fields
        dataset: qs dataset definition
        custom_fields: a dict with name of custom field as a key and a code as value
        athena: cid athena helper
        returns updated dataset definition
        '''
        def _get_athena_columns(table, database=None):
            '''returns athena columns'''
            return [
                line[0].split()
                for line in athena.query(
                    f'SHOW COLUMNS FROM {table}',
                    include_header=True, database=database
                )
            ]

        def _replace_columns(existing_columns, new_columns):
            '''replace columns but keep the order, ignore case changes
                assert _replace_columns(
                    [{'Name': 'a'}, {'Name': 'B'}, {'Name': 'c'}],
                    [{'Name': 'A'}, {'Name': 'b'}, {'Name': 'd'}]) \
                 == [{'Name': 'a'}, {'Name': 'B'}, {'Name': 'd'}]
            Different types will be replaced
            '''
            existing_columns = [
                existing_col
                for existing_col in existing_columns
                if str(existing_col).lower() in [str(c).lower() for c in new_columns]
            ] # filter out old
            for col in new_columns: # add new
                if col['Name'].lower() not in [c['Name'].lower() for c in existing_columns]:
                    existing_columns.append(col)
                #REFACTOR: what if col is there but another type?
            return existing_columns

        def _athena_to_qs_type(col, athena_type):
            '''map athena type to QS type
             The following data types are supported in SPICE: Date, Decimal-fixed, Decimal-float, Integer, and String.
            https://docs.aws.amazon.com/quicksight/latest/user/supported-data-types.html
            https://docs.aws.amazon.com/quicksight/latest/user/supported-data-types-and-values.html
            '''
            if 'string'    in athena_type: return {'Name': col, 'Type': 'STRING'}
            if 'varchar'   in athena_type: return {'Name': col, 'Type': 'STRING'}
            if 'char'      in athena_type: return {'Name': col, 'Type': 'STRING'}
            if 'timestamp' in athena_type: return {'Name': col, 'Type': 'DATETIME'}
            if 'date'      in athena_type: return {'Name': col, 'Type': 'DATETIME'}
            if 'time'      in athena_type: return {'Name': col, 'Type': 'DATETIME'}
            if 'bigint'    in athena_type: return {'Name': col, 'Type': 'INTEGER'}
            if 'int'       in athena_type: return {'Name': col, 'Type': 'INTEGER'}
            if 'decimal'   in athena_type: return {'Name': col, 'Type': 'DECIMAL', 'SubType': 'FIXED'}
            if 'double'    in athena_type: return {'Name': col, 'Type': 'DECIMAL', 'SubType': 'FIXED'}
            if 'real'      in athena_type: return {'Name': col, 'Type': 'DECIMAL', 'SubType': 'FIXED'} #is it better fit for fixed vs float Decimals
            logger.warning(f'Unknown Athena type {athena_type} for {col}. Will use STRING. This might affect dashboard.')
            return {'Name': col, 'Type': 'STRING'}

        dataset = deepcopy(dataset)

        # Get root logical table (the one that is not joined to any other logical table)
        root_lt = None
        for lt in list(dataset['LogicalTableMap'].keys()):
            if not any(lt in str(_lt["Source"]) for _lt in dataset['LogicalTableMap'].values()):
                root_lt = dataset['LogicalTableMap'][lt]
                break
        else:
            raise ValueError(f'Unable to find a root logical table in the dataset {dataset}')
        projected_cols = next(ds['ProjectOperation']["ProjectedColumns"] for ds in root_lt['DataTransforms'] if 'ProjectOperation' in ds)

        # Update each PhysicalTableMap with all columns from athena views
        all_columns = []
        for pt in dataset['PhysicalTableMap'].values():
            table_name = pt['RelationalTable']['Name']
            database = pt['RelationalTable']['Schema']
            columns = _get_athena_columns(table_name, database)
            logger.trace(f'columns = {columns}')

            new_columns = [_athena_to_qs_type(name, athena_type) for name, athena_type in columns]
            #for col in new_columns:
            #    if col['Name'] in [existing_col['Name'] for existing_col in all_columns]: #FIXME not all_columns so far but must be all cols before modification
            #        col['Name'] = f'{col["Name"]}[{table_name}]'
            pt['RelationalTable']['InputColumns'] = _replace_columns(pt['RelationalTable']['InputColumns'], new_columns)
            all_columns += [col['Name'] for col in pt['RelationalTable']['InputColumns']]

        # Add all needed calc fields
        existing_create_columns = [dt.get("CreateColumnsOperation", {}).get('Columns', [None])[0] for dt in root_lt.get('DataTransforms', []) if dt.get("CreateColumnsOperation")]
        for col_name, expression in custom_fields.items():
            existing_create_column = next((c for c in existing_create_columns if c["ColumnName"] == col_name), None)
            if existing_create_column:
                existing_create_column['Expression'] = expression
                logger.trace(f'Custom field {col_name} updated to {repr(expression)}')
            else:
                root_lt['DataTransforms'].insert(0, {
                    "CreateColumnsOperation": {
                        "Columns": [
                            {
                                "ColumnName": col_name,
                                "ColumnId": str(uuid4()),
                                "Expression": expression
                            }
                        ]
                    }
                })
                logger.trace(f'Custom field {col_name} added with code {repr(expression)}')
                all_columns.append(col_name)

        # Add all new cols to projected columns
        for col in set(all_columns):
            if col.lower() not in [c.lower() for c in projected_cols]:
                projected_cols.append(col)

        # filter out all columns that cannot be used for dataset creation
        update_ = {key: value for key, value in dataset.items() if key in 'DataSetId, Name, PhysicalTableMap, LogicalTableMap, ImportMode, ColumnGroups, FieldFolders, RowLevelPermissionDataSet, RowLevelPermissionTagConfiguration, ColumnLevelPermissionRules, DataSetUsageConfiguration, DatasetParameters'.split(', ')}
        logger.trace(f'update_ = {update_}')

        return update_


    def to_diffable_structure(self):
        """ return diffable text """
        data = {}
        data['Name'] = self.raw.get('Name')
        data['Data'] = {}
        join_clauses = {}
        for key, ltm in self.raw['LogicalTableMap'].items():
            alias = ltm.get('Alias')
            source = ltm.get('Source')
            name = alias
            element = {}
            if 'PhysicalTableId' in source:
                phtid = source['PhysicalTableId']
                phy = self.raw['PhysicalTableMap'][phtid]
                if 'RelationalTable' in phy:
                    rel = phy['RelationalTable']
                    name +='(' + '/'.join([rel.get('Catalog', 'AwsDataCatalog'),rel.get('Schema', ''), rel.get('Name', '') ]) + ')'
                    element['columns'] = sorted([col['Type']+ ' ' + col['Name'] for col in rel.get('InputColumns', [])])
                else:
                    element['columns'] = [f"Unsupported PhysicalTableMap in {phtid}: {phy.keys()}"]
                data['Data'][name] = element
            elif 'JoinInstruction' in source:
                join = source['JoinInstruction']
                right_id = join.get('RightOperand')
                right_alias = self.raw['LogicalTableMap'].get(right_id).get('Alias')
                alias = right_alias
                if alias.startswith('Intermediate Table'):
                    left_id = join.get('LeftOperand')
                    left_alias = self.raw['LogicalTableMap'].get(left_id).get('Alias')
                    alias = left_alias
                join_clauses[alias] = join.get('OnClause')
            else:
                data['Data'][name] = {'columns': [f'Unsupported diff for source {source}']}
        for alias, join in join_clauses.items():
            if isinstance(data['Data'].get(alias), dict) :
                data['Data'][alias]['clause'] = join
        return (yaml.safe_dump(data))