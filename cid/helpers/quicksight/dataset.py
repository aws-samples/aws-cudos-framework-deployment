import logging

import yaml

from cid.helpers.quicksight.resource import CidQsResource

logger = logging.getLogger(__name__)


class Dataset(CidQsResource):

    @property
    def id(self) -> str:
        return self.get_property('DataSetId')

    @property
    def columns(self) -> list:
        return self.get_property('OutputColumns')

    @property
    def datasources(self) -> list:
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