import json
import logging
import re
import time
import uuid
from pkg_resources import resource_string
from string import Template
from typing import Dict, List, Union

import click
from deepmerge import always_merger

from cid.base import CidBase
from cid.helpers.quicksight.dashboard import Dashboard
from cid.helpers.quicksight.dataset import Dataset
from cid.helpers.quicksight.datasource import Datasource
from cid.helpers.quicksight.template import Template as CidQsTemplate
from cid.utils import get_parameter, get_parameters
from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

class QuickSight(CidBase):
    # Define defaults
    cidAccountId = '223485597511'
    _AthenaWorkGroup: str = None
    _dashboards: Dict[str, Dashboard] = None
    _datasets: Dict[str, Dataset] = None
    _datasources: Dict[str, Datasource] = None
    _templates: Dict[str, CidQsTemplate] = dict()
    _identityRegion: str = None
    _user: dict = None
    _principal_arn: dict = None
    _group: dict = None
    client = None

    def __init__(self, session, resources=None) -> None:
        self._resources = resources
        super().__init__(session)

        # QuickSight clients
        logger.info(f'Creating QuickSight client')
        self.client = self.session.client('quicksight')
        self.identityClient = self.session.client('quicksight', region_name=self.identityRegion)


    @property
    def AthenaWorkGroup(self) -> str:
        return self._AthenaWorkGroup
    
    @AthenaWorkGroup.setter
    def AthenaWorkGroup(self, value):
        self._AthenaWorkGroup = value

    @property
    def user(self) -> dict:
        if not self._user:
            username = get_parameters().get('quicksight-user', self.username)
            if username:
                try:
                    self._user =  self.describe_user(username)
                except Exception as exc:
                    logger.debug(exc, exc_info=True)
                    logger.error(f'Failed to find your QuickSight username ({exc}). Is QuickSight activated?')
        return self._user

    @property
    def group(self) -> dict:
        if not self._group:
            groupname = get_parameters().get('quicksight-group', None)
            if groupname:
                try:
                    self._group =  self.describe_group(groupname)
                except Exception as exc:
                    logger.debug(exc, stack_info=True)
                    logger.error(f'Failed to find your QuickSight groupname ({exc}). Is QuickSight activated?')
        return self._group

    @property
    def identityRegion(self) -> str:
        if not self._identityRegion:
            try:
                logger.info(f'Detecting QuickSight identity region, trying {self.region}')
                username = get_parameters().get('quicksight-user', self.username)
                parameters = {
                    'AwsAccountId': self.account_id,
                    'UserName': username,
                    'Namespace': 'default'
                }
                self.client.describe_user(**parameters)
                self._identityRegion = self.region
            except self.client.exceptions.AccessDeniedException as e:
                logger.debug(e)
                pattern = f'Operation is being called from endpoint {self.region}, but your identity region is (.*). Please use the (.*) endpoint.'
                match = re.search(pattern, e.response['Error']['Message'])
                if match:
                    logger.info(f'Switching QuickSight identity region to {match.group(1)}')
                    self._identityRegion = match.group(1)
                else:
                    raise
            except self.client.exceptions.ResourceNotFoundException:
                logger.info(f'QuickSight identity region detection failed, using {self.region}')
                self._identityRegion = self.region
            except Exception as e:
                logger.debug(e, exc_info=True)
                logger.info(f'QuickSight identity region detection failed, using {self.region}')
                self._identityRegion = self.region
            logger.info(f'Using QuickSight identity region: {self._identityRegion}')
        return self._identityRegion

    @property
    def edition(self) -> Union[str, None]:
        if not hasattr(self, '_subscription_info'):
            self._subscription_info = self.describe_account_subscription()
        return self._subscription_info.get('Edition')

    @property
    def supported_dashboards(self) -> dict:
        return self._resources.get('dashboards')

    @property
    def supported_datasets(self) -> dict:
        return self._resources.get('datasets')

    @property
    def supported_views(self) -> dict:
        return self._resources.get('views')

    @property
    def dashboards(self) -> Dict[str, Dashboard]:
        """Returns a list of deployed dashboards"""
        if self._dashboards is None:
            self.discover_dashboards()
        return self._dashboards

    @property
    def datasets(self) -> Dict[str, Dataset]:
        """Returns a list of deployed dashboards"""
        if self._datasets is None:
            self.discover_datasets()
        return self._datasets or {}

    @property
    def athena_datasources(self) -> Dict[str, Datasource]:
        """Returns a list of existing athena datasources"""
        return {d.id: d for d in self.get_datasources(type='ATHENA')}

    @property
    def datasources(self) -> Dict[str, Datasource]:
        """Returns a list of existing datasources"""
        if self._datasources is None:
            logger.info(f"Discovering datasources for account {self.account_id}")
            self.discover_data_sources()

        return self._datasources


    def ensure_subscription(self) -> None:
        """Ensure that the QuickSight subscription is active"""

        if not self.edition:
            raise CidCritical('QuickSight is not activated')
        elif self.edition != 'STANDARD':
            logger.info(f'QuickSight subscription: {self._subscription_info}')
        else:
            raise CidCritical(f'QuickSight Enterprise edition is required, you have {self.edition}')

    def describe_account_subscription(self) -> dict:
        """Returns the account subscription details"""
        result = dict()

        try:
            result = self.client.describe_account_subscription(AwsAccountId=self.account_id).get('AccountInfo')
        except self.client.exceptions.AccessDeniedException as e:
            """
            In case we lack privileges to DescribeAccountSubscription API
            we use ListDashboards API call that throws UnsupportedUserEditionException
            in case the account doesn't have Enterprise edition
            """
            logger.info('Insufficient privileges to describe account subscription, working around')
            try:
                self.client.list_dashboards(AwsAccountId=self.account_id).get('AccountInfo')
                result = {'Edition': 'ENTERPRISE'}
            except self.client.exceptions.UnsupportedUserEditionException as e:
                logger.debug(f'UnsupportedUserEditionException means edition is STANDARD: {e}')
                result = {'Edition': 'STANDARD'}
        except self.client.exceptions.ResourceNotFoundException as e:
            logger.debug(e, exc_info=True)
            logger.info('QuickSight not activated')
        except Exception as e:
            logger.debug(e, exc_info=True)
        return result


    def discover_dashboard(self, dashboardId: str) -> Dashboard:
        """Discover single dashboard"""
        dashboard = self.describe_dashboard(DashboardId=dashboardId)
        try:
            _template_arn = dashboard.version.get('SourceEntityArn')
            _template_id = str(_template_arn.split('/')[1])
            _template_version = int(_template_arn.split('/')[-1])
            _template = self.describe_template(template_id=_template_id, version_number=_template_version)
            if isinstance(_template, CidQsTemplate):
                dashboard.deployedTemplate = _template
        except Exception as e:
                logger.debug(e, exc_info=True)
                logger.info(f'Unable to describe template {_template_id}, {e}')
        # Look for dashboard definition by DashboardId
        _definition = next((v for v in self.supported_dashboards.values() if v['dashboardId'] == dashboard.id), None)
        if not _definition:
            # Look for dashboard definition by templateId
            logger.info(dashboard.template_id)
            _definition = next((v for v in self.supported_dashboards.values() if v['templateId'] == dashboard.template_id), None)
        if not _definition:
            logger.info(f'Unsupported dashboard "{dashboard.name}" ({dashboard.template_arn})')
        else:
            logger.info(f'Supported dashboard "{dashboard.name}" ({dashboard.template_arn})')
            dashboard.definition = _definition
            logger.info(f'Found definition for "{dashboard.name}" ({dashboard.template_arn})')
            for dataset in dashboard.version.get('DataSetArns'):
                dataset_id = dataset.split('/')[-1]
                try:
                    _dataset = self.describe_dataset(id=dataset_id)
                    if not isinstance(_dataset, Dataset):
                        logger.info(f'Dataset "{dataset_id}" is missing')
                    else:
                        logger.info(f"Detected dataset: \"{_dataset.name}\" ({_dataset.id} in {dashboard.name})")
                        dashboard.datasets.update({_dataset.name: _dataset.id})
                except self.client.exceptions.AccessDeniedException:
                    logger.info(f'Access denied describing DataSetId {dataset_id} for Dashboard {dashboardId}')
                except self.client.exceptions.InvalidParameterValueException:
                    logger.info(f'Invalid dataset {dataset_id}')
            templateAccountId = _definition.get('sourceAccountId')
            templateId = _definition.get('templateId')
            region = _definition.get('region', 'us-east-1')
            try:
                template = self.describe_template(templateId, account_id=templateAccountId, region=region)
                dashboard.sourceTemplate = template
            except Exception as e:
                logger.debug(e, exc_info=True)
                logger.info(f'Unable to describe template {templateId} in {templateAccountId} ({region})')

            # recoursively add views
            all_views = []
            def _recoursive_add_view(view):
                all_views.append(view)
                for dep_view in (self.supported_views.get(view) or {}).get('dependsOn', {}).get('views', []):
                    _recoursive_add_view(dep_view)
            for dataset_name in dashboard.datasets.keys():
                for view in (self.supported_datasets.get(dataset_name) or {}).get('dependsOn', {}).get('views', []):
                    _recoursive_add_view(view)
            dashboard.views = all_views
            self._dashboards = self._dashboards or {}
            self._dashboards.update({dashboardId: dashboard})
            logger.info(f"{dashboard.name} has {len(dashboard.datasets)} datasets")
            logger.info(f'"{dashboard.name}" ({dashboardId}) discover complete')
            return dashboard

    def ensure_group_exists(self, groupname='cid-owners', description='Created by Cloud Intelligence Dashboards'):
        try:
            group = self.identityClient.describe_group(
                AwsAccountId=self.account_id,
                Namespace='default',
                GroupName=groupname
            ).get('Group')
        except self.client.exceptions.ResourceNotFoundException:
            group = self.identityClient.create_group(
                AwsAccountId=self.account_id,
                GroupName=groupname,
                Namespace='default',
                description=description,
            ).get('Group')
        except self.client.exceptions.AccessDeniedException as e:
            raise CidCritical('Cannot access groups. (AccessDenied). Please use quicksight-user parameter '
                'or ensure you have permissions quicksight::DescribeGroup and quicksight::CreateGroup')
        return group


    def get_principal_arn(self):
        if self._principal_arn:
            return self._principal_arn

        if self.group and self.user:
            raise CidCritical('provided both quicksight-group and quicksight-user. Please keep just one.')
        if self.group:
            self._principal_arn = self.group.get('Arn')
        elif self.user:
            self._principal_arn = self.user.get('Arn')

        if self._principal_arn:
            return self._principal_arn

        # No parameters provided, let's ask user. Following parameter is not supposed to be used by CLI users.
        quicksight_owner = get_parameter('quicksight-owner-choice',
            message='You have not provided quicksight-user or quicksight-group. Do you what your objects to be owned by a user or a group?',
            choices=[
                'group cid-owners (recommended)',
                f'current user {self.username}',
                'other user'],
            default='group cid-owners (recommended)'
        )

        if quicksight_owner.startswith("current user"):
            username = self.username # try with default user, works for IAM users
            if username:
                try:
                    self._user =  self.describe_user(username)
                except Exception as exc:
                    logger.debug(exc, stack_info=True)
                    logger.error(f'Failed to find your QuickSight username ({exc}). Is QuickSight activated?')
            if not self._user:
                self._user = self.select_user()
            if not self._user:
                logger.critical('Cannot get QuickSight username. Is Enteprise subscription activated in QuickSight?')
                exit(1)
            logger.info(f"Using QuickSight user {self._user.get('UserName')}")
            self._principal_arn = self._user.get('Arn')

        elif quicksight_owner.startswith("other user"):
            self._user = self.select_user()
            if not self._user:
                logger.critical('Cannot get QuickSight username. Is Enteprise subscription activated in QuickSight?')
                exit(1)
            self._principal_arn = self._user.get('Arn')

        elif quicksight_owner.startswith("group cid-owners"):
            group = self.ensure_group_exists('cid-owners')
            self._principal_arn = group.get('Arn')

        if not self._principal_arn:
            logger.critical('Cannot find principal_arn. Please provide --quicksight-username or --quicksight-groupname')
            exit(1)

        return self._principal_arn



    def create_data_source(self) -> bool:
        """Create a new data source"""
        logger.info('Creating Athena data source')

        columns_tpl = {
            'PrincipalArn': self.get_principal_arn()
        }
        data_source_permissions_tpl = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name=f'data/permissions/data_source_permissions.json',
        ).decode('utf-8'))
        data_source_permissions = json.loads(data_source_permissions_tpl.safe_substitute(columns_tpl))
        params = {
            "AwsAccountId": self.account_id,
            "DataSourceId": str(uuid.uuid4()),
            "Name": "Athena",
            "Type": "ATHENA",
            "DataSourceParameters": {
                "AthenaParameters": {
                    "WorkGroup": self.AthenaWorkGroup
                }
            },
            "Permissions": [
                data_source_permissions
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
                time.sleep(1)
                datasource = self.describe_data_source(create_status['DataSourceId'], update=True)
                current_status = datasource.status
            if not datasource.is_healthy:
                logger.error(f'Data source creation failed: {datasource.error_info}')
                if get_parameter(
                    param_name='quicksight-delete-failed-datasource',
                    message=f'Data source creation failed: {datasource.error_info}. Delete?',
                    choices=['yes', 'no'],
                ) == 'yes':
                    try:
                        self.delete_data_source(datasource.id)
                    except self.client.exceptions.AccessDeniedException as e:
                        logger.info('Access denied deleting Athena datasource')
                return False
            return True
        except self.client.exceptions.ResourceExistsException:
            logger.error('Data source already exists')
        except self.client.exceptions.AccessDeniedException as e:
            logger.info('Access denied creating Athena datasource')
            logger.debug(e, exc_info=True)
        return False


    def create_folder(self, folder_name: str, **create_parameters) -> dict:
        """Create a new folder"""
        logger.info('Creating QuickSight folder')
        folder_id = str(uuid.uuid4())
        create_parameters.update({
            "AwsAccountId": self.account_id,
            "FolderId": folder_id,
            "Name": folder_name,
            "FolderType": "SHARED",
        })
        try:
            logger.info(f'Creating folder {create_parameters}')
            result = self.client.create_folder(**create_parameters)
            logger.debug(f'Folder creation result {result}')
            if (result.get('Status') != 200):
                logger.info(f'Folder creation failed with status {result.get("Status")}')
                return None
            folder = self.describe_folder(result['FolderId'])
            return folder
        except self.client.exceptions.ResourceExistsException:
            logger.info('Folder already exists')
            return self.describe_folder(folder_id)
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied creating folder')
            raise
        return None

    def create_folder_membership(self, folder_id: str, member_id: str, member_type: str) -> bool:
        """Create a new folder membership"""
        logger.info(f'Creating folder membership for {member_type}: {member_id}')
        params = {
            "AwsAccountId": self.account_id,
            "FolderId": folder_id,
            "MemberId": member_id,
            "MemberType": member_type
        }
        try:
            logger.info(f'Creating folder membership {params}')
            result = self.client.create_folder_membership(**params)
            logger.debug(f'Folder membership creation result {result}')
            logger.info(f'Folder membership creation status {result.get("Status")}')
            if (result['Status'] != 200):
                logger.info(f'Folder membership creation failed with code {result.get("Status")}')
                return False
            return True
        except self.client.exceptions.ResourceExistsException:
            logger.error('Folder membership already exists')
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied creating folder membership')
        return False

    def discover_data_sources(self) -> None:
        """ Discover existing datasources"""
        if self._datasources is None:
            self._datasources = {}
        logger.info('Discovering existing datasources')
        try:
            for v in self.list_data_sources():
                _datasource = Datasource(v)
                logger.info(f'Found datasource "{_datasource.name}" ({_datasource.id}) status={_datasource.status}')
                self._datasources.update({_datasource.id: _datasource})
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied discovering data sources')
            for v in self.datasets.values():
                for d in v.datasources:
                    self.describe_data_source(d)
        except Exception as e:
            logger.debug(e, exc_info=True)

    def discover_dashboards(self, display: bool=False, refresh: bool=False) -> None:
        """ Discover deployed dashboards """
        if refresh or self._dashboards is None:
            self._dashboards = {}
        logger.info('Discovering deployed dashboards')
        deployed_dashboards=self.list_dashboards()
        logger.info(f'Found {len(deployed_dashboards)} deployed dashboards')
        logger.debug(deployed_dashboards)
        with click.progressbar(
            length=len(deployed_dashboards),
            label='Discovering deployed dashboards...',
            item_show_func=lambda a: str(a)[:50]
        ) as bar:
            for dashboard in deployed_dashboards:
                # Discover found dashboards
                dashboardName = dashboard.get('Name')
                dashboardId = dashboard.get('DashboardId')
                # Update progress bar
                bar.update(1, f'"{dashboardName}" ({dashboardId})')
                logger.info(f'Discovering dashboard "{dashboardName}" ({dashboardId})')
                self.discover_dashboard(dashboardId)
                # Update progress bar
                bar.update(0, 'Complete')
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
                raise CidCritical(f'list_dashboards: {result}')
            else:
                logger.debug(result)
                return result.get('DashboardSummaryList')
        except Exception as e:
            logger.debug(e, exc_info=True)
            return list()

    def list_data_sources(self) -> list:
        parameters = {
            'AwsAccountId': self.account_id
        }
        data_sources = []
        try:
            for page in self.client.get_paginator('list_data_sources').paginate(**parameters):
                data_sources += page.get('DataSources',[])
            return data_sources
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied listing data sources')
            raise
        except Exception as e:
            logger.debug(e, exc_info=True)
            return list()

    def select_dashboard(self, force=False) -> str:
        """ Select from a list of discovered dashboards """
        selection = list()
        dashboard_id = None
        if not self.dashboards:
            return None
        choices = {}
        for dashboard in self.dashboards.values():
            health = 'healthy' if dashboard.health else 'unhealthy'
            key = f'{dashboard.name} ({dashboard.arn}, {health}, {dashboard.status})'
            if ((dashboard.latest or not dashboard.health) and not force):
                choices[key] = None
            else:
                choices[key] = dashboard.id
        try:
            dashboard_id = get_parameter(
                param_name='dashboard-id',
                message="Please select installation(s) from the list",
                choices=choices,
                none_as_disabled=True,
            )
        except AttributeError as e:
            # No updatable dashboards (selection is disabled)
            logger.debug(e, exc_info=True)
        except Exception as e:
            logger.exception(e)
        finally:
            return dashboard_id

    def select_user(self):
        """ Select a user from the list of users """
        user_list = None
        try:
            user_list = self.identityClient.list_users(AwsAccountId=self.account_id, Namespace='default').get('UserList')
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied listing users')
            return None #FIXME: should we rather allow manual entry when no access?

        _username = get_parameter(
            param_name='quicksight-user',
            message="Please select QuickSight user to use",
            choices={f"{user.get('UserName')} ({user.get('Email')}, {user.get('Role')})":user.get('UserName') for user in user_list}
        )
        for u in user_list:
            if u.get('UserName') == _username:
                return u
        else:
            return None

    def list_data_sets(self):
        parameters = {
            'AwsAccountId': self.account_id
        }
        try:
            result = self.client.list_data_sets(**parameters)
            if result.get('Status') != 200:
                raise CidCritical(f'list_data_sets: {result}')
            else:
                return result.get('DataSetSummaries')
        except self.client.exceptions.AccessDeniedException:
            raise
        except Exception as e:
            logger.debug(e, exc_info=True)
            return None


    def list_folders(self) -> list:
        parameters = {
            'AwsAccountId': self.account_id
        }
        try:
            result = self.client.list_folders(**parameters)
            if result.get('Status') != 200:
                 raise CidCritical(f'list_folders: {result}')
            else:
                logger.debug(f"FolderList: {result.get('FolderSummaryList')}")
                return result.get('FolderSummaryList')
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied listing folders')
            raise
        except Exception as e:
            logger.debug(e, exc_info=True)
            return None


    def describe_folder(self, folder_id: str) -> dict:
        parameters = {
            'AwsAccountId': self.account_id,
            'FolderId': folder_id
        }
        try:
            result = self.client.describe_folder(**parameters)
            logger.debug(f"DescribeFolder: {result}")
            if result.get('Status') != 200:
                raise CidCritical(f'describe_folder : {result}')
            else:
                logger.debug(result.get('Folder'))
                return result.get('Folder')
        except Exception as e:
            logger.debug(e, exc_info=True)
            return None


    def select_folder(self):
        """ Select a folder from the list of folders """
        try:
            folderList = self.list_folders()
            if not folderList:
                return None
        except self.client.exceptions.AccessDeniedException:
            raise

        _folder = get_parameter(
            param_name='folder-id',
            message="Please select QuickSight folder to use",
            choices={f"{folder.get('Name')} ({folder.get('FolderId')})":folder for folder in folderList}
        )
        return _folder


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
            raise CidCritical('Error: AWS QuickSight Enterprise Edition is required')
        except Exception as e:
            print(f'Error: {e}')
            raise

    def delete_dashboard(self, dashboard_id):
        """ Deletes an AWS QuickSight dashboard """
        paramaters = {
            'AwsAccountId': self.account_id,
            'DashboardId': dashboard_id
        }
        logger.info(f'Deleting dashboard {dashboard_id}')
        result = self.client.delete_dashboard(**paramaters)
        del self._dashboards[dashboard_id]
        return result

    def delete_data_source(self, datasource_id):
        """ Deletes an AWS QuickSight dashboard """
        paramaters = {
            'AwsAccountId': self.account_id,
            'DataSourceId': datasource_id
        }
        logger.info(f'Deleting DataSource {datasource_id}')
        result = self.client.delete_data_source(**paramaters)
        if datasource_id in self._datasources:
            del self._datasources[datasource_id]
        return result

    def delete_dataset(self, id: str) -> bool:
        """ Deletes an AWS QuickSight dataset """

        logger.info(f'Deleting dataset {id}')
        try:
            self.client.delete_data_set(
                AwsAccountId=self.account_id,
                DataSetId=id
            )
            self.datasets.pop(id)
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied deleting dataset')
            return False
        except self.client.exceptions.ResourceNotFoundException:
            logger.info('Dataset does not exist')
            return False
        else:
            logger.info(f'Deleted dataset {id}')
            return True


    def get_datasets(self, id: str=None, name: str=None) -> List[Dataset]:
        """ get dataset that match parameters """
        result = []
        for dataset in self.datasets.values():
            if id is not None and dataset.id != id:
                continue
            if name is not None and dataset.name != name:
                continue
            result.append(dataset)
        return result


    def get_datasources(self, id: str=None, name: str=None, type: str=None, athena_workgroup_name: str=None, healthy: bool=True) -> List[Datasource]:
        """ get datasource that matches parameters """
        result = []
        for datasource in self.datasources.values():
            if healthy is not None and datasource.is_healthy != healthy:
                continue
            if id is not None and datasource.id != id:
                continue
            if name is not None and datasource.name != name:
                continue
            if type is not None and datasource.type != type:
                continue
            if athena_workgroup_name is not None and datasource.AthenaParameters.get('WorkGroup') != athena_workgroup_name:
                continue
            result.append(datasource)
        return result


    def describe_dataset(self, id, timeout: int=1) -> Dataset:
        """ Describes an AWS QuickSight dataset """
        if self._datasets and id in self._datasets:
            return self._datasets.get(id)
        self._datasets = self._datasets or {}
        poll_interval = 1
        _dataset = None
        deadline = time.time() + timeout
        while time.time() <= deadline:
            try:
                _dataset = Dataset(self.client.describe_data_set(AwsAccountId=self.account_id,DataSetId=id).get('DataSet'))
                logger.info(f'Saving dataset details "{_dataset.name}" ({_dataset.id})')
                self._datasets.update({_dataset.id: _dataset})
                break
            except self.client.exceptions.ResourceNotFoundException:
                logger.info(f'DataSetId {id} not found')
                time.sleep(poll_interval)
                continue
            except self.client.exceptions.AccessDeniedException:
                logger.debug(f'No quicksight:DescribeDataSet permission or missing DataSetId {id}')
                return None

        return self._datasets.get(id, None)

    def discover_datasets(self, _datasets: list=None):
        """ Discover datasets in the account """

        logger.info('Discovering datasets')
        self._datasets =  self._datasets or {}
        if _datasets:
            for dataset in _datasets:
                self.describe_dataset(dataset)
        try:
            for dataset in self.list_data_sets():
                try:
                    self.describe_dataset(dataset.get('DataSetId'))
                except Exception as e:
                    logger.debug(e, exc_info=True)
                    continue
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied listing datasets')
        except Exception as e:
            logger.debug(e, exc_info=True)
            logger.info('No datasets found')


    def describe_data_source(self, id: str, update: bool=False) -> Datasource:
        """ Describes an AWS QuickSight DataSource """
        if not update and self.datasources and id in self.datasources:
            return self.datasources.get(id)
        try:
            logger.info(f'Discovering DataSource {id}')
            result = self.client.describe_data_source(AwsAccountId=self.account_id, DataSourceId=id)
            logger.debug(result)
            _datasource = Datasource(result.get('DataSource'))
            logger.info(f'DataSource "{_datasource.name}" status is {_datasource.status}, saving details')
            self._datasources.update({_datasource.id: _datasource})
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f'DataSource {id} do not exist')
            raise
        except self.client.exceptions.AccessDeniedException:
            logger.info(f'No quicksight:DescribeDataSource permission or missing DataSetId {id}')
            raise
        except Exception as e:
            logger.info(e)
            logger.debug(e, exc_info=True)
            return None
        else:
            return _datasource


    def describe_template(self, template_id: str, version_number: int=None, account_id: str=None, region: str='us-east-1') -> CidQsTemplate:
        """ Describes an AWS QuickSight template """
        if not account_id:
            account_id=self.cidAccountId
        if not self._templates.get(f'{account_id}:{region}:{template_id}:{version_number}'):
            try:
                client = self.session.client('quicksight', region_name=region)
                parameters = {
                    'AwsAccountId': account_id,
                    'TemplateId': template_id
                }
                if version_number: parameters.update({'VersionNumber': version_number})
                result = client.describe_template(**parameters)
                self._templates.update({f'{account_id}:{region}:{template_id}:{version_number}': CidQsTemplate(result.get('Template'))})
                logger.debug(result)
            except self.client.exceptions.UnsupportedUserEditionException:
                raise CidCritical('AWS QuickSight Enterprise Edition is required')
            except self.client.exceptions.ResourceNotFoundException:
                raise CidCritical(f'Error: Template {template_id} is not available in account {account_id} and region {region}')
            except Exception as e:
                logger.debug(e, exc_info=True)
                raise CidCritical(f'Error: {e} - Cannot find {template_id} in account {account_id}.')
        return self._templates.get(f'{account_id}:{region}:{template_id}:{version_number}')

    def describe_user(self, username: str) -> dict:
        """ Describes an AWS QuickSight user """
        parameters = {
            'AwsAccountId': self.account_id,
            'UserName': username,
            'Namespace': 'default'
        }
        try:
            result = self.identityClient.describe_user(**parameters)
            logger.debug(result)
            return result.get('User')
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f'QuickSight user {username} not found.')
            return None
        except self.client.exceptions.AccessDeniedException:
            userList = self.identityClient.list_users(AwsAccountId=self.account_id, Namespace='default').get('UserList')
            logger.debug(userList)
            for user in userList:
                if username.endswith(user.get('UserName')):
                    logger.info(f'Found user: {user}')
                    return user
            logger.info(f'QuickSight user {username} not found.')
            return None

    def describe_group(self, groupname: str) -> dict:
        """ Describes an AWS QuickSight Group """
        try:
            result = self.identityClient.describe_group(**{
                'AwsAccountId': self.account_id,
                'GroupName': groupname,
                'Namespace': 'default'
            })
            logger.debug('group = ',json.dumps(result))
            return result.get('Group')
        except self.client.exceptions.ResourceNotFoundException:
            logger.error(f'QuickSight group {groupname} not found.')
            return None
        except self.client.exceptions.AccessDeniedException: # Try to overcome AccessDeniedException
            #FIXME: paginator is not available for list_groups
            logger.error(f'AccessDeniedException when trying to DescribeGroup in QuickSight.')
            return None


    def create_dataset(self, definition: dict) -> str:
        """ Creates an AWS QuickSight dataset """
        poll_interval = 1
        max_timeout = 60
        columns_tpl = {
            'PrincipalArn': self.get_principal_arn()
        }
        data_set_permissions_tpl = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name=f'data/permissions/data_set_permissions.json',
        ).decode('utf-8'))
        data_set_permissions = json.loads(data_set_permissions_tpl.safe_substitute(columns_tpl))
        definition.update({
            'AwsAccountId': self.account_id,
            'Permissions': [
                data_set_permissions
            ]
        })
        dataset_id = None
        try:
            logger.info(f'Creating dataset {definition.get("Name")} ({dataset_id})')
            logger.debug(f'Dataset definition: {definition}')
            response = self.client.create_data_set(**definition)
            dataset_id = response.get('DataSetId')
        except self.client.exceptions.ResourceExistsException:
            dataset_id = definition.get("DataSetId")
            logger.info(f'Dataset {definition.get("Name")} already exists with DataSetId={dataset_id}')
        except self.client.exceptions.LimitExceededException:
            raise CidCritical('AWS QuickSight SPICE limit exceeded. Add SPICE here https://quicksight.aws.amazon.com/sn/admin#capacity .')

        logger.info(f'Waiting for {definition.get("Name")} to be created')
        deadline = time.time() + max_timeout
        while time.time() < deadline:
            _dataset = self.describe_dataset(dataset_id)
            if isinstance(_dataset, Dataset):
                break
            else:
                time.sleep(poll_interval)
        else:
            logger.info(f'Dataset {definition.get("Name")} is not created before timeout.')
            return None
        logger.info(f'Dataset {_dataset.name} is created')
        return dataset_id


    def update_dataset(self, definition: dict) -> str:
        """ Creates an AWS QuickSight dataset """
        definition.update({'AwsAccountId': self.account_id})
        logger.info(f'Updating dataset {definition.get("Name")}')

        if "Permissions" in definition:
            logger.info('Ignoring permissions for dataset update.')
            del definition['Permissions']
        response = self.client.update_data_set(**definition)
        logger.info(f'Dataset {definition.get("Name")} is updated')
        return True


    def create_dashboard(self, definition: dict, **kwargs) -> Dashboard:
        """ Creates an AWS QuickSight dashboard """
        DataSetReferences = list()
        for k, v in definition.get('datasets', dict()).items():
            DataSetReferences.append({
                'DataSetPlaceholder': k,
                'DataSetArn': v
            })
        
        dashboard_permissions_tpl = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name=f'data/permissions/dashboard_permissions.json',
        ).decode('utf-8'))
        columns_tpl = {
            'PrincipalArn': self.get_principal_arn()
        }
        dashboard_permissions = json.loads(dashboard_permissions_tpl.safe_substitute(columns_tpl))
        create_parameters = {
            'AwsAccountId': self.account_id,
            'DashboardId': definition.get('dashboardId'),
            'Name': definition.get('name'),
            'Permissions': [
                dashboard_permissions
            ],
            'SourceEntity': {
                'SourceTemplate': {
                    'Arn': f"{definition.get('sourceTemplate').arn}/version/{definition.get('sourceTemplate').version}",
                    'DataSetReferences': DataSetReferences
                }
            }
        }
        
        create_parameters = always_merger.merge(create_parameters, kwargs)
        try:
            logger.info(f'Creating dashboard "{definition.get("name")}"')
            logger.debug(create_parameters)
            create_status = self.client.create_dashboard(**create_parameters)
            logger.debug(create_status)
        except self.client.exceptions.ResourceExistsException:
            logger.info(f'Dashboard {definition.get("name")} already exists')
            raise
        created_version = int(create_status['VersionArn'].split('/')[-1])

        # Poll for the current status of query as long as its not finished
        describe_parameters = {
            'DashboardId': definition.get('dashboardId'),
            'VersionNumber': created_version
        }
        dashboard = self.describe_dashboard(poll=True, **describe_parameters)
        self.discover_dashboard(dashboard.id)
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
                'DataSetArn': self.datasets.get(v).arn
            })

        update_parameters = {
            'AwsAccountId': self.account_id,
            'DashboardId': dashboard.id,
            'Name': dashboard.name,
            'SourceEntity': {
                'SourceTemplate': {
                    'Arn': f"{dashboard.sourceTemplate.arn}/version/{dashboard.latest_version}",
                    'DataSetReferences': DataSetReferences
                }
            }
        }

        update_parameters = always_merger.merge(update_parameters, kwargs)
        logger.info(f'Updating dashboard "{dashboard.name}"')
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
        logger.debug(result)
        if result['Status'] != 200:
            raise Exception(result)

        return result


    def update_dashboard_permissions(self, **update_parameters):
        """ Updates an AWS QuickSight dashboard permissions """
        logger.debug(f"Updating Dashboard permissions: {update_parameters}")
        update_parameters.update({'AwsAccountId': self.account_id})
        update_status = self.client.update_dashboard_permissions(**update_parameters)
        logger.debug(update_status)
        return update_status


    def update_data_set_permissions(self, **update_parameters):
        """ Updates an AWS QuickSight dataset permissions """
        logger.debug(f"Updating DataSet permissions: {update_parameters}")
        update_parameters.update({'AwsAccountId': self.account_id})
        update_status = self.client.update_data_set_permissions(**update_parameters)
        logger.debug(update_status)
        return update_status


    def update_data_source_permissions(self, **update_parameters):
        """ Updates an AWS QuickSight data source permissions """
        logger.debug(f"Updating DataSource permissions: {update_parameters}")
        update_parameters.update({'AwsAccountId': self.account_id})
        update_status = self.client.update_data_source_permissions(**update_parameters)
        logger.debug(update_status)
        return update_status


    def update_template_permissions(self, **update_parameters):
        """ Updates an AWS QuickSight template permissions """
        logger.debug(f"Updating Template permissions: {update_parameters}")
        update_parameters.update({'AwsAccountId': self.account_id})
        update_status = self.client.update_template_permissions(**update_parameters)
        logger.debug(update_status)
        return update_status
