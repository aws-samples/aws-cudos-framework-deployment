import re
import io
import json
import uuid
import time
import datetime
import logging
import yaml
from string import Template
from typing import Dict, List, Union
from pkg_resources import resource_string

from tqdm import tqdm

from cid.base import CidBase
from cid.helpers import diff, timezone, randtime
from cid.helpers.quicksight.dashboard import Dashboard
from cid.helpers.quicksight.dataset import Dataset
from cid.helpers.quicksight.datasource import Datasource
from cid.helpers.quicksight.template import Template as CidQsTemplate
from cid.helpers.quicksight.definition import Definition as CidQsDefinition
from cid.utils import get_parameter, get_parameters, exec_env, cid_print, ago, unset_parameter
from cid.exceptions import CidCritical, CidError

logger = logging.getLogger(__name__)

class QuickSight(CidBase):
    # Define defaults
    cidAccountId = '223485597511'
    _AthenaWorkGroup: str = None
    _dashboards: Dict[str, Dashboard] = None
    _datasets: Dict[str, Dataset] = None
    _datasources: Dict[str, Datasource] = None
    _templates: Dict[str, CidQsTemplate] = dict()
    _definitions: Dict[str, CidQsDefinition] = dict()
    _identityRegion: str = None
    _user: dict = None
    _principal_arn: dict = None
    _group: dict = None
    _subscription_info: dict = None
    client = None

    def __init__(self, session, resources=None) -> None:
        self._resources = resources
        super().__init__(session)

        # QuickSight clients
        logger.info('Creating QuickSight client')
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
            except self.client.exceptions.AccessDeniedException as exc:
                logger.debug(exc)
                pattern = f'Operation is being called from endpoint {self.region}, but your identity region is (.*). Please use the (.*) endpoint.'
                match = re.search(pattern, exc.response['Error']['Message'])
                if match:
                    logger.info(f'Switching QuickSight identity region to {match.group(1)}')
                    self._identityRegion = match.group(1)
                else:
                    raise
            except self.client.exceptions.ResourceNotFoundException:
                logger.info(f'QuickSight identity region detection failed, using {self.region}')
                self._identityRegion = self.region
            except Exception as exc:
                logger.debug(exc, exc_info=True)
                logger.info(f'QuickSight identity region detection failed, using {self.region}')
                self._identityRegion = self.region
            logger.info(f'Using QuickSight identity region: {self._identityRegion}')
        return self._identityRegion

    def edition(self, fresh: bool=False) -> str:
        """ get QuickSight Edition
        :fresh: set to True if you want it fresh (not cached)
        """
        if fresh or not hasattr(self, '_subscription_info'):
            self._subscription_info = self.describe_account_subscription()
        status = self._subscription_info.get('AccountSubscriptionStatus')
        if status != 'ACCOUNT_CREATED':
            return None
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
        """Ensure that the Amazon QuickSight subscription is active"""
        if not self.edition(fresh=True):
            raise CidCritical('Amazon QuickSight is not activated. Please run `cid-cmd initqs` command, or activate QuickSight Enterprise Edition from the console.')
        if self.edition() == 'STANDARD':
            raise CidCritical(f'Amazon QuickSight Enterprise edition is required, you have {self.edition}.')
        logger.info(f'QuickSight subscription: {self._subscription_info}')

    def describe_account_subscription(self) -> dict:
        """Returns the account subscription details"""
        result = {}

        try:
            result = self.client.describe_account_subscription(AwsAccountId=self.account_id).get('AccountInfo')
        except self.client.exceptions.AccessDeniedException:
            # In case we lack privileges to DescribeAccountSubscription API
            # we use ListDashboards API call that throws UnsupportedUserEditionException
            # in case the account doesn't have Enterprise edition
            logger.info('Insufficient privileges to describe account subscription, working around')
            try:
                self.client.list_dashboards(AwsAccountId=self.account_id)
                result = {'Edition': 'ENTERPRISE', 'AccountSubscriptionStatus': 'ACCOUNT_CREATED'}
            except self.client.exceptions.UnsupportedUserEditionException as exc:
                logger.debug(f'UnsupportedUserEditionException means edition is STANDARD: {exc}')
                result = {'Edition': 'STANDARD', 'AccountSubscriptionStatus': 'ACCOUNT_CREATED'}
        except self.client.exceptions.ResourceNotFoundException as exc:
            logger.debug(exc, exc_info=True)
            logger.info('QuickSight not activated?')
        except Exception as exc:
            logger.debug(exc, exc_info=True)
        return result


    def discover_dashboard(self, dashboardId: str, refresh: bool = False) -> Dashboard:
        """Discover a single dashboard: describe and pull downstream info (datasets, related templates and views) """

        def _safe_int(value, default=None):
            """Safe int from string"""
            return int(str(value)) if str(value).isdecimal() else default

        dashboard = self.describe_dashboard(DashboardId=dashboardId)
        if not dashboard:
            raise CidCritical(f'Dashboard {dashboardId} was not found')
        # Look for dashboard definition by DashboardId in the catalog of supported dashboards (the currently available definitions in their latest public version)
        # This definition can be used to determine the gap between the latest public version and the currently deployed version
        _definition = next((v for v in self.supported_dashboards.values() if v['dashboardId'] == dashboard.id), None)
        if not _definition:
            # Look for dashboard definition by templateId.
            # This is for a specific use-case when a dashboard with another id points to managed template
            source_arn = dashboard.raw.get('Version', {}).get('SourceEntityArn', '')
            if source_arn:
                template_id = source_arn.split('/version/')[0].split('/')[-1]
                template_account = source_arn.split(':').pop(4)
                logger.info(template_id)
                _definition = next((v for v in self.supported_dashboards.values() if 'templateId' in v and v['templateId'] == template_id), None)
        if not _definition:
            logger.info(f'Unsupported dashboard "{dashboard.name}" ({dashboard.template_arn})')
            return None

        logger.info(f'Supported dashboard "{dashboard.name}" ({dashboard.template_arn})')
        dashboard.definition = _definition
        logger.info(f'Found definition for "{dashboard.name}" ({dashboard.template_arn})')

        # Check for extra information from resource definition
        version_obj = _definition.get('versions', dict())
        min_template_version = _safe_int(version_obj.get('minTemplateVersion'))
        default_description_version = version_obj.get('minTemplateDescription')

        # Fetch template referenced as dashboard source (if any)
        _template_arn = dashboard.version.get('SourceEntityArn')
        if _template_arn and isinstance(_template_arn, str) \
            and len(_template_arn.split(':')) > 5 \
            and _template_arn.split(':')[5].startswith('template/'):

            params = {
                "template_id": _template_arn.split('/')[1],
                "account_id": _template_arn.split(':')[4],
                "region": _template_arn.split(':')[3]
            }

            if '/version/' in _template_arn:
                params['version_number'] = _safe_int(_template_arn.split('/version/')[-1])
            elif min_template_version:
                logger.info(f"Using default version number {min_template_version} in place")
                params['version_number'] = min_template_version

            if 'version_number' in params:
                try:
                    _template = self.describe_template(**params)
                    if isinstance(_template, CidQsTemplate):
                        dashboard.deployedTemplate = _template
                except Exception as exc:
                    logger.debug(exc, exc_info=True)
                    logger.info(f'Unable to describe template for {dashboardId}, {exc}')
            else:
                logger.info("Minimum template version could not be found for Dashboard {dashboardId}: {_template_arn}, deployed template could not be described")
        else: # Dashboard is not template based but definition based
            try:
                dashboard.deployedDefinition = self.describe_dashboard_definition(dashboard_id=dashboardId, refresh=refresh)
            except CidError as exc:
                logger.info('Exception on reading dashboard definition {dashboardId}: {exc}. Not critical. Continue.')

        if 'data' in _definition:
            # Resolve source definition (the latest definition publicly available)
            data_stream = io.StringIO(_definition["data"])
            definition_data = yaml.safe_load(data_stream)
            dashboard.sourceDefinition = CidQsDefinition(definition_data)

        # Fetch datasets (works for both TEMPLATE and DEFINITION based dashboards)
        for dataset in dashboard.version.get('DataSetArns', []):
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
        logger.info(f"{dashboard.name} has {len(dashboard.datasets)} datasets")

        # Fetch the latest version of sourceTemplate referenced in definition
        source_template_account_id = _definition.get('sourceAccountId')
        template_id = _definition.get('templateId')
        region = _definition.get('region', 'us-east-1')
        if template_id:
            try:
                logger.debug(f'Loading latest source template {template_id} from source account {source_template_account_id} in {region}')
                template = self.describe_template(template_id, account_id=source_template_account_id, region=region)
                dashboard.sourceTemplate = template
            except Exception as exc:
                logger.debug(exc, exc_info=True)
                logger.info(f'Unable to describe template {template_id} in {source_template_account_id} ({region})')

        # Checking for version override in template definition
        for dashboard_template in [dashboard.deployedTemplate, dashboard.sourceTemplate]:
            if not isinstance(dashboard_template, CidQsTemplate)\
                or int(dashboard_template.version) <= 0 \
                or not version_obj:
                continue

            logger.debug("versions object found in template")
            version_map = version_obj.get('versionMap', dict())
            description_override = version_map.get(int(dashboard_template.version))

            try:
                if description_override:
                    logger.info(f"Template description is overridden with: {description_override}")
                    description_override = str(description_override)
                    dashboard_template.raw['Version']['Description'] = description_override
                else:
                    if min_template_version and default_description_version:
                        if int(dashboard_template.version) <= min_template_version:
                            logger.info(f"The template version does not provide cid_version in description, using the default template description: {default_description_version}")
                            dashboard_template.raw['Version']['Description'] = default_description_version
            except ValueError as val_error:
                logger.debug(val_error,  exc_info=True)
                logger.info("The provided values of the versions object are not well formed, please use int for template version and str for template description")
            except Exception as exc:
                logger.debug(exc, exc_info=True)
                logger.info("Unable to override template description")

        # Fetch all views recursively (works for both TEMPLATE and DEFINITION based dashboards)
        all_views = []
        def _recursive_add_view(view):
            all_views.append(view)
            for dep_view in (self.supported_views.get(view) or {}).get('dependsOn', {}).get('views', []):
                _recursive_add_view(dep_view)
        for dataset_name in dashboard.datasets:
            for view in (self.supported_datasets.get(dataset_name) or {}).get('dependsOn', {}).get('views', []):
                _recursive_add_view(view)
        dashboard.views = all_views
        self._dashboards = self._dashboards or {}
        self._dashboards[dashboardId] = dashboard
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
                Description=description,
            ).get('Group')
        except self.client.exceptions.AccessDeniedException as exc:
            raise CidCritical('Cannot access groups. (AccessDenied). Please use quicksight-user parameter '
                'or ensure you have permissions quicksight::DescribeGroup and quicksight::CreateGroup') from exc
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
        auth_type = self.describe_account_subscription().get('AuthenticationType')
        if auth_type not in ["ACTIVE_DIRECTORY", 'IAM_IDENTITY_CENTER']:
            choices = [
                'group cid-owners (recommended)',
                'select group',
                f'current user {self.username}',
                'select user',
            ]
        else: # cannot create groups if managed by AD or IAM IC. And cannot read users.
            choices = [
                'select group',
                'select user',
            ]
        quicksight_owner = get_parameter('quicksight-owner-choice',
            message='You have not provided quicksight-user or quicksight-group. Do you what your objects to be owned by a user or a group?',
            choices=choices,
            default=choices[0],
        )

        if quicksight_owner.startswith("current user"):
            try:
                self._user =  self.describe_user(self.username) # Only works for IAM
            except Exception as exc:
                logger.debug(exc, stack_info=True)
                logger.error(f'Failed to find your QuickSight username ({exc}). Is QuickSight activated? Is there a user ({self.username})?')
            if not self._user:
                self._user = self.select_user() # fallback to user choice
            if not self._user:
                raise CidCritical('Cannot get QuickSight username. Is Enterprise subscription activated in QuickSight?')
            logger.info(f"Using QuickSight user {self._user.get('UserName')}")
            self._principal_arn = self._user.get('Arn')

        elif quicksight_owner.startswith("select group"):
            self._group = self.select_group()
            if not self._group:
                raise CidCritical('Cannot get QuickSight group.')
            self._principal_arn = self._group.get('Arn')

        elif quicksight_owner.startswith("select user"):
            self._user = self.select_user()
            if not self._user:
                raise CidCritical('Cannot get QuickSight username. Is Enterprise subscription activated in QuickSight?')
            self._principal_arn = self._user.get('Arn')

        elif quicksight_owner.startswith("group cid-owners"):
            group = self.ensure_group_exists('cid-owners')
            self._principal_arn = group.get('Arn')

        if not self._principal_arn:
            raise CidCritical('Cannot find principal_arn. Please provide --quicksight-username or --quicksight-groupname')
        return self._principal_arn


    def create_data_source(self, athena_workgroup, datasource_id: str=None, role_arn: str=None) -> Datasource:
        """Create a new data source"""
        logger.info('Creating Athena data source')

        columns_tpl = {
            'PrincipalArn': self.get_principal_arn()
        }
        data_source_permissions_tpl = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name='data/permissions/data_source_permissions.json',
        ).decode('utf-8'))
        data_source_permissions = json.loads(data_source_permissions_tpl.safe_substitute(columns_tpl))
        datasource_name = datasource_id or "CID Athena"
        datasource_id = datasource_id or str(uuid.uuid4())
        params = {
            "AwsAccountId": self.account_id,
            "DataSourceId": datasource_id,
            "Name": datasource_name,
            "Type": "ATHENA",
            "DataSourceParameters": {
                "AthenaParameters": {
                    "WorkGroup": athena_workgroup,
                }
            },
            "Permissions": [
                data_source_permissions
            ]
        }
        if role_arn:
            params['DataSourceParameters']['AthenaParameters']['RoleArn'] = role_arn
        try:
            logger.info(f'Creating data source {params}')
            create_status = self.client.create_data_source(**params)
            logger.debug(f'Data source creation result {create_status}')
            # Wait for the datasource completion
            for _ in tqdm(range(60), desc='DataSet Creation', leave=False):
                time.sleep(1)
                datasource = self.describe_data_source(datasource_id, update=True)
                logger.debug(f'Waiting for datasource {datasource_id}. current status={datasource.status}')
                if not datasource.status.endswith('IN_PROGRESS'):
                    break
            if not datasource.is_healthy:
                logger.error(f'DataSource parameters: {json.dumps(params, indent=2)}')
                logger.error(f'DataSource creation failed: {datasource.error_info}.')
                if "The QuickSight service role required to access your AWS resources has not been created yet." in str(datasource.error_info):
                    logger.error(
                        'Please check that QuickSight has a default role that can access S3 Buckets and Athena https://quicksight.aws.amazon.com/sn/admin?#aws '
                        'OR provide a custom datasource role as a parameter --quicksight-datasource-role-arn'
                    )
                if get_parameter(
                    param_name='quicksight-delete-failed-datasource',
                    message=f'Data source creation failed: {datasource.error_info}. Delete(recommended)?',
                    choices=['yes', 'no'],
                    default='yes'
                ) == 'yes':
                    try:
                        self.delete_data_source(datasource.id)
                    except self.client.exceptions.AccessDeniedException:
                        logger.info('Access denied deleting Athena datasource')
                return None
            for _ in tqdm(range(5), desc='Waiting for Data Source', leave=False):
                time.sleep(1)
            return datasource
        except self.client.exceptions.ResourceExistsException:
            datasource = self.describe_data_source(datasource_id, update=True)
            logger.error(f'Data source already exists {datasource.raw}')
            if not datasource.is_healthy:
                if get_parameter(
                    param_name='quicksight-delete-failed-datasource',
                    message=f'Data source creation failed: {datasource.error_info}. Delete?',
                    choices=['yes', 'no'],
                ) == 'yes':
                    try:
                        self.delete_data_source(datasource.id)
                        raise CidCritical('Issue on datasource creation. Please retry.')
                    except self.client.exceptions.AccessDeniedException:
                        raise CidCritical('Access denied deleting datasource in QS. Please cleanup manually and retry.')
            return datasource
        except self.client.exceptions.AccessDeniedException as exc:
            logger.info('Access denied creating Athena datasource')
            logger.debug(exc, exc_info=True)
            return None
        return None

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
        except Exception as exc:
            logger.debug(exc, exc_info=True)
    
    def discover_dashboards(self, refresh_overrides: List[str]=[], refresh: bool = False) -> None:
        """ Discover deployed dashboards
        
        :param refresh_overrides: a list of dashboard ids to refresh
        :param refresh: force refresh all dashboards
        """
        
        if refresh or self._dashboards is None:
            self._dashboards = {}
        else:
            for dashboard_id in refresh_overrides:
                if dashboard_id in self._dashboards:
                    del self._dashboards[dashboard_id]
        
        logger.info('Discovering deployed dashboards')
        deployed_dashboards=self.list_dashboards()
        logger.info(f'Found {len(deployed_dashboards)} deployed dashboards')
        logger.debug(deployed_dashboards)
        bar = tqdm(deployed_dashboards, desc='Discovering Dashboards', leave=False)
        for dashboard in bar:
            # Discover found dashboards
            dashboard_name = dashboard.get('Name')
            dashboard_id = dashboard.get('DashboardId')
            bar.set_description(f'Discovering {dashboard_name[:10]:<10}', refresh=True)
            logger.info(f'Discovering "{dashboard_name}"')
            
            refresh = dashboard_id in refresh_overrides
            
            self.discover_dashboard(dashboard_id, refresh=refresh)

    def list_dashboards(self) -> list:
        parameters = {
            'AwsAccountId': self.account_id
        }
        try:
            result = self.client.list_dashboards(**parameters)
            if result.get('Status') != 200:
                raise CidCritical(f'list_dashboards returns: {result}')
            else:
                logger.debug(result)
                return result.get('DashboardSummaryList')
        except Exception as exc:
            logger.debug(exc, exc_info=True)
            return []

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
        except Exception as exc:
            logger.debug(exc, exc_info=True)
            return list()

    def clear_dashboard_selection (self):
        """ Clears the current dashboard selection. """
        unset_parameter('dashboard-id')

    def select_dashboard(self, force=False) -> str:
        """ Select from a list of discovered dashboards """
        dashboard_id = get_parameters().get('dashboard-id')
        if dashboard_id:
            return dashboard_id

        if not self.dashboards:
            return None
        choices = {}
        for dashboard in self.dashboards.values():
            health = '' if dashboard.health else ' UNHEALTHY'
            status = '' if dashboard.status == 'up to date' else ' ' + dashboard.status.upper()
            key = f'{dashboard.name} ({dashboard.arn.split("/")[-1]}){health}{status}'
            notice = dashboard.definition.get('deprecationNotice', '')
            if notice:
                key = f'{key} {notice}'
            if ((dashboard.latest or not dashboard.health or notice) and not force):
                choices[key] = None
            else:
                choices[key] = dashboard.id

        try:
            dashboard_id = get_parameter(
                param_name='dashboard-id',
                message="Please select dashboard from the list",
                choices=choices,
                none_as_disabled=True,
            )
        except AttributeError as exc:
            # No updatable dashboards (selection is disabled)
            logger.debug(exc, exc_info=True)
        except Exception as exc:
            logger.exception(exc)
        finally:
            return dashboard_id

    def select_user(self):
        """ Select a user from the list of users """
        all_users = []
        next_token = None
        try:
            while True:
                if next_token:
                    response = self.identityClient.list_users(AwsAccountId=self.account_id, Namespace='default', NextToken=next_token)
                else:
                    response = self.identityClient.list_users(AwsAccountId=self.account_id, Namespace='default')

                user_list = response.get('UserList', [])
                all_users.extend(user_list)

                next_token = response.get('NextToken')
                if not next_token:
                    break

            # Sort the users by UserName
            user_list = sorted(all_users, key=lambda x: x.get('UserName'))

        except self.client.exceptions.AccessDeniedException as exc:
            raise CidCritical('AccessDenied for listing users, your can explicitly provide --quicksight-user parameter') from exc

        user_name = get_parameter(
            param_name='quicksight-user',
            message="Please select QuickSight user to use",
            choices={f"{user.get('UserName')} ({user.get('Email')}, {user.get('Role')})":user.get('UserName') for user in user_list}
        )
        for user in user_list:
            if user.get('UserName') == user_name:
                return user

    def select_group(self):
        """ Select a group from the list of groups """
        try:
            groups = self.identityClient.list_groups(AwsAccountId=self.account_id, Namespace='default').get('GroupList')
        except self.client.exceptions.AccessDeniedException as exc:
            raise CidCritical('AccessDenied for listing groups, your can explicitly provide --quicksight-group parameter') from exc

        group_name = get_parameter(
            param_name='quicksight-group',
            message="Please select QuickSight Group to use",
            choices={f"{group.get('GroupName')} ({group.get('Description')})":group.get('GroupName') for group in groups}
        )
        for group in groups:
            if group.get('GroupName') == group_name:
                return group

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
        except Exception as exc:
            logger.debug(exc, exc_info=True)
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
                logger.debug(f"Folder_list: {result.get('FolderSummaryList')}")
                return result.get('FolderSummaryList')
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied listing folders')
            raise
        except Exception as exc:
            logger.debug(exc, exc_info=True)
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
        except Exception as exc:
            logger.debug(exc, exc_info=True)
            return None


    def select_folder(self):
        """ Select a folder from the list of folders """
        try:
            folder_list = self.list_folders()
            if not folder_list:
                return None
        except self.client.exceptions.AccessDeniedException:
            logger.error('AccessDeniedException on listing folders')
            raise

        _folder = get_parameter(
            param_name='folder-id',
            message="Please select QuickSight folder to use",
            choices={f"{folder.get('Name')} ({folder.get('FolderId')})":folder for folder in folder_list}
        )
        return _folder


    def describe_dashboard(self, poll: bool=False, **kwargs) -> Union[None, Dashboard]:
        """ Describes an Amazon QuickSight dashboard
        Keyword arguments:
            DashboardId
            poll_interval
        """
        poll_interval = kwargs.get('poll_interval', 5)
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
                try:
                    response = self.client.describe_dashboard(AwsAccountId=self.account_id, **kwargs).get('Dashboard')
                except self.client.exceptions.ThrottlingException:
                    logger.debug('Got ThrottlingException will sleep for 5 sec')
                    time.sleep(5)
                    continue
                logger.debug(response)
                dashboard = Dashboard(response, qs=self)
                current_status = dashboard.version.get('Status')
                if not poll:
                    break
            logger.info(f'Dashboard {dashboard.name} status is {current_status}')
            return dashboard
        except self.client.exceptions.ResourceNotFoundException:
            return None
        except self.client.exceptions.UnsupportedUserEditionException as exc:
            raise CidCritical('Error: Amazon QuickSight Enterprise Edition is required') from exc
        except Exception as exc:
            logger.error(f'Error in describe_dashboard: {exc}')
            raise
    
    # Create a method to retrieve the definition for a given dashboard
    def describe_dashboard_definition(self, dashboard_id: str, refresh: bool = False) -> CidQsDefinition:
        """ Describes an Amazon QuickSight dashboard definition """
        if refresh or not self._definitions.get(f'{self.account_id}:{self.identityRegion}:{dashboard_id}'):
            try:
                parameters = {
                    'AwsAccountId': self.account_id,
                    'DashboardId': dashboard_id
                }
                result = self.client.describe_dashboard_definition(**parameters)
                self._definitions.update({f'{self.account_id}:{self.identityRegion}:{dashboard_id}': CidQsDefinition(result.get('Definition'))})
                logger.debug(result)
            except self.client.exceptions.UnsupportedUserEditionException as exc:
                raise CidCritical('Amazon QuickSight Enterprise Edition is required') from exc
            except self.client.exceptions.ResourceNotFoundException as exc:
                raise CidError(f'Error: Definition for dashboard with ID {dashboard_id} is not available in account {self.account_id} and region {self.identityRegion}') from exc
            except Exception as exc:
                logger.debug(exc, exc_info=True)
                raise CidError(f'Error: {exc} - Cannot find definition for dashboard with ID {dashboard_id} in account {self.account_id}.') from exc
        return self._definitions.get(f'{self.account_id}:{self.identityRegion}:{dashboard_id}')

    def delete_dashboard(self, dashboard_id):
        """ Deletes an Amazon QuickSight dashboard """
        params = {
            'AwsAccountId': self.account_id,
            'DashboardId': dashboard_id
        }
        logger.info(f'Deleting dashboard {dashboard_id}')
        result = self.client.delete_dashboard(**params)
        del self._dashboards[dashboard_id]
        return result

    def delete_data_source(self, datasource_id):
        """ Deletes an Amazon QuickSight dashboard """
        params = {
            'AwsAccountId': self.account_id,
            'DataSourceId': datasource_id
        }
        logger.info(f'Deleting DataSource {datasource_id}')
        try:
            result = self.client.delete_data_source(**params)
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f'Deleting DataSource {datasource_id} not needed as it is does not exist')
            result = True
        if datasource_id in (self._datasources or []):
            del self._datasources[datasource_id]
        return result

    def delete_dataset(self, id: str) -> bool:
        """ Deletes an Amazon QuickSight dataset """

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


    def get_datasources(self, id: str=None, name: str=None, type: str=None, athena_role_arn: str=None, athena_workgroup_name: str=None, healthy: bool=True) -> List[Datasource]:
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
            if athena_role_arn is not None and datasource.AthenaParameters.get('RoleArn') != athena_role_arn:
                continue
            result.append(datasource)
        return result


    def describe_dataset(self, id, timeout: int=1) -> Dataset:
        """ Describes an Amazon QuickSight dataset """
        if self._datasets and id in self._datasets:
            return self._datasets.get(id)
        self._datasets = self._datasets or {}
        poll_interval = 1
        _dataset = None
        deadline = time.time() + timeout
        while time.time() <= deadline:
            try:
                _dataset = Dataset(self.client.describe_data_set(AwsAccountId=self.account_id, DataSetId=id).get('DataSet'))
                logger.info(f'Saving dataset details "{_dataset.name}" ({_dataset.id})')
                self._datasets[_dataset.id] = _dataset
                break
            except self.client.exceptions.ResourceNotFoundException:
                logger.info(f'DataSetId {id} not found')
                time.sleep(poll_interval)
                continue
            except self.client.exceptions.AccessDeniedException:
                logger.debug(f'No quicksight:DescribeDataSet permission or missing DataSetId {id}')
                return None
            except self.client.exceptions.ClientError as exc:
                logger.error(f'Error when trying to describe dataset {id}: {exc}')
                return None

        return self._datasets.get(id, None)

    def get_dataset_last_ingestion(self, dataset_id) -> str:
        """returns human friendly status of the latest ingestion"""
        try:
            ingestions = self.client.list_ingestions(
                DataSetId=dataset_id,
                AwsAccountId=self.account_id,
            ).get('Ingestions', [])
        except self.client.exceptions.ResourceNotFoundException:
            return '<RED>NotFound<END>'
        except self.client.exceptions.AccessDeniedException:
            return '<YELLOW>AccessDenied<END>'
        if not ingestions:
            return None
        last_ingestion = ingestions[0] # Suppose it is the latest
        status = last_ingestion.get('IngestionStatus')
        time_ago = ago(last_ingestion.get('CreatedTime'))
        if last_ingestion.get('ErrorInfo', {}).get('Type') == "DATA_SET_NOT_SPICE":
            return '<BLUE>DIRECT_QUERY<END>'
        if status in ('COMPLETED',):
            status = f'<GREEN>{status}<END>'
            time_in_mins = int(int(last_ingestion.get('IngestionTimeInSeconds', 0) or 0) / 60)
            return f"{status} ({time_in_mins} mins, {last_ingestion['RowInfo']['RowsIngested']} rows) {time_ago}"
        if status in ('FAILED', 'CANCELLED'):
            status = f'<RED>{status}<END>'
            return f"{status} ({last_ingestion['ErrorInfo']['Type']} {last_ingestion['ErrorInfo']['Message']}) {time_ago}"
        return f'{status} {time_ago}'

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
                except Exception as exc:
                    logger.debug(exc, exc_info=True)
                    continue
        except self.client.exceptions.AccessDeniedException:
            logger.info('Access denied listing datasets')
        except Exception as exc:
            logger.debug(exc, exc_info=True)
            logger.info('No datasets found')

    def refresh_dataset(self, dataset_id):
        """ Refresh the dataset """

        logger.info(f'Starting refresh for dataset: {dataset_id}')
        status = 'FAILED'
        try:
            response = self.client.describe_data_set(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id)
            mode = response.get('DataSet').get('ImportMode')
            if mode == 'DIRECT_QUERY':
                return mode, 'DIRECT'
            response = self.client.create_ingestion(
                DataSetId=dataset_id,
                IngestionId=datetime.datetime.now().strftime("%d%m%y-%H%M%S-%f"),
                AwsAccountId=self.account_id)
            status = response.get('IngestionStatus')
        except self.client.exceptions.AccessDeniedException:
            logger.error(f'Access denied refreshing dataset: {dataset_id}')
        except Exception as exc:
            logger.debug(exc, exc_info=True)
            raise CidError(f'Unable to list refresh dataset {dataset_id}: {str(exc)}') from exc
        return mode, status

    def describe_data_source(self, id: str, update: bool=False) -> Datasource:
        """ Describes an Amazon QuickSight DataSource """
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
        except Exception as exc:
            logger.info(exc)
            logger.debug(exc, exc_info=True)
            return None
        else:
            return _datasource


    def describe_template(self, template_id: str, version_number: int=None, account_id: str=None, region: str='us-east-1') -> CidQsTemplate:
        """ Describes an Amazon QuickSight template """
        if not account_id:
            account_id=self.cidAccountId
        if not self._templates.get(f'{account_id}:{region}:{template_id}:{version_number}'):
            try:
                client = self.session.client('quicksight', region_name=region)
                parameters = {
                    'AwsAccountId': account_id,
                    'TemplateId': template_id
                }
                if version_number:
                    parameters.update({'VersionNumber': version_number})
                result = client.describe_template(**parameters)
                self._templates.update({f'{account_id}:{region}:{template_id}:{version_number}': CidQsTemplate(result.get('Template'))})
                logger.debug(result)
            except self.client.exceptions.UnsupportedUserEditionException as exc:
                raise CidCritical('Amazon QuickSight Enterprise Edition is required') from exc
            except self.client.exceptions.ResourceNotFoundException as exc:
                raise CidError(f'Error: Template {template_id} is not available in account {account_id} and region {region}') from exc
            except Exception as exc:
                logger.debug(exc, exc_info=True)
                raise CidError(f'Error: {exc} - Cannot find {template_id} in account {account_id}.') from exc
        return self._templates.get(f'{account_id}:{region}:{template_id}:{version_number}')

    def describe_user(self, username: str) -> dict:
        """ Describes an Amazon QuickSight user """
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
        """ Describes an Amazon QuickSight Group """
        try:
            result = self.identityClient.describe_group(**{
                'AwsAccountId': self.account_id,
                'GroupName': groupname,
                'Namespace': 'default'
            })
            logger.debug('group = %s', json.dumps(result))
            return result.get('Group')
        except self.client.exceptions.ResourceNotFoundException:
            logger.error(f'QuickSight group {groupname} not found.')
            return None
        except self.client.exceptions.AccessDeniedException:
            logger.error('AccessDeniedException when trying to DescribeGroup in QuickSight.')
            return None


    def create_dataset(self, definition: dict) -> str:
        """ Creates an Amazon QuickSight dataset """
        poll_interval = 1
        max_timeout = 60
        columns_tpl = {
            'PrincipalArn': self.get_principal_arn()
        }
        data_set_permissions_tpl = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name='data/permissions/data_set_permissions.json',
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
        except self.client.exceptions.LimitExceededException as exc:
            logger.error(exc)
            raise CidCritical(f'Not enough Amazon QuickSight SPICE capacity in {self.region}. Add SPICE here https://quicksight.aws.amazon.com/sn/admin#capacity .') from exc

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


    def update_dataset(self, definition: dict) -> Dataset:
        """ Update an Amazon QuickSight dataset """
        definition.update({'AwsAccountId': self.account_id})
        logger.info(f'Updating dataset {definition.get("Name")}')

        if "Permissions" in definition:
            logger.info('Ignoring permissions for dataset update.')
            del definition['Permissions']
        response = self.client.update_data_set(**definition)
        logger.info(f'Dataset {definition.get("Name")} is updated')
        dataset_id = definition.get('DataSetId')
        self.datasets.pop(dataset_id, None) # invalidate cache
        return self.describe_dataset(dataset_id)


    def get_dataset_refresh_schedules(self, dataset_id):
        """Returns refresh schedules for given dataset id"""
        try:
            refresh_schedules = self.client.list_refresh_schedules(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id
            )
            return refresh_schedules.get("RefreshSchedules")
        except self.client.exceptions.ResourceNotFoundException as exc:
            raise CidError(f'DataSet {dataset_id} does not exist') from exc
        except self.client.exceptions.AccessDeniedException as exc:
            raise CidError('AccessDenied on ListRefreshSchedules') from exc
        except Exception as exc:
            raise CidError(f'Unable to list refresh schedules for dataset {dataset_id}: {str(exc)}') from exc


    def ensure_dataset_refresh_schedule(self, dataset_id, schedules: list):
        """ Ensures that dataset has scheduled refresh """
        # get all existing schedules for the given dataset
        try:
            existing_schedules = self.get_dataset_refresh_schedules(dataset_id)
        except CidError as exc:
            # We cannot access schedules, but let's check if there are scheduled ingestions. 
            ingestions_exist = False
            try:
                ingestions_exist = list(
                    self.client.get_paginator('list_ingestions').paginate(
                        DataSetId=dataset_id,
                        AwsAccountId=self.account_id
                    ).search("Ingestions[?RequestSource=='SCHEDULED']")
                )
            except Exception:
                logger.debug(f'List refresh schedule throws: {exc}')
                logger.warning(
                    f'Cannot read dataset schedules for dataset = {dataset_id}. {str(exc)}. Skipping schedule management.'
                    ' Please make sure scheduled refresh is configured manually.'
                )
                return
            if ingestions_exist:
                logger.debug(f'We cannot read schedules but there are ingestions. Skipping creation of schedule.')
                return
            logger.debug(f'We cannot read schedules but there no ingestions. Continue to creation of schedule.')
            existing_schedules = []

        if schedules:
            if exec_env()['terminal'] in ('lambda'):
                schedule_frequency_timezone = get_parameters().get("timezone", timezone.get_default_timezone())
            else:
                default_timezone = timezone.get_default_timezone()
                schedule_frequency_timezone = get_parameter("timezone",
                    message='Please select timezone for datasets scheduled refresh.',
                    choices=sorted(list(set(timezone.get_all_timezones() + [default_timezone]))),
                    default=default_timezone
                )
            if not schedule_frequency_timezone:
                logger.warning('Cannot get timezone. Please provide --timezone parameter. Please make sure scheduled refresh is configured manually.')
                return

        for schedule in schedules:

            # Get the list of existing schedules with the same id
            existing_schedule = None
            for existing in existing_schedules:
                if schedule["ScheduleId"] == existing["ScheduleId"]:
                    existing_schedule = existing
                    break

            # Verify that all schedule parameters are set
            schedule["ScheduleId"] = schedule.get("ScheduleId", "cid")
            if "ScheduleFrequency" not in schedule:
                schedule["ScheduleFrequency"] = {}
            schedule["ScheduleFrequency"]["Timezone"] = schedule_frequency_timezone
            try:
                schedule["ScheduleFrequency"]["TimeOfTheDay"] = randtime.get_random_time_from_range(
                    self.account_id + dataset_id,
                    schedule["ScheduleFrequency"].get("TimeOfTheDay", "")
                )
            except Exception as exc:
                logger.error(
                    f'Invalid timerange for schedule with id "{schedule["ScheduleId"]}"'
                    f' and dataset {dataset_id}: {str(exc)} ... skipping.'
                    f' Please create dataset refresh schedule manually.'
                )
                continue
            schedule["ScheduleFrequency"]["Interval"] = schedule["ScheduleFrequency"].get("Interval", "DAILY")
            schedule["RefreshType"] = schedule.get("RefreshType", "FULL_REFRESH")
            if "providedBy" in schedule:
                del schedule["providedBy"]

            if not existing_schedule:
                # Avoid adding a new schedule  when customer already has put a schedule manually as this can lead to additional charges.
                schedules_with_different_id = [existing for existing in existing_schedules if schedule["ScheduleId"] != existing["ScheduleId"] ]
                if schedules_with_different_id:
                    logger.info(
                        f'Found the same schedule {schedule.get("RefreshType")} / {schedule["ScheduleFrequency"].get("Interval")}'
                        f' but with different id. Skipping to avoid duplication. Please delete all manually created schedules for dataset {dataset_id}'
                    )
                    continue
                logger.debug(f'Creating refresh schedule with id {schedule["ScheduleId"]} for dataset {dataset_id}.')
                try:
                    self.client.create_refresh_schedule(
                        DataSetId=dataset_id,
                        AwsAccountId=self.account_id,
                        Schedule=schedule
                    )
                    logger.debug(f'Refresh schedule with id {schedule["ScheduleId"]} for dataset {dataset_id} is created.')
                except self.client.exceptions.ResourceNotFoundException:
                    logger.error(f'Unable to create refresh schedule with id {schedule["ScheduleId"]}. Dataset {dataset_id} does not exist.')
                except self.client.exceptions.AccessDeniedException:
                    logger.error(f'Unable to create refresh schedule with id {schedule["ScheduleId"]}. Please add quicksight:CreateDataSet permission.')
                except self.client.exceptions.ResourceExistsException:
                    logger.info(f'Schedule with id {schedule["ScheduleId"]} exists. But can have other settings. You better check.')
                except Exception as exc:
                    logger.error(f'Unable to create refresh schedule with id {schedule["ScheduleId"]} for dataset "{dataset_id}": {str(exc)}')
            else:
                # schedule exists so we need to update
                logger.debug(f'Updating refresh schedule with id {schedule["ScheduleId"]} for dataset {dataset_id}.')
                try:
                    self.client.update_refresh_schedule(
                        DataSetId=dataset_id,
                        AwsAccountId=self.account_id,
                        Schedule=schedule
                    )
                    logger.debug(f'Refresh schedule with id {schedule["ScheduleId"]} for dataset {dataset_id} is updated.')
                except self.client.exceptions.ResourceNotFoundException:
                    logger.error(f'Unable to update refresh schedule with id {schedule["ScheduleId"]}. Dataset {dataset_id} does not exist.')
                except self.client.exceptions.AccessDeniedException:
                    logger.error(f'Unable to update refresh schedule with id {schedule["ScheduleId"]}. Please add quicksight:UpdqteDataSet permission.')
                except Exception as exc:
                    logger.error(f'Unable to update refresh schedule with id {schedule["ScheduleId"]} for dataset "{dataset_id}": {str(exc)}')

        # Verify if there is at least one schedule and warn user if not
        try:
            if not self.get_dataset_refresh_schedules(dataset_id):
                logger.warning(f'There is no refresh schedule for dataset "{dataset_id}". Please create a refresh schedule manually.' )
        except CidError:
            pass

    def create_dashboard(self, definition: dict) -> Dashboard:
        """ Creates an Amazon QuickSight dashboard """

        create_parameters = self._build_params_for_create_update_dash(definition)

        dashboard_permissions_tpl = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name='data/permissions/dashboard_permissions.json',
        ).decode('utf-8'))
        columns_tpl = {
            'PrincipalArn': self.get_principal_arn()
        }
        dashboard_permissions = json.loads(dashboard_permissions_tpl.safe_substitute(columns_tpl))
        create_parameters['Permissions'] = [ dashboard_permissions ]

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


    def _build_params_for_create_update_dash(self, definition: dict, permissions: bool=True) -> Dict:

        create_parameters = {
            'AwsAccountId': self.account_id,
            'DashboardId': definition.get('dashboardId'),
            'Name': definition.get('name'),
            'ValidationStrategy': {'Mode': 'LENIENT'},
        }
        theme = get_parameters().get('theme') or definition.get('theme')
        if theme:
            if not theme.startswith('arn:'):
                theme_arn = f'arn:{self.partition}:quicksight::aws:theme/' + theme
            else:
                raise NotImplementedError('Only standard themes are supported now.')
            create_parameters['ThemeArn'] = theme_arn

        if definition.get('sourceTemplate'):
            dataset_references = [
                {'DataSetPlaceholder': key, 'DataSetArn': value}
                for key, value in definition.get('datasets', {}).items()
            ]
            create_parameters['SourceEntity'] = {
                'SourceTemplate': {
                    'Arn': f"{definition.get('sourceTemplate').arn}/version/{definition.get('sourceTemplate').version}",
                    'DataSetReferences': dataset_references
                }
            }
        elif definition.get('definition'):
            create_parameters['Definition'] = definition.get('definition')
            dataset_references = []
            for identifier, arn in definition.get('datasets', {}).items():
                # Fetch dataset by name (preferably) OR by id
                dataset_declarations = create_parameters['Definition'].get('DataSetIdentifierDeclarations', [])
                for ds_dec in dataset_declarations:
                    if identifier == ds_dec['Identifier']:
                        logger.debug(f'Dataset {identifier} matched by Name')
                        break # all good
                    elif arn.split('/')[-1] == ds_dec['DataSetArn'].split('/')[-1]:
                        logger.debug(f'Dataset {identifier} matched by Id')
                        identifier = ds_dec['Identifier']
                        break
                else:
                    raise CidCritical(f'Unable to match dataset {identifier} / {arn} with any DataSetIdentifierDeclarations of dashboard {repr(dataset_declarations)}')

                dataset_references.append({'Identifier': identifier, 'DataSetArn': arn})

            create_parameters['SourceEntity'] = {}
            create_parameters['Definition']['DataSetIdentifierDeclarations'] = dataset_references
        else:
            logger.debug(f'Definition = {definition}')
            raise CidCritical('Dashboard definition must contain sourceTemplate or definition')
        return create_parameters

    def update_dashboard(self, dashboard: Dashboard, definition):
        """ Updates an Amazon QuickSight dashboard """
        update_parameters = self._build_params_for_create_update_dash(definition)
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
        """ Updates an Amazon QuickSight dashboard permissions """
        logger.debug(f"Updating Dashboard permissions: {update_parameters}")
        update_parameters.update({'AwsAccountId': self.account_id})
        update_status = self.client.update_dashboard_permissions(**update_parameters)
        logger.debug(update_status)
        return update_status


    def update_data_set_permissions(self, **update_parameters):
        """ Updates an Amazon QuickSight dataset permissions """
        logger.debug(f"Updating DataSet permissions: {update_parameters}")
        update_parameters.update({'AwsAccountId': self.account_id})
        update_status = self.client.update_data_set_permissions(**update_parameters)
        logger.debug(update_status)
        return update_status


    def update_data_source_permissions(self, **update_parameters):
        """ Updates an Amazon QuickSight data source permissions """
        logger.debug(f"Updating DataSource permissions: {update_parameters}")
        update_parameters.update({'AwsAccountId': self.account_id})
        update_status = self.client.update_data_source_permissions(**update_parameters)
        logger.debug(update_status)
        return update_status


    def update_template_permissions(self, **update_parameters):
        """ Updates an Amazon QuickSight template permissions """
        logger.debug(f"Updating Template permissions: {update_parameters}")
        update_parameters.update({'AwsAccountId': self.account_id})
        update_status = self.client.update_template_permissions(**update_parameters)
        logger.debug(update_status)
        return update_status

    def get_dashboard_permissions(self, dashboard_id):
        """ get_dashboard_permissions """
        return self.client.describe_dashboard_permissions(AwsAccountId=self.account_id, DashboardId=dashboard_id)['Permissions']

    def dataset_diff(self, raw1, raw2):
        """ get dataset diff """
        return diff(
            Dataset(raw1).to_diffable_structure(),
            Dataset(raw2).to_diffable_structure(),
        )
