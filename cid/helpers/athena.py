import time, csv

import questionary
from io import StringIO

from pkg_resources import resource_string
from string import Template
import json

import yaspin

import logging
logger = logging.getLogger(__name__)

class Athena():
    # Define defaults
    defaults = {
        'CatalogName': 'AwsDataCatalog',
        'DatabaseName': 'customer_cur_data'
    }
    _CatalogName = None
    _DatabaseName = None
    ahq_queries = None
    _metadata = dict()
    _resources = dict()
    _client = None
    region: str = None

    def __init__(self, session, resources: dict=None):        
        self.region = session.region_name
        self._resources = resources
        
        # Athena client
        self._client = session.client('athena', region_name=self.region)

    @property
    def client(self):
        return self._client

    @property
    def CatalogName(self) -> str:
        """ Check if AWS Datacalog and Athena database exist """
        if not self._CatalogName:
            # Get AWS Glue DataCatalogs
            glue_data_catalogs = [d for d in self.list_data_catalogs() if d['Type'] == 'GLUE']
            if not len(glue_data_catalogs):
                self._status = 'AWS DataCatog of type GLUE not found'
            if len(glue_data_catalogs) == 1:
                self._CatalogName = glue_data_catalogs.pop().get('CatalogName')
            elif len(glue_data_catalogs) > 2:
                # Select default catalog if present
                default_catalog = [d for d in glue_data_catalogs if d['CatalogName'] == self.defaults.get('_CatalogName')]
                if not len(default_catalog):
                    # Ask user
                    self._CatalogName = questionary.select(
                        "Select AWS DataCatalog to use",
                        choices=glue_data_catalogs
                    ).ask()
            logger.info(f'Using datacatalog: {self._CatalogName}')
        return self._CatalogName

    @property
    def DatabaseName(self) -> str:
        """ Check if Athena database exist """

        if not self._DatabaseName:
            # Get AWS Athena databases
            athena_databases = self.list_databases()
            if not len(athena_databases):
                self._status = 'AWS Athena databases not found'
                print(self._status)
                exit(1)
            if len(athena_databases) == 1:
                self._DatabaseName = athena_databases.pop().get('Name')
            elif len(athena_databases) > 1:
                # Remove empty databases from the list
                for d in athena_databases:
                    tables = self.list_table_metadata(DatabaseName=d.get('Name'))
                    if not len(tables):
                        athena_databases.remove(d)
                # Select default database if present
                default_database = [d for d in athena_databases if d['Name'] == self.defaults.get('DatabaseName')]
                if len(default_database):
                    self._DatabaseName = default_database.pop().get('Name')
                else:
                    # Ask user
                    self._DatabaseName = questionary.select(
                        "Select AWS Athena database to use",
                        choices=[d['Name'] for d in athena_databases]
                    ).ask()
            logger.info(f'Using Athena database: {self._DatabaseName}')
        return self._DatabaseName

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
        except:
            return False

    def list_table_metadata(self, DatabaseName: str=None) -> dict:
        params = {
            'CatalogName': self.CatalogName,
            'DatabaseName': DatabaseName if DatabaseName else self.DatabaseName
        }
        try:
            table_metadata = self.client.list_table_metadata(**params).get('TableMetadataList')
        except:
            table_metadata = list()
            
        return table_metadata

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


    def execute_query(self, sql_query, sleep_duration=1) -> str:
        """ Executes an AWS Athena Query """

        # Set execution context
        execution_context = {'Database': self.DatabaseName}

        try:
            # Start Athena query
            response = self.client.start_query_execution(
                QueryString=sql_query, 
                QueryExecutionContext=execution_context, 
                WorkGroup='primary'
            )

            # Get Query ID
            query_id = response.get('QueryExecutionId')

            # Get Query Status
            query_status = self.client.get_query_execution(QueryExecutionId=query_id)
        except self.client.exceptions.InvalidRequestException as e:
            logger.error(f'InvalidRequestException: {e}')
            exit(1)
        except Exception as e:
            logger.error('Athena query failed: {}'.format(e))
            logger.error('Full query: {}'.format(sql_query))
            exit(1)

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
        else:
            failure_reason = response['QueryExecution']['Status']['StateChangeReason']
            logger.error('Athena query failed: {}'.format(failure_reason))
            logger.error(f'Failure reason: {failure_reason}')
            logger.info('Full query: {}'.format(sql_query))
            exit(1)

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


    def update_views(self):
        """ Update Athena views """
        # TODO: check if needed
        print('Loading views definitions', end='')
        view_list = self.get_views(self.hasReservations, self.hasSavingsPlans)
        print('done')
        print('Updating views')
        
        for view in view_list.get('views'):
            sp = yaspin(text=view.get('label'))
            # Load query
            sql_query = self.get_view(view.get('id')).get('query')
            # Execute query
            try:
                query_id = self.athena.execute_query(sql_query=sql_query)
                # Get results as list
                response = self.athena.get_query_results(query_id)
                # result = athena.parse_response_as_list(response)
                sp.ok("✔")
            except:
                sp.fail("query failed")
        
        return True
