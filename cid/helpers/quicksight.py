import time
from typing import Dict, Union
import click
import json
from deepmerge import always_merger
import questionary
from pathlib import Path
import os

import logging

logger = logging.getLogger(__name__)

class Dashboard():
    def __init__(self, dashboard: dict) -> None:
        self.dashboard: dict = dashboard
        # Initialize properties
        self.datasets = dict()
        self._status = str()
        self.status_detail = str()
        # Source template in origin account
        self.sourceTemplate = dict()
        # Dashboard definition
        self.definition = dict()
        # Locally saved deployment
        self.localConfig = dict()

    @property
    def id(self) -> str:
        return self.get_property('DashboardId')

    @property
    def name(self) -> str:
        return self.get_property('Name')
    
    @property
    def arn(self) -> str:
        return self.get_property('Arn')

    @property
    def account_id(self) -> str:
        return self.get_property('Arn').split(':')[4]

    @property
    def version(self) -> dict:
        return self.get_property('Version')

    @property
    def latest(self) -> bool:
        return self.latest_version == self.deployed_version

    @property
    def latest_version(self) -> int:
        return int(self.sourceTemplate.get('Version', dict()).get('VersionNumber', -1))
    
    @property
    def deployed_arn(self) -> str:
        return self.version.get('SourceEntityArn')
    
    @property
    def deployed_version(self) -> int:
        try:
            return int(self.deployed_arn.split('/')[-1])
        except:
            return 0
 
    @property
    def health(self) -> bool:
        return self.status not in ['broken']

    @property
    def status(self) -> str:
        if not self._status:
            # Not dicovered yet
            if not self.definition:
                self._status = 'undiscovered'
            # Missing dataset
            elif not self.datasets or (len(self.datasets) < len(self.definition.get('dependsOn').get('datasets'))):
                self.status_detail = 'missing dataset(s)'
                self._status = 'broken'
                logger.info(f"Found datasets: {self.datasets}")
                logger.info(f"Required datasets: {self.definition.get('dependsOn').get('datasets')}")
            # Deployment failed
            elif self.version.get('Status') not in ['CREATION_SUCCESSFUL']:
                self._status = 'broken'
                self.status_detail = f"{self.version.get('Status')}: {self.version.get('Errors')}"
            # Source Template has changed
            elif self.deployed_arn and self.sourceTemplate.get('Arn') and not self.deployed_arn.startswith(self.sourceTemplate.get('Arn')):
                self._status = 'legacy'
            else:
                if self.latest_version > self.deployed_version:
                    self._status = f'update available {self.deployed_version}->{self.latest_version}'
                elif self.latest:
                    self._status = 'up to date'
        return self._status

    @property
    def templateId(self) -> str:
        return str(self.version.get('SourceEntityArn').split('/')[1])

    def get_property(self, property: str) -> str:
        return self.dashboard.get(property)
    
    def find_local_config(self) -> Union[dict, None]:

        if self.localConfig:
            return self.localConfig
        # Set base paths
        abs_path = Path().absolute()

        # Load TPL file
        file_path = None
        files_to_find = [
            f'work/{self.account_id}/{self.id.lower()}-update-dashboard.json',
            f'work/{self.account_id}/{self.id.lower()}-create-dashboard.json',
            f'work/{self.account_id}/{self.id.lower()}-update-dashboard-{self.account_id}.json',
            f'work/{self.account_id}/{self.id.lower()}-create-dashboard-{self.account_id}.json',
        ]
        files_to_find += [f'work/{self.account_id}/{f.lower()}' for f in self.definition.get('localConfigs', list())]
        for file in files_to_find:
            logger.info(f'Checking local config file {file}')
            if os.path.isfile(os.path.join(abs_path, file)):
                file_path = os.path.join(abs_path, file)
                logger.info(f'Found local config file {file}, using it')
                break
            
        if file_path:
            try:
                with open(file_path) as f:
                    self.localConfig = json.loads(f.read())
                    if self.localConfig:
                        for dataset in self.localConfig.get('SourceEntity').get('SourceTemplate').get('DataSetReferences'):
                            if not self.datasets.get(dataset.get('DataSetPlaceholder')):    
                                logger.info(f"Using dataset {dataset.get('DataSetPlaceholder')} ({dataset.get('DataSetId')})")
                                self.datasets.update({dataset.get('DataSetPlaceholder'): dataset.get('DataSetArn')})
            except:
                logger.info(f'Failed to load local config file {file_path}')

    def display_status(self):
        print('\nDashboard status:')
        print(f"  Name (id): {self.name} ({self.id})")
        print(f"  Status: {self.status}")
        print(f"  Health: {'healthy' if self.health else 'unhealthy'}")
        if self.status_detail:
            print(f"  Status detail: {self.status_detail}")
        if self.latest:
            print(f"  Version: {self.deployed_version}")
        else:
            print(f"  Version (deployed, latest): {self.deployed_version}, {self.latest_version}")
        if self.localConfig:
            print(f"  Local config: {self.localConfig.get('SourceEntity').get('SourceTemplate').get('Name')}")
        if self.datasets:
            print(f"  Datasets: {', '.join(sorted(self.datasets.keys()))}")
        print('\n')
        if click.confirm('Display dashboard raw data?'):
            print(json.dumps(self.dashboard, indent=4, sort_keys=True, default=str))
    
    def display_url(self, url_template: str, launch: bool = False, **kwargs):
        url = url_template.format(dashboard_id=self.id, **kwargs)
        print(f"#######\n####### {self.name} is available at: " + url + "\n#######")
        _supported_env = os.environ.get('AWS_EXECUTION_ENV') not in ['CloudShell', 'AWS_Lambda']
        if _supported_env and launch and click.confirm('Do you wish to open it in your browser?'):
                click.launch(url)

class QuickSight():
    # Define defaults
    cidAccountId = '223485597511'
    _dashboards: Dict[str, Dashboard] = {}
    _datasets = dict()
    _datasources: dict() = {}
    _user: dict = None

    def __init__(self, session, awsIdentity, resources=None):        
        self.region = session.region_name
        self.awsIdentity = awsIdentity
        self._resources = resources

        # QuickSight client
        logger.info(f'Creating QuickSight client')
        self.client = session.client('quicksight')
        self.use1Client = session.client('quicksight', region_name='us-east-1')

    @property
    def account_id(self) -> str:
        return self.awsIdentity.get('Account')

    @property
    def user(self) -> dict:
        if not self._user:
            self._user =  self.describe_user('/'.join(self.awsIdentity.get('Arn').split('/')[-2:]))
            if not self._user:
                # If no user match, ask
                userList = self.use1Client.list_users(AwsAccountId=self.account_id, Namespace='default').get('UserList')
                selection = list()
                for user in userList:
                    selection.append(
                        questionary.Choice(
                            title=f"{user.get('UserName')} ({user.get('Email')}, {user.get('Role')})",
                            value=user
                        )
                    )
                try:
                    self._user =  questionary.select("Please select QuickSight to use", choices=selection).ask()
                except:
                    return None
            logger.info(f"Using QuickSight user {self._user.get('UserName')}")
        return self._user

    @property
    def supported_dashboards(self) -> list:
        return self._resources.get('dashboards')

    @property
    def dashboards(self) -> Dict[str, Dashboard]:
        """Returns a list of deployed dashboards"""
        if not self._dashboards:
            self.discover_dashboards()
        return self._dashboards

    @property
    def athena_datasources(self) -> dict:
        """Returns a list of existing athena datasources"""
        return {k: v for (k, v) in self.datasources.items() if v.get('Type') == 'ATHENA'}

    @property
    def datasources(self) -> dict:
        """Returns a list of existing datasources"""
        if not self._datasources:
            logger.info(f"Discovering datasources for account {self.account_id}")
            self.discover_data_sources()

        return self._datasources

    def discover_dashboard(self, dashboardId: str):
        """Discover single dashboard"""
        
        dashboard = self.describe_dashboard(DashboardId=dashboardId)
        # Look for dashboard definition by DashboardId
        _definition = next((v for v in self.supported_dashboards.values() if v['dashboardId'] == dashboard.id), None)
        if not _definition:
            # Look for dashboard definition by templateId
            _definition = next((v for v in self.supported_dashboards.values() if v['templateId'] == dashboard.templateId), None)
        if not _definition:
            logger.info(f'Unsupported dashboard "{dashboard.name}" ({dashboard.deployed_arn})')
        else:
            logger.info(f'Supported dashboard "{dashboard.name}" ({dashboard.deployed_arn})')
            dashboard.definition = _definition
            logger.info(f'Found definition for "{dashboard.name}" ({dashboard.deployed_arn})')
            for dataset in dashboard.version.get('DataSetArns'):
                dataset_id = dataset.split('/')[-1]
                try:
                    _dataset = self.describe_dataset(id=dataset_id)
                    if not _dataset:
                        dashboard.datasets.update({dataset_id: 'missing'})
                        logger.info(f'Dataset "{dataset_id}" is missing')
                    else:
                        logger.info(f"Using dataset \"{_dataset.get('Name')}\" ({_dataset.get('DataSetId')} for {dashboard.name})")
                        dashboard.datasets.update({_dataset.get('Name'): _dataset.get('Arn')})
                except self.client.exceptions.AccessDeniedException:
                    logger.info(f'Looking local config for {dashboardId}')
                    dashboard.find_local_config()
                except self.client.exceptions.InvalidParameterValueException:
                    logger.info(f'Invalid dataset {dataset_id}')
            templateAccountId = _definition.get('sourceAccountId')
            templateId = _definition.get('templateId')
            try:
                template = self.describe_template(templateId, account_id=templateAccountId)
                dashboard.sourceTemplate = template
            except:
                logger.info(f'Unable to describe template {templateId} in {templateAccountId}')
            self._dashboards.update({dashboardId: dashboard})
            logger.info(f"{dashboard.name} has {len(dashboard.datasets)} datasets")
            logger.info(f'"{dashboard.name}" ({dashboardId}) discover complete')

    def create_data_source(self) -> bool:
        """Create a new data source"""
        logger.info('Creating Athena data source')
        params = {
            "AwsAccountId": self.account_id,
            "DataSourceId": "95aa6f18-abb4-436f-855f-182b199a961f",
            "Name": "Athena",
            "Type": "ATHENA",
            "DataSourceParameters": {
                "AthenaParameters": {
                    "WorkGroup": "primary"
                }
            },
            "Permissions": [
                {
                    "Principal": self.user.get('Arn'),
                    "Actions": [
                        "quicksight:UpdateDataSourcePermissions",
                        "quicksight:DescribeDataSource",
                        "quicksight:DescribeDataSourcePermissions",
                        "quicksight:PassDataSource",
                        "quicksight:UpdateDataSource",
                        "quicksight:DeleteDataSource"
                    ]
                }
            ]
        }
        try:
            logger.info(f'Creating data source {params}')
            create_status = self.client.create_data_source(**params)
            logger.debug(f'Data source creation result {create_status}')
            current_status = create_status['CreationStatus']
            logger.info(f'Data source creation status {current_status}')
            # Poll for the current status of query as long as its not finished
            while current_status in ['CREATION_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
                response = self.describe_data_source(create_status['DataSourceId'])
                current_status = response.get('Status')

            if (current_status != "CREATION_SUCCESSFUL"):
                failure_reason = response.get('Errors')
                logger.info(f'Data source creation failed with reason {failure_reason}')
                return False
            return True
        except self.client.exceptions.ResourceExistsException:
            logger.error('Data source already exists')
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied creating data source')
        return False

    def discover_data_sources(self) -> None:
        """ Discover existing datasources"""
        try:
            for v in self.list_data_sources():
                self.describe_data_source(v.get('DataSourceId'))
        except:
            for _,v in self.datasets.items():
                for _,map in v.get('PhysicalTableMap').items():
                    self.describe_data_source(map.get('RelationalTable').get('DataSourceArn').split('/')[-1])

    def discover_dashboards(self, display: bool=False) -> None:
        """ Discover deployed dashboards """
        logger.info('Discovering deployed dashboards')
        deployed_dashboards=self.list_dashboards()
        logger.info(f'Found {len(deployed_dashboards)} deployed dashboards')
        logger.debug(deployed_dashboards)
        with click.progressbar(
            deployed_dashboards,
            label='Discovering deployed dashboards...',
            item_show_func=lambda a: a
        ) as bar:
            for index, dashboard in enumerate(deployed_dashboards, start=1):
                # Discover found dashboards
                dashboardName = dashboard.get('Name')
                dashboardId = dashboard.get('DashboardId')
                # Update progress bar
                bar.update(index, f'"{dashboardName}" ({dashboardId})')
                logger.info(f'Discovering dashboard "{dashboardName}" ({dashboardId})')
                self.discover_dashboard(dashboardId)
                # Update progress bar
                bar.update(index, 'Complete')
        # print('Discovered dashboards:')
        if not display:
            return
        for dashboard in self._dashboards.values():
            if dashboard.health:
                health = 'healthy' 
            else:
                health = 'unhealthy'
            print(f'\t{dashboard.name} ({dashboard.id}, {health}, {dashboard.status})')


    def list_dashboards(self) -> list:
        parameters = {
            'AwsAccountId': self.account_id
        }
        try:
            result = self.client.list_dashboards(**parameters)
            if result.get('Status') != 200:
                print(f'Error, {result}')
                exit()
            else:
                logger.debug(result)
                return result.get('DashboardSummaryList')
        except:
            return list()

    def list_data_sources(self) -> list:
        parameters = {
            'AwsAccountId': self.account_id
        }
        try:
            result = self.client.list_data_sources(**parameters)
            if result.get('Status') != 200:
                print(f'Error, {result}')
                exit()
            else:
                return result.get('DataSources')
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied listing data sources')
            return list()
        except:
            return list()

    def select_dashboard(self, force=False) -> str:
        """ Select from a list of discovered dashboards """
        selection = list()
        dashboard_id = None
        for dashboard in self.dashboards.values():
            if dashboard.health:
                health = 'healthy' 
            else:
                health = 'unhealthy'
            selection.append(
                questionary.Choice(
                    title=f'{dashboard.name} ({dashboard.arn}, {health}, {dashboard.status})',
                    value=dashboard.id,
                    # Disable if broken or no update available and not forced
                    disabled=((dashboard.latest or not dashboard.health) and not force)
                )
            )
        try:
            dashboard_id = questionary.select(
                "Please select installation(s) from the list",
                choices=selection
            ).ask()
        except:
            print('\nNo updates available or dashboard(s) is/are broken, use --force to allow selection\n')
        finally:
            return dashboard_id
        
    def list_data_sets(self):
        parameters = {
            'AwsAccountId': self.account_id
        }
        try:
            result = self.client.list_data_sets(**parameters)
            if result.get('Status') != 200:
                print(f'Error, {result}')
                exit()
            else:
                return result.get('DataSetSummaries')
        except self.client.exceptions.AccessDeniedException:
            raise
        except:
            return None

    def describe_dashboard(self, poll: bool=False, **kwargs) -> Union[None, Dashboard]:
        """ Describes an AWS QuickSight dashboard
        Keyword arguments:
        DashboardId

        """
        poll_interval = kwargs.get('poll_interval', 1)
        try:
            dashboard: Dashboard = None
            current_status = None
            # Poll for the current status of query as long as its not finished
            while current_status in [None, 'CREATION_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
                if current_status:
                    logger.info(f'Dashboard {dashboard.name} status is {current_status}, waiting for {poll_interval} seconds')
                    # Sleep before polling again
                    time.sleep(poll_interval)
                elif poll:
                    logger.info(f'Polling for dashboard {kwargs.get("DashboardId")}')
                response = self.client.describe_dashboard(AwsAccountId=self.account_id, **kwargs).get('Dashboard')
                logger.debug(response)
                dashboard = Dashboard(response)
                current_status = dashboard.version.get('Status')
                if not poll:
                    break
            logger.info(f'Dashboard {dashboard.name} status is {current_status}')
            return dashboard
        except self.client.exceptions.ResourceNotFoundException:
            return None
        except self.client.exceptions.UnsupportedUserEditionException:
            print('Error: AWS QuickSight Enterprise Edition is required')
            exit(1)
        except Exception as e:
            print(f'Error: {e}')
            raise

    def delete_dashboard(self, dashboard_id):
        """ Deletes an AWS QuickSight dashboard """
        paramaters = {
            'AwsAccountId': self.account_id,
            'DashboardId': dashboard_id
        }
        return self.client.delete_dashboard(**paramaters)

    def describe_dataset(self, id) -> dict:
        """ Describes an AWS QuickSight dataset """
        if not self._datasets.get(id):
            logger.info(f'Describing dataset {id}')
            try:
                _dataset = self.client.describe_data_set(AwsAccountId=self.account_id,DataSetId=id).get('DataSet')
                logger.info(f'Saving dataset details "{_dataset.get("Name")}" ({_dataset.get("DataSetId")})')
                self._datasets.update({_dataset.get('DataSetId'): _dataset})
            except self.client.exceptions.ResourceNotFoundException:
                logger.info(f'DataSetId {id} do not exist')
            except self.client.exceptions.AccessDeniedException:
                logger.debug(f'No quicksight:DescribeDataSet permission or missing DataSetId {id}')
        return self._datasets.get(id, dict())

    def describe_data_source(self, id):
        """ Describes an AWS QuickSight data source """
        try:
            result = self.client.describe_data_source(AwsAccountId=self.account_id,DataSourceId=id)
            logger.debug(result)
            _described_data_source = self._datasources.get(result.get('DataSource').get('Arn'))
            if not _described_data_source or _described_data_source.get('Status') in ['CREATION_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
                self._datasources.update({result.get('DataSource').get('Arn'): result.get('DataSource')})
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f'DataSource {id} do not exist')
            raise
        except self.client.exceptions.AccessDeniedException:
            logger.info(f'No quicksight:DescribeDataSource permission or missing DataSetId {id}')
            raise
        return result.get('DataSource')


    def describe_template(self, template_id: str, account_id: str=None ):
        """ Describes an AWS QuickSight template """
        if not account_id:
            account_id=self.cidAccountId
        try:
            result = self.use1Client.describe_template(AwsAccountId=account_id,TemplateId=template_id)
            logger.debug(result)
        except:
            print(f'Error: Template {template_id} is not available in account {account_id}')
            exit(1)
        return result.get('Template')

    def describe_user(self, username: str) -> dict:
        """ Describes an AWS QuickSight template """
        parameters = {
            'AwsAccountId': self.account_id,
            'UserName': username,
            'Namespace': 'default'
        }
        try:
            return self.client.describe_user(**parameters).get('User')
        except self.client.exceptions.ResourceNotFoundException:
            return None
        except self.client.exceptions.AccessDeniedException:
            userList = self.use1Client.list_users(AwsAccountId=self.account_id, Namespace='default').get('UserList')
            for user in userList:
                if username.endswith(user.get('UserName')):
                    return user
            return None

    def create_dataset(self, dataset: dict) -> dict:
        """ Creates an AWS QuickSight dataset """
        dataset.update({'AwsAccountId': self.account_id})
        try:
            response = self.client.create_data_set(**dataset)
            logger.info(f'Created dataset {dataset.get("Name")} ({response.get("DataSetId")})')
            self.describe_dataset(response.get('DataSetId'))
        except self.client.exceptions.ResourceExistsException:
            logger.info(f'Dataset {dataset.get("Name")} already exists')


    def create_dashboard(self, definition: dict, **kwargs) -> Dashboard:
        """ Creates an AWS QuickSight dashboard """
        DataSetReferences = list()
        for k, v in definition.get('datasets', dict()).items():
            DataSetReferences.append({
                'DataSetPlaceholder': k,
                'DataSetArn': v
            })
        
        create_parameters = {
            'AwsAccountId': self.account_id,
            'DashboardId': definition.get('dashboardId'),
            'Name': definition.get('name'),
            'Permissions': [
                {
                    "Principal": self.user.get('Arn'),
                    "Actions": [
                        "quicksight:DescribeDashboard",
                        "quicksight:ListDashboardVersions",
                        "quicksight:UpdateDashboardPermissions",
                        "quicksight:QueryDashboard",
                        "quicksight:UpdateDashboard",
                        "quicksight:DeleteDashboard",
                        "quicksight:DescribeDashboardPermissions",
                        "quicksight:UpdateDashboardPublishedVersion"
                    ]
                }
            ],
            'SourceEntity': {
                'SourceTemplate': {
                    'Arn': f"{definition.get('sourceTemplate').get('Arn')}/version/{definition.get('sourceTemplate').get('Version').get('VersionNumber')}",
                    'DataSetReferences': DataSetReferences
                }
            }
        }
        
        create_parameters = always_merger.merge(create_parameters, kwargs)
        try:
            create_status = self.client.create_dashboard(**create_parameters)
            logger.debug(create_status)
        except self.client.exceptions.ResourceExistsException:
            raise
        created_version = int(create_status['VersionArn'].split('/')[-1])
        current_status = create_status['CreationStatus']

        # Poll for the current status of query as long as its not finished
        describe_parameters = {
            'DashboardId': definition.get('dashboardId'),
            'VersionNumber': created_version
        }
        dashboard = self.describe_dashboard(poll=True, **describe_parameters)
        if not dashboard.health:
            failure_reason = dashboard.version.get('Errors')
            raise Exception(failure_reason)

        return dashboard


    def update_dashboard(self, dashboard: Dashboard, **kwargs):
        """ Updates an AWS QuickSight dashboard """
        DataSetReferences = list()
        for k, v in dashboard.datasets.items():
            DataSetReferences.append({
                'DataSetPlaceholder': k,
                'DataSetArn': v
            })

        update_parameters = {
            'AwsAccountId': self.account_id,
            'DashboardId': dashboard.id,
            'Name': dashboard.name,
            'SourceEntity': {
                'SourceTemplate': {
                    'Arn': f"{dashboard.sourceTemplate.get('Arn')}/version/{dashboard.latest_version}",
                    'DataSetReferences': DataSetReferences
                }
            }
        }

        update_parameters = always_merger.merge(update_parameters, kwargs)
        logger.debug(f"Update parameters: {update_parameters}")
        update_status = self.client.update_dashboard(**update_parameters)
        logger.debug(update_status)
        updated_version = int(update_status['VersionArn'].split('/')[-1])

        dashboard = self.describe_dashboard(poll=True, DashboardId=dashboard.id, VersionNumber=updated_version)
        if not dashboard.health:
            failure_reason = dashboard.version.get('Errors')
            raise Exception(failure_reason)

        update_params = {
            'AwsAccountId': self.account_id,
            'DashboardId': dashboard.id,
            'VersionNumber': updated_version
        }
        result = self.client.update_dashboard_published_version(**update_params)
        if result['Status'] != 200:
            raise Exception(result)

        return result
