import time
from typing import Union
import click
import json
from deepmerge import always_merger
import questionary
from pathlib import Path
import os

import logging

from questionary.constants import NO
logger = logging.getLogger(__name__)

class Dashboard():
    def __init__(self, dashboard) -> None:
        self.dashboard = dashboard
        self.status = None
        self.health = True
        self.latest = False
        self.status_detail = None
        self.datasets = dict()
        # Source template in origin account
        self.sourceTemplate = None
        # Dashboard definition
        self.template = None
        self.dashboard_id = None
        # Locally saved deployment
        self.localConfig = None

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
    def version(self) -> dict:
        return self.get_property('Version')

    @property
    def latest_version(self) -> int:
        return int(self.sourceTemplate.get('Version').get('VersionNumber'))
    
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
    def templateId(self) -> str:
        return str(self.version.get('SourceEntityArn').split('/')[1])

    def get_property(self, property) -> str:
        return self.dashboard.get(property)
    
    def find_local_config(self, account_id):

        # Set base paths
        abs_path = Path().absolute()

        # Load TPL file
        file_path = None
        files_to_find = [
            f'work/{account_id}/{self.id.lower()}-update-dashboard.json',
            f'work/{account_id}/{self.id.lower()}-create-dashboard.json',
            f'work/{account_id}/{self.id.lower()}-update-dashboard-{account_id}.json',
            f'work/{account_id}/{self.id.lower()}-create-dashboard-{account_id}.json',
        ]
        for localConfig in self.template.get('localConfigs', list()):
            files_to_find.append(f'work/{account_id}/{localConfig.lower()}')
        for file in files_to_find:
            logger.debug(f'Checking local config file {file}')
            if os.path.isfile(os.path.join(abs_path, file)):
                file_path = os.path.join(abs_path, file)
                break
            
        if file_path:
            try:
                with open(file_path) as f:
                    self.localConfig = json.loads(f.read())
                    if self.localConfig:
                        for dataset in self.localConfig.get('SourceEntity').get('SourceTemplate').get('DataSetReferences'):
                            # self.datasets.update({dataset.get('DataSetPlaceholder'): dataset.get('DataSetArn').split(':')[-1].split('/')[-1]})
                            self.datasets.update({dataset.get('DataSetPlaceholder'): dataset.get('DataSetArn')})
            except:
                raise


class QuickSight():
    # Define defaults
    cidAccountId = '223485597511'
    _dashboards = dict()
    _datasets = dict()
    _datasources = dict()
    _user = None

    def __init__(self, session, awsIdentity, resources=None):        
        self.region = session.region_name
        self.awsIdentity = awsIdentity
        self._resources = resources

        # QuickSight client
        self.client = session.client('quicksight', region_name=self.region)
        self.use1Client = session.client('quicksight', region_name='us-east-1')

    @property
    def account_id(self) -> str:
        return self.awsIdentity.get('Account')

    @property
    def user(self):
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
                    self._user =  questionary.select("\nPlease select QuickSight to use", choices=selection).ask()
                except:
                    return None

        return self._user

    @property
    def dashboards(self) -> dict:
        """Returns a list of deployed dashboards"""
        if not self._dashboards:
            self.discover_dashboards(self._resources.get('dashboards'))
        return self._dashboards

    # @property
    # def datasources(self, _type: str='All') -> dict:
    #     """Returns a list of existing datasources"""
    #     if _type not in ['All', 'Athena']:
    #         _type = 'Athena'
    #     if not self._datasources:
    #         self.discover_data_sources()
    #     if _type is not 'All':
    #         return {v.get('DataSourceId'):v for v in self._datasources if v.get('Type') == _type}
    #     else:
    #         return self._datasources

    @property
    def datasources(self) -> dict:
        """Returns a list of existing datasources"""
        if not self._datasources:
            self.discover_data_sources()

        return self._datasources

    def discover_dashboard(self, dashboard_id) -> Dashboard:
        """Discover single dashboard"""

        return self.describe_dashboard(DashboardId=dashboard_id)

    def discover_data_sources(self) -> None:
        """ Discover existing datasources"""
        try:
            for v in self.list_data_sources():
                self.describe_data_source(v.get('DataSourceId'))
        except:
            for _,v in self._datasets.items():
                for _,map in v.get('PhysicalTableMap').items():
                    self.describe_data_source(map.get('RelationalTable').get('DataSourceArn').split('/')[-1])

    def discover_dashboards(self, supported_dashboards, display: bool=False) -> None:
        """ Discover deployed dashboards """
        deployed_dashboards=self.list_dashboards()
        with click.progressbar(
            deployed_dashboards,
            label='Discovering deployed dashboards...',
            item_show_func=lambda a: a
        ) as bar:
            for index, item in enumerate(deployed_dashboards, start=1):
                # Iterate through loaded list of dashboards by dashboardId
                dashboardName = item.get('Name')
                dashboardId = item.get('DashboardId')
                # Update progress bar
                bar.update(index, f'"{dashboardName}" ({dashboardId})')
                dashboard = self.describe_dashboard(DashboardId=dashboardId)
                # Iterate dashboards by DashboardId
                res = next((sub for sub in supported_dashboards.values() if sub['dashboardId'] == dashboard.id), None)
                if not res:
                    # Iterate dashboards by templateId
                    res = next((sub for sub in supported_dashboards.values() if sub['templateId'] == dashboard.templateId), None)
                if not res:
                    logging.info(f'\nNot a supported dashboard "{dashboard.name}" ({dashboard.deployed_arn})\n')
                else:
                    dashboard.status = 'healthy'
                    dashboard.template = res
                    for dataset in dashboard.version.get('DataSetArns'):
                        dataset_id = dataset.split('/')[-1]
                        try:
                            _dataset = self.describe_dataset(id=dataset_id)
                            if not _dataset:
                                dashboard.status = 'broken'
                                dashboard.health = False
                                dashboard.status_detail = 'missing dataset'
                                dashboard.datasets.update({dataset_id: 'missing'})
                            else:
                                logging.info('Found dataset "{name}" ({arn})'.format(name=_dataset.get('Name'), arn=_dataset.get('Arn')))
                                dashboard.datasets.update({_dataset.get('Name'): _dataset.get('Arn')})
                                self._datasets.update({_dataset.get('Name'): _dataset})
                        except self.client.exceptions.AccessDeniedException:
                            dashboard.status = 'broken'
                            dashboard.health = False
                            dashboard.status_detail = 'missing dataset'
                            logger.debug(f'Looking local config for {dashboardId}')
                            dashboard.find_local_config(self.account_id)
                        except self.client.exceptions.InvalidParameterValueException:
                            logger.debug(f'Invalid dataset {dataset_id}')
                            continue
                    # if not dashboard.status.startswith('broken'):
                    templateAccountId = res.get('sourceAccountId')
                    try:
                        template = self.describe_template(dashboard.templateId, account_id=templateAccountId)
                    except:
                        logging.info(f'Unable to describe template {dashboard.templateId} in {templateAccountId}')
                        template = None
                    if not template:
                        continue
                    dashboard.sourceTemplate = template
                    if not dashboard.deployed_arn.startswith(template.get('Arn')):
                        dashboard.status = 'legacy'
                    else:
                        if dashboard.latest_version > dashboard.deployed_version:
                            dashboard.status = f'update available {dashboard.deployed_version}->{dashboard.latest_version}'
                        elif dashboard.latest_version == dashboard.deployed_version:
                            dashboard.latest = True
                            dashboard.status = 'up to date'
                    self._dashboards.update({dashboardId: dashboard})
                    # Update progress bar
                    bar.update(index, '')
                    logging.info(f'\t"{dashboardName}" ({dashboardId})')
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
            raise
        except:
            return list()

    def select_dashboard(self, force=False):
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
                "\nPlease select installation(s) from the list",
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

    def describe_dashboard(self, **kwargs) -> Union[None, Dashboard]:
        """ Describes an AWS QuickSight dashboard
        Keyword arguments:
        DashboardId

        """

        try:
            return Dashboard(self.client.describe_dashboard(AwsAccountId=self.account_id, **kwargs).get('Dashboard'))
        except self.client.exceptions.ResourceNotFoundException:
            return None
        except self.client.exceptions.UnsupportedUserEditionException:
            print('Error: AWS QuickSight Enterprise Edition is required')
            exit(1)

    def delete_dashboard(self, dashboard_id):
        """ Deletes an AWS QuickSight dashboard """
        paramaters = {
            'AwsAccountId': self.account_id,
            'DashboardId': dashboard_id
        }
        return self.client.delete_dashboard(**paramaters)

    def describe_dataset(self, id) -> dict:
        """ Describes an AWS QuickSight dataset """
        try:
            result = self.client.describe_data_set(AwsAccountId=self.account_id,DataSetId=id)
            if not self._datasets.get(result.get('DataSet').get('Name')):
                self._datasets.update({result.get('DataSet').get('Name'): result.get('DataSet')})
        except self.client.exceptions.ResourceNotFoundException:
            logging.info(f'Warning: DataSetId {id} do not exist')
            raise
        except self.client.exceptions.AccessDeniedException:
            logging.info(f'No quicksight:DescribeDataSet permission or missing DataSetId {id}')
            raise
        return result.get('DataSet')

    def describe_data_source(self, id):
        """ Describes an AWS QuickSight data source """
        try:
            result = self.client.describe_data_source(AwsAccountId=self.account_id,DataSourceId=id)
            if not self._datasources.get(result.get('DataSource').get('Arn')):
                self._datasources.update({result.get('DataSource').get('Arn'): result.get('DataSource')})
        except self.client.exceptions.ResourceNotFoundException:
            logging.info(f'Warning: DataSource {id} do not exist')
            raise
        except self.client.exceptions.AccessDeniedException:
            logging.info(f'No quicksight:DescribeDataSource permission or missing DataSetId {id}')
            raise
        return result.get('DataSource')


    def describe_template(self, template_id: str, account_id: str=None ):
        """ Describes an AWS QuickSight template """
        if not account_id:
            account_id=self.cidAccountId
        try:
            result = self.use1Client.describe_template(AwsAccountId=account_id,TemplateId=template_id)
            logging.debug(result)
        except:
            print(f'Error: Template {template_id} is not available in account {account_id}')
            exit(1)
            # return None
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
        response = self.client.create_data_set(**dataset)
        self.describe_dataset(response.get('DataSetId'))

    def create_dashboard(self, dashboard, sleep_duration=1, **kwargs) -> Dashboard:
        """ Creates an AWS QuickSight dashboard """
        DataSetReferences = list()
        for k, v in dashboard.get('datasets', dict()).items():
            DataSetReferences.append({
                'DataSetPlaceholder': k,
                'DataSetArn': v
            })
        
        create_parameters = {
            'AwsAccountId': self.account_id,
            'DashboardId': dashboard.get('dashboardId'),
            'Name': dashboard.get('name'),
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
                    'Arn': f"{dashboard.get('sourceTemplate').get('Arn')}/version/{dashboard.get('sourceTemplate').get('Version').get('VersionNumber')}",
                    'DataSetReferences': DataSetReferences
                }
            }
        }
        
        create_parameters = always_merger.merge(create_parameters, kwargs)
        try:
            create_status = self.client.create_dashboard(**create_parameters)
        except self.client.exceptions.ResourceExistsException:
            raise
        created_version = int(create_status['VersionArn'].split('/')[-1])
        current_status = create_status['CreationStatus']

        # Poll for the current status of query as long as its not finished
        describe_parameters = {
            'DashboardId': dashboard.get('dashboardId'),
            'VersionNumber': created_version
        }
        while current_status in ['CREATION_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
            response = self.describe_dashboard(**describe_parameters)
            current_status = response.version.get('Status')

        if (current_status != "CREATION_SUCCESSFUL"):
            failure_reason = response.version.get('Errors')
            raise Exception(failure_reason)

        return response.dashboard


    def update_dashboard(self, dashboard, sleep_duration=1, **kwargs):
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
                    'Arn': dashboard.sourceTemplate.get('Arn'),
                    'DataSetReferences': DataSetReferences
                }
            }
        }

        update_parameters = always_merger.merge(update_parameters, kwargs)
        update_status = self.client.update_dashboard(**update_parameters)
        updated_version = int(update_status['VersionArn'].split('/')[-1])
        current_status = update_status['CreationStatus']

        # Poll for the current status of query as long as its not finished
        while current_status in ['CREATION_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
            # Sleep before polling again
            time.sleep(sleep_duration)
            dashboard = self.describe_dashboard(DashboardId=dashboard.id, VersionNumber=updated_version)
            current_status = dashboard.version.get('Status')


        if (current_status != "CREATION_SUCCESSFUL"):
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
