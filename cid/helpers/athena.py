import re
import csv
import json
import time
import uuid
import logging
from string import Template
from io import StringIO
from pkg_resources import resource_string

from cid.base import CidBase
from cid.helpers.s3 import S3
from cid.utils import get_parameter, get_parameters, cid_print
from cid.helpers.diff import diff
from cid.exceptions import CidCritical, CidError

logger = logging.getLogger(__name__)

class Athena(CidBase):
    # Define defaults
    defaults = {
        'CatalogName': 'AwsDataCatalog',
        'DatabaseName': 'customer_cur_data',
        'WorkGroup': 'CID'
    }
    _CatalogName = None
    _DatabaseName = None
    _WorkGroup = None
    _metadata = dict()
    _resources = dict()
    _client = None

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
        if self._DatabaseName: return self._DatabaseName

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
            # Silently choose an existing database
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
            default_databases = [d for d in athena_databases if d['Name'] == self.defaults.get('DatabaseName')]
            if len(default_databases):
                # Silently choose an existing default database
                self._DatabaseName = default_databases.pop().get('Name')
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
            if get_parameters().get('athena-workgroup'):
                self.WorkGroup = self._ensure_workgroup(name=get_parameters().get('athena-workgroup'))
                return self._WorkGroup
            logger.info('Selecting Athena workgroup...')
            workgroups = self.list_work_groups()
            logger.info(f'Found {len(workgroups)} workgroups: {", ".join([wg.get("Name") for wg in workgroups])}')
            if len(workgroups) == 0:
                self.WorkGroup = self._ensure_workgroup(name=self.defaults.get('WorkGroup'))
            elif len(workgroups) == 1:
                # Silently choose the only workgroup that is available
                self.WorkGroup = self._ensure_workgroup(name=workgroups.pop().get('Name'))
            else:
                # Select default workgroup if present
                if self.defaults.get('WorkGroup') not in {wgr['Name'] for wgr in workgroups}:
                    workgroups.append({'Name': f"{self.defaults.get('WorkGroup')} (create new)"})
                default_workgroup = next(iter([wgr.get('Name') for wgr in workgroups if wgr['Name'] == self.defaults.get('WorkGroup')]), None)
                if default_workgroup: logger.info(f'Found "{default_workgroup}" as a default workgroup')
                # Ask user
                selected_workgroup = get_parameter(
                    param_name='athena-workgroup',
                    message="Select Amazon Athena workgroup to use",
                    choices=[wgr['Name'] for wgr in workgroups],
                    default=default_workgroup
                )
                if ' (create new)' in selected_workgroup:
                    selected_workgroup = selected_workgroup.replace(' (create new)', '')
                self.WorkGroup = self._ensure_workgroup(name=selected_workgroup)
                
            logger.info(f'Selected workgroup: "{self._WorkGroup}"')
        return self._WorkGroup

    @WorkGroup.setter
    def WorkGroup(self, name: str):
        try:
            _workgroup = self.client.get_work_group(WorkGroup=name).get('WorkGroup')
        except self.client.exceptions.InvalidRequestException as e:
            raise CidCritical(e)
        if _workgroup.get('State') == 'DISABLED':
            raise CidCritical(f'Athena Workgroup "{name}" is disabled.')
        if not _workgroup.get('Configuration', {}).get('ResultConfiguration', {}).get('OutputLocation'):
            raise CidCritical(f'Athena Workgroup "{name}" must have an output location s3 bucket configured in the region {self.region}. See https://{self.region}.console.aws.amazon.com/athena/home?#/workgroups .')
        self._WorkGroup = name
        logger.info(f'Selected Athena WorkGroup: "{self._WorkGroup}"')

    def _ensure_workgroup(self, name: str) -> str:
        try:
            s3 = S3(session=self.session)
            bucket_name = f'{self.partition}-athena-query-results-cid-{self.account_id}-{self.region}'
            
            workgroup = self.client.get_work_group(WorkGroup=name)
            # "${AWS::Partition}-athena-query-results-cid-${AWS::AccountId}-${AWS::Region}"
            if not workgroup.get('WorkGroup', {}).get('Configuration', {}).get('ResultConfiguration', {}).get('OutputLocation', None):
                s3 = S3(session=self.session)
                buckets = s3.list_buckets(region_name=self.region)
                if bucket_name not in buckets:
                    buckets.append(f'{bucket_name} (create new)')
                bucket_name = get_parameter(
                    param_name='athena-result-bucket',
                    message=f"Select S3 bucket to use with Amazon Athena Workgroup [{name}]",
                    choices=[bucket for bucket in buckets]
                )
                if ' (create new)' in bucket_name:
                    bucket_name = bucket_name.replace(' (create new)', '')
                s3.ensure_bucket(name=bucket_name)
                response = self.client.update_work_group(
                    WorkGroup=name,
                    Description='string',
                    ConfigurationUpdates={
                        'ResultConfigurationUpdates': {
                            'OutputLocation': f's3://{bucket_name}',
                            'EncryptionConfiguration': {
                                'EncryptionOption': 'SSE_S3',
                            },
                            'AclConfiguration': {
                                'S3AclOption': 'BUCKET_OWNER_FULL_CONTROL'
                            }
                        }
                    }
                )
            return name
        except self.client.exceptions.InvalidRequestException as ex:
            # Workgroup does not exist
            if 'WorkGroup is not found' in ex.response.get('Error', {}).get('Message'):
                s3.ensure_bucket(name=bucket_name)
                response = self.client.create_work_group(
                    Name=name,
                    Configuration={
                        'ResultConfiguration': {
                            'OutputLocation': f's3://{bucket_name}',
                            'EncryptionConfiguration': {
                                'EncryptionOption': 'SSE_S3',
                            },
                            'AclConfiguration': {
                                'S3AclOption': 'BUCKET_OWNER_FULL_CONTROL'
                            }
                        },
                    }
                )
                return name
        except Exception as ex:
            raise CidCritical('Failed to create Athena work group') from ex
                
    def list_data_catalogs(self) -> list:
        return self.client.list_data_catalogs().get('DataCatalogsSummary')
    
    def list_databases(self) -> list:
        return self.client.list_databases(CatalogName=self.CatalogName).get('DatabaseList')
    
    def get_database(self, DatabaseName: str=None) -> bool:
        """ Check if AWS Datacalog and Athena database exist """
        if not DatabaseName:
            DatabaseName = self.DatabaseName
        try:
            self.client.get_database(CatalogName=self.CatalogName, DatabaseName=DatabaseName).get('Database')
            return True
        except Exception as exc:
            if 'AccessDeniedException' in str(exc):
                raise
            else:
                logger.debug(exc, exc_info=True)
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
            if not query_id:
                logger.debug(f'Full query: {sql_query}')
                raise CidCritical(f'Athena cannot start query. Answer is: {response}')
            # Get Query Status for the first time
            query_status = self.client.get_query_execution(QueryExecutionId=query_id)
        except self.client.exceptions.InvalidRequestException as exc:
            logger.debug(f'Full query: {sql_query}')
            raise CidCritical(f'InvalidRequestException: {exc}') from exc
        except Exception as exc:
            logger.debug(f'Full query: {sql_query}')
            raise CidCritical(f'Athena query failed: {exc}') from exc

        current_status = query_status['QueryExecution']['Status']['State']

        # Poll for the current status of query as long as its not finished
        while current_status in ['SUBMITTED', 'RUNNING', 'QUEUED']:
            response = self.client.get_query_execution(QueryExecutionId=query_id)
            current_status = response['QueryExecution']['Status']['State']

            # Sleep before polling again
            time.sleep(sleep_duration)

        if current_status == "SUCCEEDED":
            return query_id
        failure_reason = response.get('QueryExecution', {}).get('Status', {}).get('StateChangeReason',repr(response))
        logger.info(f'Athena query failed: {failure_reason}')
        logger.debug(f'Full query: {sql_query}')
        if fail:
            raise CidCritical(f'Athena query failed: {failure_reason}')
        return False

    def get_query_results(self, query_id):
        """ Get Query Results """
        return self.client.get_query_results(QueryExecutionId=query_id)

    def parse_response_as_table(self, response, include_header=False):
        """ Return a query response as a table. """
        result = []
        starting_row = 0 if include_header else 1
        for row in response['ResultSet']['Rows'][starting_row:]:
            result.append([data.get('VarCharValue', '') for data in row['Data']])
        return result

    def query(self, sql, include_header=False, **kwargs) -> list:
        """ Execute Athena Query and return a result"""
        logger.debug(f'query={sql}')
        execution_id = self.execute_query(sql, **kwargs)
        results = self.get_query_results(execution_id)
        #logger.debug(f'results = {json.dumps(results, indent=2)}')
        prarsed = self.parse_response_as_table(results, include_header)
        logger.debug(f'prarsed res = {json.dumps(prarsed, indent=2)}')
        return prarsed


    def discover_views(self, views: dict={}) -> None:
        """ Discover views from a given list of view names and cahe them. """
        for view_name in views:
            try:
                self.get_table_metadata(TableName=view_name)
            except self.client.exceptions.MetadataException:
                pass


    def wait_for_view(self, view_name: str, poll_interval=1, timeout=60) -> None:
        """ Wait for a View to be created. """
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

    def get_view_diff(self, name, sql):
        """ returns a diff between existing and new viws. """
        tmp_name = 'cid_tmp_deleteme'
        existing_sql = ''
        try:
            existing_sql = self.query(f'SHOW CREATE VIEW {name}', include_header=True)
            existing_sql = '\n'.join([line[0] for line in existing_sql][1:])
        except Exception as exc:
            print(exc)
            return None
        try:
            # Avoid difference in the first line of diff (replace name of the view with the tmp_name)
            tmp_sql = re.sub(r'(CREATE OR REPLACE VIEW) (.+?) (AS.*)', r'\1 ' + tmp_name +  r' \3', sql)

            if tmp_sql == sql:
                raise CidError(f"Cannot get diff: same sql {repr(sql)}")
            self.query(tmp_sql)
            tmp_sql = self.query(f'SHOW CREATE VIEW {tmp_name}', include_header=True)
            tmp_sql = '\n'.join([line[0] for line in tmp_sql][1:])
        except Exception as exc:
            print(exc)
            return None
        finally:
            try:
                self.query(f'DROP VIEW IF EXISTS {tmp_name};', fail=False)
            except Exception as exc:
                logger.debug(f'Cannot delete temporary view {tmp_name}: {exc}')

        existing_sql = re.sub('"(.+?)"', r'\1', existing_sql) # remove quotes
        tmp_sql = re.sub('"(.+?)"', r'\1', tmp_sql) # remove quotes
        return diff(existing_sql, tmp_sql)


    def process_views(self, views):
        """ returns a dict of discovered views. Going to each view and try to discover recursively all "FROM" dependanices
        """
        all_views = {}
        def _recursively_process_view(view):
            """ process recursively views and add all dependency views to the global dict
            """
            athena_type = None
            if self.query(f"SHOW VIEWS LIKE '{view}'", include_header=True):
                athena_type = 'view'
            elif self.query(f"SHOW TABLES LIKE '{view}'", include_header=True):
                athena_type = 'table'
            else:
                logger.debug(f'{view} not a view and not a table. Skipping.')
                return None
            cid_print(f"    Processing Athena {athena_type}: <BOLD>{view}<END>")

            all_views[view] = {}
            if athena_type == 'view':
                sql = self.query(f'SHOW CREATE VIEW {view}', include_header=True)
                if not sql:
                    return
                sql = '\n'.join([line[0] for line in sql])
                #print("sql", sql)
                all_views[view]["dependsOn"] = {}
                all_views[view]["dependsOn"]['views'] = []
                deps = re.findall(r'FROM\W+?([\w."]+)', sql)
                for dep_view in deps:
                    #FIXME: need to add cross Database Dependancies
                    if dep_view.upper() in ('SELECT', 'VALUES'): # remove "FROM SELECT" and "FROM VALUES"
                        continue
                    dep_view = dep_view.replace('"', '')
                    if len(dep_view.split('.')) == 2:
                        dep_database, dep_view_name = dep_view.split('.')
                        if dep_database != self.DatabaseName:
                            logger.error(f'The view {view} has a dependency on {dep_view}. CID cannot manage multiple Databases. Please move {dep_view_name} to Database {self.DatabaseName}. Skipping dependency.')
                            continue
                    dep_view = dep_view.split('.')[-1]
                    if dep_view not in all_views:
                        _recursively_process_view(dep_view)
                    if dep_view not in all_views[view]["dependsOn"]['views'] and dep_view in all_views:
                        all_views[view]["dependsOn"]['views'].append(dep_view)
                if not all_views[view]["dependsOn"]['views']:
                    del all_views[view]["dependsOn"]

            elif athena_type == 'table':
                sql = self.query(f'SHOW CREATE TABLE {view}', include_header=True)
                sql = '\n'.join([line[0] for line in sql])

            all_views[view]['data'] = sql.rstrip()
            return all_views[view]

        for view in views:
            _recursively_process_view(view)

        return all_views