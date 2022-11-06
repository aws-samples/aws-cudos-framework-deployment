import os
import sys
import json
import logging
import functools
from pathlib import Path
from string import Template
from typing import Dict
from pkg_resources import resource_string

if sys.version_info < (3, 8):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

import yaml
import click
import requests
from deepmerge import always_merger
from botocore.exceptions import ClientError, NoCredentialsError, CredentialRetrievalError


from cid import utils
from cid.base import CidBase
from cid.plugin import Plugin
from cid.utils import get_parameter, get_parameters, set_parameters, unset_parameter, get_yesno_parameter
from cid.helpers.account_map import AccountMap
from cid.helpers import Athena, CUR, Glue, QuickSight, Dashboard, Dataset, Datasource, Template as CidQsTemplate
from cid._version import __version__
from cid.export import export_analysis
from cid.logger import set_cid_logger
from cid.exceptions import CidError, CidCritical

logger = logging.getLogger(__name__)

class Cid():

    def __init__(self, **kwargs) -> None:
        self.base: CidBase = None
        # Defined resources
        self.resources = dict()
        self.dashboards = dict()
        self.plugins = self.__loadPlugins()
        self._clients = dict()
        self._visited_views = [] # Views updated in the current session
        self.qs_url = 'https://{region}.quicksight.aws.amazon.com/sn/dashboards/{dashboard_id}'
        self.all_yes = kwargs.get('yes')
        self.verbose = kwargs.get('verbose')
        set_parameters(kwargs, self.all_yes)
        self._logger = None

    def aws_login(self):
        params = {
            'profile_name': None,
            'region_name': None,
            'aws_access_key_id': None,
            'aws_secret_access_key': None,
            'aws_session_token': None
        }
        for key in params.keys():
            value = get_parameters().get(key.replace('_', '-'))
            if  value != None:
                params[key] = value

        print('Checking AWS environment...')
        try:
            self.base = CidBase(session=utils.get_boto_session(**params))
            if self.base.session.profile_name:
                print(f'\tprofile name: {self.base.session.profile_name}')
                logger.info(f'AWS profile name: {self.base.session.profile_name}')
            self.qs_url_params = {
                'account_id': self.base.account_id,
                'region': self.base.session.region_name
            }
        except (NoCredentialsError, CredentialRetrievalError):
            raise CidCritical('Error: Not authenticated, please check AWS credentials')
        except ClientError as e:
            raise CidCritical(f'ClientError: {e}')
        print(f'\taccountId: {self.base.account_id}\n\tAWS userId: {self.base.username}')
        logger.info(f'AWS accountId: {self.base.account_id}')
        logger.info(f'AWS userId: {self.base.username}')
        print('\tRegion: {}'.format(self.base.session.region_name))
        logger.info(f'AWS region: {self.base.session.region_name}')
        print('\n')

    @property
    def qs(self) -> QuickSight:
        if not self._clients.get('quicksight'):
            self._clients.update({
                'quicksight': QuickSight(self.base.session, resources=self.resources)
            })
        return self._clients.get('quicksight')

    @property
    def athena(self) -> Athena:
        if not self._clients.get('athena'):
            self._clients.update({
                'athena': Athena(self.base.session, resources=self.resources)
            })
        return self._clients.get('athena')

    @property
    def glue(self) -> Glue:
        if not self._clients.get('glue'):
            self._clients.update({
                'glue': Glue(self.base.session)
            })
        return self._clients.get('glue')

    @property
    def cur(self) -> CUR:
        if not self._clients.get('cur'):
            _cur = CUR(self.base.session)
            _cur.athena = self.athena
            print('Checking if CUR is enabled and available...')

            if not _cur.configured:
                raise ClientError("Error: please ensure CUR is enabled, if yes allow it some time to propagate")

            print(f'\tAthena table: {_cur.tableName}')
            print(f"\tResource IDs: {'yes' if _cur.hasResourceIDs else 'no'}")
            if not _cur.hasResourceIDs:
                raise ClientError("Error: CUR has to be created with Resource IDs")
            print(f"\tSavingsPlans: {'yes' if _cur.hasSavingsPlans else 'no'}")
            print(f"\tReserved Instances: {'yes' if _cur.hasReservations else 'no'}")
            print('\n')
            self._clients.update({
                'cur': _cur
            })
        return self._clients.get('cur')

    @property
    def accountMap(self) -> AccountMap:
        if not self._clients.get('accountMap'):
            _account_map = AccountMap(self.base.session)
            _account_map.athena = self.athena
            _account_map.cur = self.cur

            self._clients.update({
                'accountMap': _account_map
            })
        return self._clients.get('accountMap')

    def command(func):
        ''' a decorator that ensure that we logged in to AWS acc, and loaded additional resource files
        '''
        @functools.wraps(func)
        def wrap(self, *args, **kwargs):
            self.all_yes = self.all_yes or kwargs.get('yes') # Flag params need special treatment
            if kwargs.get('verbose'): # Count params need special treatment
                self.verbose = self.verbose + kwargs.get('verbose')
            set_parameters(kwargs, all_yes=self.all_yes)
            logger.debug(json.dumps(get_parameters()))
            if not self._logger:
                self._logger = set_cid_logger(
                    verbosity=self.verbose,
                    log_filename=get_parameters().get('log_filename', 'cid.log')
                )
                logger.info(f'Initializing CID {__version__} for {func.__name__}')
            if not self.base:
                self.aws_login()
            self.load_resources()
            return func(self, *args, **kwargs)
        return wrap

    def __loadPlugins(self) -> dict:
        try:
            _entry_points = entry_points().get('cid.plugins')
        except: # fallback for python version more than 3.7.x AND still less then 3.8
            _entry_points = [ep for ep in entry_points() if ep.group == 'cid.plugins']

        plugins = dict()
        print('Loading plugins...')
        logger.info(f'Located {len(_entry_points)} plugin(s)')
        for ep in _entry_points:
            if ep.value in plugins.keys():
                logger.info(f'Plugin {ep.value} already loaded, skipping')
                continue
            logger.info(f'Loading plugin: {ep.name} ({ep.value})')
            plugin = Plugin(ep.value)
            print(f"\t{ep.name} loaded")
            plugins.update({ep.value: plugin})
            try:
                self.resources = always_merger.merge(
                    self.resources, plugin.provides())
            except AttributeError:
                pass
        print('\n')
        logger.info('Finished loading plugins')
        return plugins

    def getPlugin(self, plugin) -> dict:
        return self.plugins.get(plugin)


    def get_definition(self, type: str, name: str=None, id: str=None) -> dict:
        """ return resource definition that matches parameters """
        if type not in ['dashboard', 'dataset', 'view']:
            print(f'Error: {type} is not a valid type')
            raise ValueError(f'{type} is not a valid definition type')
        if type in  ['dataset', 'view'] and name:
            return self.resources.get(f'{type}s').get(name)
        elif type in ['dashboard']:
            for definition in self.resources.get(f'{type}s').values():
                if name is not None and definition.get('name') != name:
                    continue
                if id is not None and definition.get('dashboardId') != id:
                    continue
                return definition
        return None


    @command
    def export(self, **kwargs):
        export_analysis(self.qs)

    def track(self, action, dashboard_id):
        """ Send dashboard_id and account_id to adoption tracker """
        method = {'created':'PUT', 'updated':'PATCH', 'deleted': 'DELETE'}.get(action, None)
        if not method:
            logger.debug(f"This will not fail the deployment. Logging action {action} is not supported. This issue will be ignored")
            return
        endpoint = 'https://okakvoavfg.execute-api.eu-west-1.amazonaws.com/'
        payload = {
            'dashboard_id': dashboard_id,
            'account_id': self.base.account_id,
            action + '_via': 'Lambda' if os.environ.get('AWS_EXECUTION_ENV', '').startswith('AWS_Lambda') else 'CID',
        }
        try:
            res = requests.request(
                method=method,
                url=endpoint,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            if res.status_code != 200:
                logger.debug(f"This will not fail the deployment. There has been an issue logging action {action}  for dashboard {dashboard_id} and account {self.base.account_id}, server did not respond with a 200 response,actual  status: {res.status_code}, response data {res.text}. This issue will be ignored")
        except Exception as e:
            logger.debug(f"Issue logging action {action}  for dashboard {dashboard_id} , due to a urllib3 exception {str(e)} . This issue will be ignored")


    def load_resources(self):
        ''' load additional resources from command line parameters
        '''
        if get_parameters().get('resources'):
            fileneme = get_parameters().get('resources')
            with open(get_parameters().get('resources'), 'r', encoding='utf-8') as file:
                resources = yaml.safe_load(file)
            logging.info(f'Loaded resources from {fileneme}')
            self.resources = always_merger.merge(self.resources, resources)


    @command
    def deploy(self, dashboard_id: str=None, recursive=True, update=False, **kwargs):
        """ Deploy Dashboard Command"""
        self._deploy(dashboard_id, recursive, update, **kwargs)


    def _deploy(self, dashboard_id: str=None, recursive=True, update=False, **kwargs):
        """ Deploy Dashboard """

        self.qs.ensure_subscription()

        if dashboard_id is None:
            dashboard_id = get_parameter(
                param_name='dashboard-id',
                message="Please select dashboard to install",
                choices={
                   f"[{dashboard.get('dashboardId')}] {dashboard.get('name')}" : dashboard.get('dashboardId')
                   for k, dashboard in self.resources.get('dashboards').items()
                },
            )
        if not dashboard_id:
            print('No dashboard selected')
            return

        # Get selected dashboard definition
        dashboard_definition = self.get_definition("dashboard", id=dashboard_id)
        if not dashboard_definition:
            dashboard = self.qs.dashboards.get(dashboard_id)
            if isinstance(dashboard, Dashboard):
                dashboard_definition = dashboard.definition
            else:
                raise ValueError(f'Cannot find dashboard with id={dashboard_id} in resources file.')

        required_datasets = dashboard_definition.get('dependsOn', dict()).get('datasets', list())

        dashboard_datasets = self.qs.dashboards.get(dashboard_id).datasets if self.qs.dashboards.get(dashboard_id) else {}
        for name, id in dashboard_datasets.items():
            if id not in self.qs.datasets:
                logger.info(f'Removing unknown dataset "{name}" ({id}) from dashboard {dashboard_id}')
                del dashboard_datasets[name]

        if recursive:
            self.create_datasets(required_datasets, dashboard_datasets, recursive=recursive, update=update)

        # Get QuickSight template details
        source_template = self.qs.describe_template(
            template_id=dashboard_definition.get('templateId'),
            account_id=dashboard_definition.get('sourceAccountId'),
            region=dashboard_definition.get('region', 'us-east-1')
        )
        dashboard_definition.update({'sourceTemplate': source_template})
        print(f'\nLatest template: {source_template.arn}/version/{source_template.version}')

        # Prepare API parameters
        if not dashboard_definition.get('datasets'):
            dashboard_definition.update({'datasets': {}})
        for dataset_name in required_datasets:
            ds = next((v for v in self.qs.datasets.values() if v.name == dataset_name), None)
            if isinstance(ds, Dataset):
                dataset_fields = {col.get('Name'): col.get('Type') for col in ds.columns}
                required_fileds = {col.get('Name'): col.get('DataType') for col in source_template.datasets.get(dataset_name)}
                unmatched = {}
                for k,v in required_fileds.items():
                    if k not in dataset_fields or dataset_fields[k] != v:
                        unmatched.update({k: {'expected': v, 'found': dataset_fields.get(k)}})
                if unmatched:
                    raise CidCritical(f'Dataset "{dataset_name}" ({ds.id}) is missing required fields. {(unmatched)}')
                else:
                    print(f'Using dataset {dataset_name}: {ds.id}')
                    dashboard_definition.get('datasets').update({dataset_name: ds.arn})
  

        kwargs = dict()
        local_overrides = f'work/{self.base.account_id}/{dashboard_id}.json'
        logger.info(f'Looking for local overrides file "{local_overrides}"...')
        try:
            with open(local_overrides, 'r', encoding='utf-8') as r:
                try:
                    print('found')
                    if click.confirm(f'Use local overrides from {local_overrides}?'):
                        kwargs = json.load(r)
                        print('loaded')
                except Exception as e:
                    # Catch exception and dump a reason
                    click.echo('failed to load, dumping error message')
                    print(json.dumps(e, indent=4, sort_keys=True, default=str))
        except FileNotFoundError:
            logger.info('local overrides file not found')

        _url = self.qs_url.format(dashboard_id=dashboard_id, **self.qs_url_params)

        dashboard = self.qs.dashboards.get(dashboard_id)
        if isinstance(dashboard, Dashboard):
            if update:
                return self.update_dashboard(dashboard_id, **kwargs)
            else:
                print(f'Dashboard {dashboard_id} exists. See {_url}')
                return dashboard_id

        print(f'Deploying dashboard {dashboard_id}')
        try:
            dashboard = self.qs.create_dashboard(dashboard_definition, **kwargs)
            print(f"\n#######\n####### Congratulations!\n####### {dashboard_definition.get('name')} is available at: {_url}\n#######")
            self.track('created', dashboard_id)
        except self.qs.client.exceptions.ResourceExistsException:
            print('error, already exists')
            print(f"#######\n####### {dashboard_definition.get('name')} is available at: {_url}\n#######")
        except Exception as e:
            # Catch exception and dump a reason
            logger.debug(e, exc_info=True)
            print(f'failed with an error message: {e}')
            self.delete(dashboard_id)
            raise CidCritical(f'Deploy failed: {e}')

        if get_yesno_parameter(
                param_name=f'share-with-account',
                message=f'Share this dashboard with everyone in the account?',
                default='yes'):
            set_parameters({'share-method': 'account'})
            self.share(dashboard_id)

        return dashboard_id


    @command
    def open(self, dashboard_id, **kwargs):
        """Open QuickSight dashboard in browser"""

        aws_execution_env = os.environ.get('AWS_EXECUTION_ENV', '')
        if  aws_execution_env == 'CloudShell' or aws_execution_env.startswith('AWS_Lambda'):
            print(f"Operation is not supported in {aws_execution_env}")
            return dashboard_id
        if not dashboard_id:
            dashboard_id = self.qs.select_dashboard(force=True)
            dashboard = self.qs.dashboards.get(dashboard_id)
        else:
            # Describe dashboard by the ID given, no discovery
            dashboard = self.qs.describe_dashboard(DashboardId=dashboard_id)

        click.echo('Getting dashboard status...', nl=False)
        if dashboard is not None:
            if dashboard.version.get('Status') not in ['CREATION_SUCCESSFUL']:
                print(json.dumps(dashboard.version.get('Errors'),
                      indent=4, sort_keys=True, default=str))
                click.echo(
                    f'\nDashboard is unhealthy, please check errors above.')
            click.echo('healthy, opening...')
            click.launch(self.qs_url.format(dashboard_id=dashboard_id, **self.qs_url_params))
        else:
            click.echo('not deployed.')
        
        return dashboard_id

    @command
    def status(self, dashboard_id, **kwargs):
        """Check QuickSight dashboard status"""

        if not dashboard_id:
            if not self.qs.dashboards:
                print('No deployed dashboards found')
                return
            dashboard_id = self.qs.select_dashboard(force=True)
            if not dashboard_id:
                print('No dashboard selected')
                return
            dashboard = self.qs.dashboards.get(dashboard_id)
        else:
            # Describe dashboard by the ID given, no discovery
            self.qs.discover_dashboard(dashboardId=dashboard_id)
            dashboard = self.qs.describe_dashboard(DashboardId=dashboard_id)

        if dashboard is not None:
            dashboard.display_status()
            dashboard.display_url(self.qs_url, **self.qs_url_params)
        else:
            click.echo('not deployed.')

    @command
    def delete(self, dashboard_id, **kwargs):
        """Delete QuickSight dashboard"""

        if not dashboard_id:
            if not self.qs.dashboards:
                print('No deployed dashboards')
                return
            dashboard_id = self.qs.select_dashboard(force=True)
            if not dashboard_id:
                return

        if self.qs.dashboards and dashboard_id in self.qs.dashboards:
            datasets = self.qs.dashboards.get(dashboard_id).datasets # save for later
        else:
            dashboard_definition = self.get_definition("dashboard", id=dashboard_id)
            datasets = {d: None for d in (dashboard_definition or {}).get('dependsOn', {}).get('datasets', [])}

        try:
            # Execute query
            click.echo('Deleting dashboard...', nl=False)
            self.qs.delete_dashboard(dashboard_id=dashboard_id)
            print(f'Dashboard {dashboard_id} deleted')
            self.track('deleted', dashboard_id)
        except self.qs.client.exceptions.ResourceNotFoundException:
            print('not found')
        except Exception as e:
            # Catch exception and dump a reason
            logger.debug(e, exc_info=True)
            print(f'failed with an error message: {e}')
            return dashboard_id

        print('Processing dependencies')
        for dataset_name, dataset_id in datasets.items():
            self.delete_dataset(name=dataset_name, id=dataset_id)

        return dashboard_id

    def delete_dataset(self, name: str, id: str=None):
        if name not in self.resources['datasets']:
            logger.info(f'Dataset {name} is not managed by CID. Skipping.')
            print(f'Dataset {name} is not managed by CID. Skipping.')
            return False
        for dataset in list(self.qs._datasets.values()) if self.qs._datasets else []:
            if dataset.id == id or dataset.name == name:
                # Check if dataset is used in some other dashboard
                for dashboard in (self.qs.dashboards or {}).values():
                    if dataset.id in dashboard.datasets.values():
                        logger.info(f'Dataset {dataset.name} ({dataset.id}) is still used by dashboard "{dashboard.id}". Skipping.')
                        print      (f'Dataset {dataset.name} ({dataset.id}) is still used by dashboard "{dashboard.id}". Skipping.')
                        return False
                else: #not used

                    # try to get the database name from the dataset (might need this for later)
                    schema = next(iter(dataset.schemas), None) # FIXME: manage choice if multiple data sources
                    if schema:
                        self.athena.DatabaseName = schema

                    if get_parameter(
                        param_name=f'confirm-{dataset.name}',
                        message=f'Delete QuickSight Dataset {dataset.name}?',
                        choices=['yes', 'no'],
                        default='no') == 'yes':
                        print(f'Deleting dataset {dataset.name} ({dataset.id})')
                        self.qs.delete_dataset(dataset.id)
                    else:
                        logger.info(f'Skipping dataset {dataset.name}')
                        print      (f'Skipping dataset {dataset.name}')
                        return False
                if not dataset.datasources:
                    continue
                datasources = dataset.datasources
                athena_datasource = self.qs.datasources.get(datasources[0])
                if athena_datasource:
                    self.athena.WorkGroup = athena_datasource.AthenaParameters.get('WorkGroup')
                    break
                logger.debug(f'Cannot find QuickSight DataSource {datasources[0]}. So cannot define Athena WorkGroup')
                continue
        else:
            logger.info(f'Dataset not found for deletion: {name} ({id})')
        for view_name in list(set(self.resources['datasets'][name].get('dependsOn', {}).get('views', []))):
            self.delete_view(view_name)
        return True

    def delete_view(self, view_name):
        if view_name not in self.resources['views']:
            logger.info(f'View {view_name} is not managed by CID. Skipping.')
            return False
        logger.info(f'Deleting view "{view_name}"')
        definition = self.get_definition("view", name=view_name)
        if not definition:
            logger.info(f'Definition not found for view: "{view_name}"')
            return False

        for dashboard in (self.qs.dashboards or {}).values():
            if view_name in dashboard.views:
                print(f'View {view_name} is used by dashboard "{dashboard.id}". Skipping')
                return False

        self.athena.discover_views([view_name])
        if view_name not in self.athena._metadata.keys():
            print(f'Table for deletion not found: {view_name}')
        else:
            if definition.get('type', '') == 'Glue_Table':
                print(f'Deleting table: {view_name}')
                self.athena.delete_table(view_name)
            else:
                print(f'Deleting view:  {view_name}')
                self.athena.delete_view(view_name)

        # manage dependancies
        for dependancy_view in list(set(definition.get('dependsOn', {}).get('views', []))):
            self.delete_view(dependancy_view)

        return True

    @command
    def cleanup(self, **kwargs):
        """Delete unused resources (QuickSight datasets, Athena views)"""

        self.qs.discover_dashboards()
        self.qs.discover_datasets()
        used_datasets = [x for v in self.qs.dashboards.values() for x in v.datasets.values() ]
        for v in list(self.qs._datasets.values()):
            if v.arn not in used_datasets and click.confirm(f'Delete unused dataset {v.name}?'):
                logger.info(f'Deleting dataset {v.name} ({v.arn})')
                self.qs.delete_dataset(v.id)
                logger.info(f'Deleted dataset {v.name} ({v.arn})')
                print(f'Deleted dataset {v.name} ({v.arn})')
            else:
                print(f'Dataset {v.name} ({v.arn}) is in use')


    @command
    def share(self, dashboard_id, **kwargs):
        """Share resources (QuickSight datasets, dashboards)"""
        self._share(dashboard_id, **kwargs)


    def _share(self, dashboard_id, **kwargs):
        """Share resources (QuickSight datasets, dashboards)"""

        if not dashboard_id:
            if not self.qs.dashboards:
                print('No deployed dashboards found')
                return
            dashboard_id = self.qs.select_dashboard(force=True)
            if not dashboard_id:
                return
        else:
            # Describe dashboard by the ID given, no discovery
            self.qs.discover_dashboard(dashboardId=dashboard_id)

        dashboard = self.qs.dashboards.get(dashboard_id)

        if dashboard is None:
            print('not deployed.')
            return

        share_methods = {
            'Shared Folder (except datasource)': 'folder',
            'Specific User only': 'user',
            'Everyone in this account': 'account',
        }
        share_method = get_parameter(
            param_name='share-method',
            message="Please select sharing method",
            choices=share_methods,
        )
        if share_method == 'folder':
            folder = None
            folder_methods = {
                'Select Existing folder': 'existing',
                'Create New folder': 'new'
            }
            folder_method = get_parameter(
                param_name='folder-method',
                message="Please select folder method",
                choices=folder_methods,
            )
            if folder_method == 'existing':
                try:
                    folder = self.qs.select_folder()
                except self.qs.client.exceptions.AccessDeniedException:
                    # If user is not allowed to select folder, prompt for it
                    print('\nYou are not allowed to select folder, please enter folder ID')
                    while not folder:
                        folder_id = get_parameter(
                            param_name='folder-id',
                            message='Please enter the folder Id to use'
                        )
                        folder = self.qs.describe_folder(folder_id)
                    print(f'Selected folder {folder.get("Name")} ({folder.get("FolderId")})')
            elif folder_method == 'new' or not folder:
                # If user is allowed to select folder, but there is no folder exists, prompt to create one
                if folder_method != 'new':
                    print("No folders found, creating one...")
                while not folder:
                    try:
                        folder_name = get_parameter(
                            param_name='folder-name',
                            message='Please enter the folder name to create'
                        )
                        folder_permissions_tpl = Template(resource_string(
                            package_or_requirement='cid.builtin.core',
                            resource_name=f'data/permissions/folder_permissions.json',
                        ).decode('utf-8'))
                        columns_tpl = {
                            'PrincipalArn': self.qs.get_principal_arn()
                        }
                        folder_permissions = json.loads(folder_permissions_tpl.safe_substitute(columns_tpl))
                        folder = self.qs.create_folder(folder_name, **folder_permissions)
                    except self.qs.client.exceptions.AccessDeniedException:
                        raise CidError('You are not allowed to create folder, unable to proceed')

            self.qs.create_folder_membership(folder.get('FolderId'), dashboard.id, 'DASHBOARD')
            for _id in dashboard.datasets.values():
                self.qs.create_folder_membership(folder.get('FolderId'), _id, 'DATASET')
            print(f'Sharing complete')
        elif share_method in ['account', 'user']:
            if share_method == 'account':
                principal_arn = f"arn:aws:quicksight:{self.qs.identityRegion}:{self.qs.account_id}:namespace/default"
                template_filename = 'data/permissions/dashboard_permissions_namespace.json'
            elif share_method == 'user':
                template_filename = 'data/permissions/dashboard_permissions.json'
                user = self.qs.select_user()
                while not user:
                    user_name = get_parameter(
                        param_name='quicksight-user',
                        message='Please enter the user name to share with'
                    )
                    user = self.qs.describe_user(user_name)
                    if not user:
                        print(f'QuickSight user {user_name} was not found')
                        unset_parameter('quicksight-user')
                principal_arn = user.get('Arn')

            # Update Dashboard permissions
            columns_tpl = {
                'PrincipalArn': principal_arn
            }
            dashboard_permissions_tpl = Template(resource_string(
                package_or_requirement='cid.builtin.core',
                resource_name=template_filename,
            ).decode('utf-8'))
            dashboard_permissions = json.loads(dashboard_permissions_tpl.safe_substitute(columns_tpl))
            dashboard_params = {
                "GrantPermissions": [
                    dashboard_permissions
                ]
            }
            if share_method == 'account':
                dashboard_params.update({
                    "GrantLinkPermissions": [
                        dashboard_permissions
                    ]
                })

            logger.info(f'Sharing dashboard {dashboard.name} ({dashboard.id})')
            try:
                self.qs.update_dashboard_permissions(DashboardId=dashboard.id, **dashboard_params)
                logger.info(f'Shared dashboard {dashboard.name} ({dashboard.id})')
            except self.qs.client.exceptions.AccessDeniedException:
                logger.error('An error occurred (AccessDeniedException) when calling the UpdateDashboardPermissions operation')

            # Update DataSet permissions
            if share_method == 'account':
                logger.info(f'Sharing datasets/datasources with an account is not supported, skipping')
            else:
                data_set_permissions_tpl = Template(resource_string(
                    package_or_requirement='cid.builtin.core',
                    resource_name=f'data/permissions/data_set_permissions.json',
                ).decode('utf-8'))
                data_set_permissions = json.loads(data_set_permissions_tpl.safe_substitute(columns_tpl))

                _datasources: Dict[str, Datasource] = {}
                for _id in dashboard.datasets.values():
                    logger.info(f'Sharing dataset {_id}')
                    self.qs.update_data_set_permissions(DataSetId=_id, GrantPermissions=[data_set_permissions])
                    logger.info(f'Sharing dataset {_id} complete')
                    _dataset = self.qs._datasets.get(_id)
                    # Extract DataSources from DataSet
                    for v in _dataset.datasources:
                        _datasource = self.qs.describe_data_source(v)
                        if not _datasources.get(_datasource.id):
                            _datasources.update({_datasource.id: _datasource})

                data_source_permissions_tpl = Template(resource_string(
                    package_or_requirement='cid.builtin.core',
                    resource_name=f'data/permissions/data_source_permissions.json',
                ).decode('utf-8'))
                data_source_permissions = json.loads(data_source_permissions_tpl.safe_substitute(columns_tpl))
                for k, v in _datasources.items():
                    logger.info(f'Sharing data source "{v.name}" ({k})')
                    self.qs.update_data_source_permissions(DataSourceId=k, GrantPermissions=[data_source_permissions])
                    logger.info(f'Sharing data source "{v.name}" ({k}) complete')

            print(f'Sharing complete')

    @command
    def update(self, dashboard_id, recursive=False, force=False, **kwargs):
        """Update Dashboard

        :param dashboard_id: dashboard_id, if None user will be asked to choose
        :param recursive: Update Datasets and Views as well
        :param force: allow selection of already updated dashboards in the manual selection mode
        """
        if not dashboard_id:
            if not self.qs.dashboards:
                print('\nNo deployed dashboards found')
                return
            dashboard_id = self.qs.select_dashboard(force)
            if not dashboard_id:
                if not force:
                    print('\nNo updates available or dashboard(s) is/are broken, use --force to allow selection\n')
                return

        return self._deploy(dashboard_id, recursive=recursive, update=True)


    def update_dashboard(self, dashboard_id, recursive=False, **kwargs):

        dashboard = self.qs.dashboards.get(dashboard_id)
        if not dashboard:
            click.echo(f'Dashboard "{dashboard_id}" is not deployed')
            return

        print(f'\nChecking for updates...')
        print(f'Deployed template: {dashboard.deployedTemplate.arn}')
        print(f"Latest template: {dashboard.sourceTemplate.arn}/version/{dashboard.latest_version}")
        if dashboard.status == 'legacy':
            if get_parameter(
                param_name=f'confirm-update',
                message=f'Dashboard template changed, update it anyway?',
                choices=['yes', 'no'],
                default='yes') != 'yes':
                return
        elif dashboard.latest:
            if get_parameter(
                param_name=f'confirm-update',
                message=f'No updates available, should I update it anyway?',
                choices=['yes', 'no'],
                default='yes') != 'yes':
                return

        # Update dashboard
        print(f'\nUpdating {dashboard_id}')
        try:
            self.qs.update_dashboard(dashboard, **kwargs)
            print('Update completed\n')
            dashboard.display_url(self.qs_url, launch=True, **self.qs_url_params)
            self.track('updated', dashboard_id)
        except Exception as e:
            # Catch exception and dump a reason
            logger.debug(e, exc_info=True)
            print(f'failed with an error message: {e}')

        return dashboard_id


    def create_datasets(self, _datasets: list, known_datasets: dict={}, recursive: bool=True, update: bool=False) -> dict:
        # Check dependencies
        required_datasets = sorted(_datasets)
        print('\nRequired datasets: \n - {}\n'.format('\n - '.join(list(set(required_datasets)))))

        for dataset_name in required_datasets:
            _ds_id = get_parameters().get(f'{dataset_name.replace("_", "-")}-dataset-id')
            if _ds_id:
                self.qs.describe_dataset(_ds_id)
        
        found_datasets = utils.intersection(required_datasets, [v.name for v in self.qs.datasets.values()])
        missing_datasets = utils.difference(required_datasets, found_datasets)

        # Update existing datasets
        if update:
            for dataset_name in found_datasets[:]:
                if dataset_name in known_datasets.keys():
                    dataset_id = self.qs.get_datasets(id=known_datasets.get(dataset_name))[0].id
                else:
                    datasets = self.qs.get_datasets(name=dataset_name)
                    if not datasets:
                        continue
                    elif len(datasets) == 1:
                        dataset_id = datasets[0].id
                    else:
                        dataset_id = get_parameter(
                            param_name=f'{dataset_name}-dataset-id',
                            message=f'Multiple "{dataset_name}" datasets detected, please select one',
                            choices=[v.id for v in datasets],
                            default=datasets[0].id
                        )
                    known_datasets.update({dataset_name: dataset_id})
                print(f'Updating dataset: "{dataset_name}"')
                try:
                    dataset_definition = self.get_definition("dataset", name=dataset_name)
                    if not dataset_definition:
                        print(f'Dataset definition not found, skipping {dataset_name}')
                        continue
                except Exception as e:
                    logger.critical('dashboard definition is broken, unable to proceed.')
                    logger.critical(f'dataset definition not found: {dataset_name}')
                    logger.critical(e, exc_info=True)
                    raise
                try:
                    if self.create_or_update_dataset(dataset_definition, dataset_id, recursive=recursive, update=update):
                        print(f'Updated dataset: "{dataset_name}"')
                    else:
                        print(f'Dataset "{dataset_name}" update failed, collect debug log for more info')
                except self.qs.client.exceptions.AccessDeniedException as exc:
                    print(f'Unable to update, missing permissions: {exc}')
                except Exception as e:
                    logger.debug(e, exc_info=True)
                    raise


        # Look by DataSetId from dataset_template file
        if len(missing_datasets):
            # Look for previously saved deployment info
            print('\nLooking by DataSetId defined in template...', end='')
            for dataset_name in missing_datasets[:]:
                try:
                    dataset_definition = self.get_definition(type='dataset', name=dataset_name)
                    raw_template = self.get_dataset_data_from_definition(dataset_definition)
                    if raw_template:
                        ds = self.qs.describe_dataset(raw_template.get('DataSetId'))
                        if isinstance(ds, Dataset) and ds.name == dataset_name:
                            missing_datasets.remove(dataset_name)
                            print(f"\n\tFound {dataset_name} as {raw_template.get('DataSetId')}")

                except FileNotFoundError:
                    logger.info(f'Definitions File for Dataset "{dataset_name}" not found')
                    pass
                except self.qs.client.exceptions.ResourceNotFoundException:
                    logger.info(f'Dataset "{dataset_name}" not found')
                    pass
                except self.qs.client.exceptions.AccessDeniedException:
                    logger.info(f'Access denied trying to find dataset "{dataset_name}"')
                    pass
                except Exception as e:
                    logger.debug(e, exc_info=True)
            print('complete')

        # If there still datasets missing try automatic creation
        if len(missing_datasets):
            missing_str = ', '.join(missing_datasets)
            print(f'\nThere are still {len(missing_datasets)} datasets missing: {missing_str}')
            for dataset_name in missing_datasets[:]:
                dataset_id = known_datasets.get(dataset_name)
                print(f'Creating dataset: {dataset_name}')
                try:
                    dataset_definition = self.get_definition("dataset", name=dataset_name)
                except Exception as e:
                    logger.critical('dashboard definition is broken, unable to proceed.')
                    logger.critical(f'dataset definition not found: {dataset_name}')
                    logger.critical(e, exc_info=True)
                    raise
                try:
                    if self.create_or_update_dataset(dataset_definition, dataset_id, recursive=recursive, update=update):
                        missing_datasets.remove(dataset_name)
                        print(f'Dataset "{dataset_name}" created')
                    else:
                        print(f'Dataset "{dataset_name}" creation failed, collect debug log for more info')
                except self.qs.client.exceptions.AccessDeniedException as e:
                    print(f'Unable to create dataset  "{dataset_name}", missing permissions')
                    logger.info(f'Unable to create dataset  "{dataset_name}", missing permissions')
                    logger.debug(e, exc_info=True)
                except Exception as e:
                    logger.debug(e, exc_info=True)
                    raise

        # Last chance to enter DataSetIds manually by user
        if len(missing_datasets):
            missing_str = '\n - '.join(missing_datasets)
            print(f'\nThere are still {len(missing_datasets)} datasets missing: \n - {missing_str}')
            print(f"\nCan't move forward without full list, please manually create datasets and provide DataSetIds")
            # Loop over the list unless we get it empty
            while len(missing_datasets):
                # Make a copy and then get an item from the list
                dataset_name = missing_datasets.copy().pop()
                _id = get_parameter(
                    param_name=f'{dataset_name}-dataset-id',
                    message=f'DataSetId/Arn for {dataset_name}'
                )
                id = _id.split('/')[-1]
                try:
                    _dataset = self.qs.describe_dataset(id)
                    if _dataset.name != dataset_name:
                        print(f"\tFound dataset with a different name: {_dataset.name}, please provide another one")
                        unset_parameter(f'{dataset_name}-dataset-id')
                        continue
                    self.qs._datasets.update({dataset_name: _dataset})
                    missing_datasets.remove(dataset_name)
                    print(f'\tFound valid "{_dataset.name}" dataset, using')
                    logger.info(f'\tFound valid "{_dataset.name}" ({_dataset.id}) dataset, using')
                except Exception as e:
                    logger.debug(e, exc_info=True)
                    print(f"\tProvided DataSetId '{id}' can't be found\n")
                    unset_parameter(f'{dataset_name}-dataset-id')
                    continue
            print('\n')

    def get_dataset_data_from_definition(self, dataset_definition):
        raw_template = None
        dataset_file = dataset_definition.get('File')
        if dataset_file:
            raw_template = json.loads(resource_string(
                dataset_definition.get('providedBy'), f'data/datasets/{dataset_file}'
            ).decode('utf-8'))
        elif dataset_definition.get('Data'):
            raw_template = dataset_definition.get('Data')
        if raw_template is None:
            raise CidCritical(f"Error: definition is broken. Cannot find data for {repr(dataset_definition)}. Check resources file.")
        return raw_template


    def create_or_update_dataset(self, dataset_definition: dict, dataset_id: str=None,recursive: bool=True, update: bool=False) -> bool:
        # Read dataset definition from template
        data = self.get_dataset_data_from_definition(dataset_definition)
        template = Template(json.dumps(data))
        cur_required = dataset_definition.get('dependsOn', dict()).get('cur')
        athena_datasource = None

        if get_parameters().get('quicksight-datasource-id'):
            # We have explicit choice of datasource
            datasource_id = get_parameters().get('quicksight-datasource-id')

            try:
                athena_datasource = self.qs.describe_data_source(datasource_id)
            except self.qs.client.exceptions.AccessDeniedException:
                athena_datasource = Datasource(raw={
                    'AthenaParameters':{},
                    "Id": datasource_id,
                    "Arn": f"arn:aws:quicksight:{self.base.session.region_name}:{self.base.account_id}:datasource/{datasource_id}",
                })

        if not athena_datasource and not len(self.qs.athena_datasources):
            logger.info('No Athena datasources found, attempting to create one')
            self.qs.AthenaWorkGroup = self.athena.WorkGroup
            self.qs.create_data_source() # FIXME: we need to use name/id provided by user if any
            # FIXME: we need to cleanup if datasource creation fails

        if not athena_datasource:
            if not self.qs.athena_datasources:
                logger.info('No valid DataSources available, failing')
                print('No valid DataSources detected and unable to create one. Please create at least one DataSet manually in QuickSight and see why it fails.')
                # Not failing here to let views creation below
            else:
                datasource_choices = {
                    f"{datasource.name} {id_} (workgroup={datasource.AthenaParameters.get('WorkGroup')})":id_
                    for id_, datasource in self.qs.athena_datasources.items()
                }
                if get_parameters().get('quicksight-datasource-id'):
                    # We have explicit choice of datasource
                    datasource_id = get_parameters().get('quicksight-datasource-id')
                    if datasource_id not in datasource_choices.values():
                        logger.critical(
                            f'quicksight-datasource-id={datasource_id} not found or not in a valid state. '
                            f'Here is a list of available DataSources (Name ID WorkGroup): {datasource_choices.keys()}'
                        )
                        exit(1)
                    athena_datasource = self.qs.athena_datasources[datasource_id]

                else:
                    # Datasources are not obvious for customer so we will try to do our best guess
                    # - if there is just one? -> take that one
                    # - if datasource is references in existing dataset? -> take that one
                    # - if athena workgroup defined -> Try to find a dataset with this workgroup
                    # - and if still nothing -> ask an expicit choice from the user
                    pre_compiled_dataset = json.loads(template.safe_substitute())
                    dataset_name = pre_compiled_dataset.get('Name')

                    # let's find the schema/database and workgroup name
                    schemas = []
                    datasources = []
                    if dataset_id:
                        schemas = self.qs.get_datasets(id=dataset_id)[0].schemas
                        datasources = self.qs.get_datasets(id=dataset_id)[0].datasources
                    else: # try to find dataset and get athena database
                        found_datasets = self.qs.get_datasets(name=dataset_name)
                        if found_datasets:
                            schemas = list(set(sum([d.schemas for d in found_datasets], [])))
                            datasources = list(set(sum([d.datasources for d in found_datasets], [])))

                    if len(schemas) == 1:
                        self.athena.DatabaseName = schemas[0]
                    # else user will be suggested to choose database anyway

                    if len(datasources) == 1 and datasources[0] in self.qs.athena_datasources:
                        athena_datasource = self.qs.get_datasources(id=datasources[0])[0]
                    else:
                        #try to find a datasource with defined workgroup
                        workgroup = self.athena.WorkGroup
                        datasources_with_workgroup = self.qs.get_datasources(athena_workgroup_name=workgroup)
                        if len(datasources_with_workgroup) == 1:
                            athena_datasource = datasources_with_workgroup[0]
                        else:
                            #cannot find the right athena_datasource
                            logger.info('Multiple DataSources found.')
                            datasource_id = get_parameter(
                                param_name='quicksight-datasource-id',
                                message=f"Please choose DataSource (Choose the first one if not sure).",
                                choices=datasource_choices,
                            )
                            athena_datasource = self.qs.athena_datasources[datasource_id]
                            logger.info(f'Found {len(datasources)} Athena datasources, not using {athena_datasource.id}')
        if isinstance(athena_datasource, Datasource) and athena_datasource.AthenaParameters.get('WorkGroup', None):
            self.athena.WorkGroup = athena_datasource.AthenaParameters.get('WorkGroup')
        else:
            logger.debug('Athena_datasource is not defined. Will only create views')

        # Check for required views
        _views = dataset_definition.get('dependsOn', {}).get('views', [])
        required_views = [(self.cur.tableName if cur_required and name =='${cur_table_name}' else name) for name in _views]

        self.athena.discover_views(required_views)
        found_views = utils.intersection(required_views, self.athena._metadata.keys())
        missing_views = utils.difference(required_views, found_views)

        if recursive:
            print(f"Detected views: {', '.join(found_views)}")
            for view_name in found_views:
                if cur_required and view_name == self.cur.tableName:
                    logger.debug(f'Dependancy view {view_name} is a CUR. Skip.')
                    continue
                if view_name == 'account_map':
                    logger.debug(f'Dependancy view is {view_name}. Skip.')
                    continue
                self.create_or_update_view(view_name, recursive=recursive, update=update)

        # create missing views
        if len(missing_views):
            print(f"Missing views: {', '.join(missing_views)}")
            for view_name in missing_views:
                self.create_or_update_view(view_name, recursive=recursive, update=update)

        if not isinstance(athena_datasource, Datasource): return False
        # Proceed only if all the parameters are set
        columns_tpl = {
            'athena_datasource_arn': athena_datasource.arn,
            'athena_database_name': self.athena.DatabaseName,
            'cur_table_name': self.cur.tableName if cur_required else None
        }

        compiled_dataset = json.loads(template.safe_substitute(columns_tpl))
        if dataset_id:
            compiled_dataset.update({'DataSetId': dataset_id})

        found_dataset = self.qs.describe_dataset(compiled_dataset.get('DataSetId'))
        if isinstance(found_dataset, Dataset):
            if update:
                self.qs.update_dataset(compiled_dataset)
            elif found_dataset.name != compiled_dataset.get('Name'):
                print(f"Dataset found with name {found_dataset.name}, but {compiled_dataset.get('Name')} expected. Updating.")
                self.qs.update_dataset(compiled_dataset)
            else:
                print(f'No update requested for dataset {compiled_dataset.get("DataSetId")}')
        else:
            self.qs.create_dataset(compiled_dataset)

        return True


    def create_or_update_view(self, view_name: str, recursive: bool=True, update: bool=False) -> None:
        # For account mappings create a view using a special helper
        if view_name in self._visited_views: # avoid checking a views multiple times in one cid session
            return
        logger.info(f'Processing view: {view_name}')
        self._visited_views.append(view_name)

        if view_name in ['account_map', 'aws_accounts']:
            if view_name in self.athena._metadata.keys():
                print(f'Account map {view_name} exists. Skipping.')
            else:
                self.accountMap.create(view_name) #FIXME: add or_update
            return

        # Create a view
        logger.info(f'Getting view definition')
        view_definition = self.get_definition("view", name=view_name)
        if not view_definition and view_name in self.athena._metadata.keys():
            logger.info(f"Definition is unavailable but view exists: {view_name}, skipping")
            return
        logger.debug(f'View definition: {view_definition}')

        if recursive:
            dependency_views = view_definition.get('dependsOn', dict()).get('views', list())
            if 'cur' in dependency_views: dependency_views.remove('cur')
            # Discover dependency views (may not be discovered earlier)
            self.athena.discover_views(dependency_views)
            logger.info(f"Dependency views: {', '.join(dependency_views)}" if dependency_views else 'No dependency views')
            for dep_view_name in dependency_views:
                if dep_view_name not in self.athena._metadata.keys():
                    print(f'Missing dependency view: {dep_view_name}, creating')
                    logger.info(f'Missing dependency view: {dep_view_name}, creating')
                self.create_or_update_view(dep_view_name, recursive=recursive, update=update)
        view_query = self.get_view_query(view_name=view_name)
        logger.debug(f'view_query: {view_query}')
        if view_name in self.athena._metadata.keys():
            logger.debug(f'View "{view_name}" exists')
            if update:
                logger.info(f'Updating view: "{view_name}"')
                if view_definition.get('type') == 'Glue_Table':
                    print(f'Updating table {view_name}')
                    self.glue.create_or_update_table(view_name, view_query)
                else:
                    if 'CREATE OR REPLACE' in view_query.upper():
                        print(f'Updating view: "{view_name}"')
                        self.athena.execute_query(view_query)
                    else:
                        print(f'View "{view_name}" is not compatible with update. Skipping.')
                assert self.athena.wait_for_view(view_name), f"Failed to update a view {view_name}"
                logger.info(f'View "{view_name}" updated')
            else:
                return
        else:
            logger.info(f'Creating view: "{view_name}"')
            if view_definition.get('type') == 'Glue_Table':
                self.glue.create_or_update_table(view_name, view_query)
            else:
                self.athena.execute_query(view_query)
            assert self.athena.wait_for_view(view_name), f"Failed to create a view {view_name}"
            logger.info(f'View "{view_name}" created')


    def get_view_query(self, view_name: str) -> str:
        """ Returns a fully compiled AHQ """
        # View path
        view_definition = self.get_definition("view", name=view_name)
        cur_required = view_definition.get('dependsOn', dict()).get('cur')
        if cur_required and self.cur.hasSavingsPlans and self.cur.hasReservations and view_definition.get('spriFile'):
            view_file = view_definition.get('spriFile')
        elif cur_required and self.cur.hasSavingsPlans and view_definition.get('spFile'):
            view_file = view_definition.get('spFile')
        elif cur_required and self.cur.hasReservations and view_definition.get('riFile'):
            view_file = view_definition.get('riFile')
        elif view_definition.get('File'):
            view_file = view_definition.get('File')
        else:
            logger.critical(f'\nCannot find view {view_name}. View information is incorrect, please check resources.yaml')
            raise Exception(f'\nCannot find view {view_name}')

        # Load TPL file
        template = Template(resource_string(
            view_definition.get('providedBy'),
            f'data/queries/{view_file}'
        ).decode('utf-8'))

        # Prepare template parameters
        columns_tpl = {
            'cur_table_name': self.cur.tableName if cur_required else None,
            'athenaTableName': view_name,
            'athena_database_name': self.athena.DatabaseName,
        }

        for k, v in view_definition.get('parameters', dict()).items():
            if isinstance(v, str):
                param = {k:v}
            elif isinstance(v, dict):
                value = v.get('value')
                while not value:
                    value = get_parameter(
                        param_name=f'view-{view_name}-{k}',
                        message=f"Required parameter: {k} ({v.get('description')})",
                        default=v.get('default'),
                        template_variables=dict(account_id=self.base.account_id),
                    )
                param = {k:value}
            else:
                raise CidCritical(f'Unknown parameter type for "{k}". Must be a string or a dict with value or with default key')
            # Add parameter
            columns_tpl.update(param)
        # Compile template
        compiled_query = template.safe_substitute(columns_tpl)

        return compiled_query

    @command
    def map(self, **kwargs):
        """Create account mapping Athena views"""
        for v in ['account_map', 'aws_accounts']:
            self.accountMap.create(v)

