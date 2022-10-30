from io import StringIO
import json
import logging
from string import Template
import time, csv

from pkg_resources import resource_string

from cid.base import CidBase
from cid.utils import get_parameter, get_parameters
from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

class Athena(CidBase):
    # Define defaults
    defaults = {
        'CatalogName': 'AwsDataCatalog',
        'DatabaseName': 'customer_cur_data',
        'WorkGroup': 'primary'
    }
    _CatalogName = None
    _DatabaseName = None
    _WorkGroup = None
    ahq_queries = None
    _metadata = dict()
    _resources = dict()
    _client = None
    region: str = None

    def __init__(self, session, resources: dict=None) -> None:
        super().__init__(session)
        self._resources = resources

    @property
    def client(self):
        if not self._client:
            self._client = self.session.client('athena', region_name=self.region)
        return self._client

    @property
    def CatalogName(self) -> str:
        """ Check if AWS Datacalog and Athena database exist """
        if not self._CatalogName:
            # Get AWS Glue DataCatalogs
            glue_data_catalogs = [d for d in self.list_data_catalogs() if d['Type'] == 'GLUE']
            if not len(glue_data_catalogs):
                logger.error('AWS DataCatog of type GLUE not found!')
                self._status = 'AWS DataCatog of type GLUE not found'
            if len(glue_data_catalogs) == 1:
                self._CatalogName = glue_data_catalogs.pop().get('CatalogName')
            elif len(glue_data_catalogs) > 1:
                # Ask user
                self._CatalogName = get_parameter(
                    param_name='glue-data-catalog',
                    message="Select AWS DataCatalog to use",
                    choices=[catalog.get('CatalogName') for catalog in glue_data_catalogs],
                )
            logger.info(f'Using datacatalog: {self._CatalogName}')
        return self._CatalogName

    @CatalogName.setter
    def set_catalog_name(self, catalog):
        self._CatalogName = catalog

    @property
    def DatabaseName(self) -> str:
        """ Check if Athena database exist """

        if not self._DatabaseName:
            if get_parameters().get('athena-database'):
                self._DatabaseName = get_parameters().get('athena-database')
                try:
                    if not self.get_database(self._DatabaseName):
                        raise CidCritical(f'Database {self._DatabaseName} not found in Athena catalog {self.CatalogName}')
                except Exception as exc:
                    if 'AccessDeniedException' in str(exc):
                        logger.warning(f'{type(exc)} - Missing athena:GetDatabase permission. Cannot verify existance of {self._DatabaseName} in {self.CatalogName}. Hope you have it there.')
                        return self._DatabaseName
                    raise
            # Get AWS Athena databases
            athena_databases = self.list_databases()
            if not len(athena_databases):
                self._status = 'AWS Athena databases not found'
                raise CidCritical(self._status)
            if len(athena_databases) == 1:
                self._DatabaseName = athena_databases.pop().get('Name')
            elif len(athena_databases) > 1:
                # Remove empty databases from the list
                for d in athena_databases:
                    tables = self.list_table_metadata(
                        DatabaseName=d.get('Name'),
                        max_items=1000, # This is an impiric limit. User can have up to 200k tables in one DB we need to draw a line somewhere
                    )
                    if not len(tables):
                        athena_databases.remove(d)
                # Select default database if present
                default_database = [d for d in athena_databases if d['Name'] == self.defaults.get('DatabaseName')]
                if len(default_database):
                    self._DatabaseName = default_database.pop().get('Name')
                else:
                    # Ask user
                    self._DatabaseName = get_parameter(
                        param_name='athena-database',
                        message="Select AWS Athena database to use",
                        choices=[d['Name'] for d in athena_databases],
                    )
            logger.info(f'Using Athena database: {self._DatabaseName}')
        return self._DatabaseName

    @DatabaseName.setter
    def DatabaseName(self, database):
        self._DatabaseName = database

    @property
    def WorkGroup(self) -> str:
        """ Select AWS Athena workgroup """
        if not self._WorkGroup:
            logger.info('Selecting Athena workgroup...')
            workgroups = self.list_work_groups()
            logger.info(f'Found {len(workgroups)} workgroups: {", ".join([wg.get("Name") for wg in workgroups])}')
            if len(workgroups) == 1:
                self.WorkGroup = workgroups.pop().get('Name')
            elif len(workgroups) > 1:
                # Select default workgroup if present
                default_workgroup = next(iter([wg.get('Name') for wg in workgroups if wg['Name'] == self.defaults.get('WorkGroup')]), None)
                if default_workgroup: logger.info(f'Found "{default_workgroup}" as a default workgroup')
                # Ask user
                self.WorkGroup = get_parameter(
                    param_name='athena-workgroup',
                    message="Select AWS Athena workgroup to use",
                    choices=[d['Name'] for d in workgroups],
                    default=default_workgroup
                )
            logger.info(f'Selected workgroup: "{self._WorkGroup}"')
        return self._WorkGroup

    @WorkGroup.setter
    def WorkGroup(self, name: str):
        try:
            _workgroup = self.client.get_work_group(WorkGroup=name).get('WorkGroup')
        except self.client.exceptions.InvalidRequestException as e:
            raise CidCritical(e)
        if _workgroup.get('State') == 'DISABLED':
            raise CidCritical(f'Workgroup "{name}" is disabled.')
        if not _workgroup.get('Configuration', {}).get('ResultConfiguration', {}).get('OutputLocation'):
            raise CidCritical(f'Workgroup "{name}" must have an output location set.')
        self._WorkGroup = name
        logger.info(f'Selected Athena WorkGroup: "{self._WorkGroup}"')

    def list_data_catalogs(self) -> list:
        return self.client.list_data_catalogs().get('DataCatalogsSummary')
    
    def list_databases(self) -> list:
        return self.client.list_databases(CatalogName=self.CatalogName).get('DatabaseList')
    
    def get_database(self, DatabaseName: str=None) -> bool:
        """ Check if AWS Datacalog and Athena database exist """
        if not DatabaseName:
            DatabaseName=self.DatabaseName
        try:
            self.client.get_database(CatalogName=self.CatalogName, DatabaseName=DatabaseName).get('Database')
            return True
        except Exception as exc:
            if 'AccessDeniedException' in str(exc):
                raise
            else:
                logger.debug(e, exc_info=True)
                return False

    def list_table_metadata(self, DatabaseName: str=None, max_items: int=None) -> dict:
        params = {
            'CatalogName': self.CatalogName,
            'DatabaseName': DatabaseName or self.DatabaseName,
            'PaginationConfig':{
                'MaxItems': max_items,
            },
        }
        table_metadata = list()
        try:
            paginator = self.client.get_paginator('list_table_metadata')
            response_iterator = paginator.paginate(**params)
            for page in response_iterator:
                table_metadata.extend(page.get('TableMetadataList'))
            logger.debug(f'Table metadata: {table_metadata}')
            logger.info(f'Found {len(table_metadata)} tables in {DatabaseName if DatabaseName else self.DatabaseName}')
        except Exception as e:
            logger.error(f'Failed to list tables in {DatabaseName if DatabaseName else self.DatabaseName}')
            logger.error(e)
            
        return table_metadata

    def list_work_groups(self) -> list:
        """ List AWS Athena workgroups """
        result = self.client.list_work_groups()
        logger.debug(f'Workgroups: {result.get("WorkGroups")}')
        return result.get('WorkGroups')

    def get_table_metadata(self, TableName: str) -> dict:
        table_metadata = self._metadata.get(TableName)
        params = {
            'CatalogName': self.CatalogName,
            'DatabaseName': self.DatabaseName,
            'TableName': TableName
        }
        if not table_metadata:
            table_metadata = self.client.get_table_metadata(**params).get('TableMetadata')
            self._metadata.update({TableName: table_metadata})

        return table_metadata


    def execute_query(self, sql_query, sleep_duration=1, database: str=None, catalog: str=None, fail: bool=True) -> str:
        """ Executes an AWS Athena Query """

        # Set execution context
        execution_context = {
            'Database': database or self.DatabaseName,
            'Catalog': catalog or self.CatalogName,
        }

        try:
            # Start Athena query
            response = self.client.start_query_execution(
                QueryString=sql_query, 
                QueryExecutionContext=execution_context, 
                WorkGroup=self.WorkGroup
            )

            # Get Query ID
            query_id = response.get('QueryExecutionId')

            # Get Query Status
            query_status = self.client.get_query_execution(QueryExecutionId=query_id)
        except self.client.exceptions.InvalidRequestException as e:
            logger.debug(f'Full query: {sql_query}')
            raise CidCritical(f'InvalidRequestException: {e}')
        except Exception as e:
            logger.debug(f'Full query: {sql_query}')
            raise CidCritical(f'Athena query failed: {e}')


        current_status = query_status['QueryExecution']['Status']['State']

        # Poll for the current status of query as long as its not finished
        while current_status in ['SUBMITTED', 'RUNNING', 'QUEUED']:
            response = self.client.get_query_execution(QueryExecutionId=query_id)
            current_status = response['QueryExecution']['Status']['State']

            # Sleep before polling again
            time.sleep(sleep_duration)

        # Return result, either positive or negative
        if (current_status == "SUCCEEDED"):
            return query_id
        elif not fail:
            return False
        else:
            failure_reason = response['QueryExecution']['Status']['StateChangeReason']
            logger.error(f'Athena query failed: {failure_reason}')
            logger.info(f'Full query: {sql_query}')
            raise CidCritical(f'Athena query failed: {failure_reason}')

    def get_query_results(self, query_id):
        return self.client.get_query_results(QueryExecutionId=query_id)
    
    def get_query_execution(self, query_id):
        return self.client.get_query_execution(QueryExecutionId=query_id)

    def parse_response_as_list(self, response, include_header=False):
        data = list()

        # Get results rows, either with or without the header row
        rows = response['ResultSet']['Rows'] if include_header else response['ResultSet']['Rows'][1:]

        for row in rows:
            for r in row['Data']:
                data.append(r['VarCharValue'] if 'VarCharValue' in r else '')

        return data

    def query_results_to_csv(self, query_id, return_header=False):
        # Get query results
        response = self.client.get_query_results(QueryExecutionId=query_id)

        # Get results rows, either with or without the header row
        rows = response['ResultSet']['Rows'] if return_header else response['ResultSet']['Rows'][1:]

        if rows:
            # Write rows to StringIO in CSV format
            buf = StringIO()
            csv_writer = csv.writer(buf, delimiter=',')

            for row in rows:
                csv_writer.writerow([x['VarCharValue'] if 'VarCharValue' in x else None for x in row['Data']])

            # Strip whitespaces from CSVified string and return it
            return buf.getvalue().rstrip('\n')
        else:
            return None

    def show_columns(self, table_name):
        sql_query = f'SHOW COLUMNS in {table_name}'
        query_id = self.execute_query(sql_query=sql_query)

        describe = self.query_results_to_csv(query_id).split('\n')

        # Athena is weird.. Remove whitespaces.
        result = [elem.rstrip() for elem in describe]

        return result

    def parse_selected_tables(self, month_list):
        d = {}

        for month in month_list:
            split = month.split('_')

        payer = split[1]
        year = split[2][:4]
        month = split[2][4:]

        if payer in d:
            d[payer].append((year, month))
        else:
            d[payer] = list()
            d[payer].append((year, month))
        
        return d

    # AHQ functions
    def execute_ahq(self, query_id, **kwargs) -> list:
        """ Execute Athena Query by name """
        # Load query
        query = self.get_ahq(query_id, **kwargs)
        # Execute query
        execution_id = self.execute_query(query)
        results = self.get_query_results(execution_id)
        # Return results as list
        return self.parse_response_as_list(results)


    def get_ahq(self, query_id, **kwargs) -> str:
        """ Returns a fully compiled AHQ """
        # Query path
        query_file = self.get_ahqs().get(query_id).get('File')

        template = Template(resource_string(__name__, f'../queries/{query_file}').decode('utf-8'))

        # Fill in TPLs
        columns_tpl = dict()
        columns_tpl.update(**kwargs)
        compiled_query = template.safe_substitute(columns_tpl)

        return compiled_query


    def get_ahqs(self) -> dict:
        """ Return a list of all availiable AHQs """
        
        if not self.ahq_queries:            
            # Load queries
            queries_files = resource_string(__name__, '../queries/ahq-queries.json')
            self.ahq_queries = json.loads(queries_files).get('query_templates')

        return self.ahq_queries


    def discover_views(self, views: dict={}) -> None:
        for view_name in views:
            try:
                self.get_table_metadata(TableName=view_name)
            except self.client.exceptions.MetadataException:
                pass


    def wait_for_view(self, view_name: str, poll_interval=1, timeout=60) -> None:
        deadline = time.time() + timeout
        while time.time() <= deadline:
            self.discover_views([view_name])
            if view_name in self._metadata.keys():
                logger.info(f'view {view_name} exists')
                return True
            else:
                time.sleep(poll_interval)
        else:
            logger.info(f'View {view_name} does not exist, or not discoverable')
            return False


    def delete_table(self, name: str, catalog: str=None, database: str=None):
        if get_parameter(
                param_name=f'confirm-{name}',
                message=f'Delete Athena table {name}?',
                choices=['yes', 'no'],
                default='no') != 'yes':
            return False

        try:
            res = self.execute_query(
                f'DROP TABLE IF EXISTS {name};',
                catalog=catalog,
                database=database,
                fail=False
            )
        except Exception as exc:
            logger.debug(exc, exc_info=True)
            logger.info(f'Table {name} cannot be deleted: {exc}')
            return False
        else:
            if name in self._metadata: del self._metadata[name]
            logger.info(f'Table {name} deleted')
        return True

    def delete_view(self, name: str, catalog: str=None, database: str=None):
        if get_parameter(
                param_name=f'confirm-{name}',
                message=f'Delete Athena view {name}?',
                choices=['yes', 'no'],
                default='no') != 'yes':
            return False

        try:
            res = self.execute_query(
                f'DROP VIEW IF EXISTS {name};',
                catalog=catalog,
                database=database,
                fail=False
            )
        except Exception as exc:
            logger.debug(exc, exc_info=True)
            logger.info(f'View {name} cannot be deleted: {exc}')
            return False
        else:
            if name in self._metadata: del self._metadata[name]
            logger.info(f'View {name} deleted')
        return True
