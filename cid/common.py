from pkg_resources import resource_string
import questionary

from cid import utils
from cid.helpers import Athena, CUR, Glue, QuickSight, Dashboard
from cid.helpers.account_map import AccountMap
from cid.plugin import Plugin

import os
import sys

import click
from string import Template

import json

from pathlib import Path
from botocore.exceptions import NoCredentialsError

from deepmerge import always_merger

import logging
logger = logging.getLogger(__name__)


class Cid:
    defaults = {
        'quicksight_url': 'https://{region}.quicksight.aws.amazon.com/sn/dashboards/{dashboard_id}'
    }

    def __init__(self, **kwargs) -> None:
        # Defined resources
        self.resources = dict()
        self.dashboards = dict()
        self.plugins = self.__loadPlugins()
        self._clients = dict()
        self.awsIdentity = None
        self.session = None
        self.qs_url = kwargs.get(
            'quicksight_url', self.defaults.get('quicksight_url'))

    @property
    def qs(self) -> QuickSight:
        if not self._clients.get('quicksight'):
            self._clients.update({
                'quicksight': QuickSight(self.session, self.awsIdentity, resources=self.resources)
            })
        return self._clients.get('quicksight')

    @property
    def athena(self) -> Athena:
        if not self._clients.get('athena'):
            self._clients.update({
                'athena': Athena(self.session, resources=self.resources)
            })
        return self._clients.get('athena')

    @property
    def glue(self) -> Glue:
        if not self._clients.get('glue'):
            self._clients.update({
                'glue': Glue(self.session)
            })
        return self._clients.get('glue')

    @property
    def cur(self) -> CUR:
        if not self._clients.get('cur'):
            _cur = CUR(self.session)
            _cur.athena = self.athena
            print('Checking if CUR is enabled and available...')

            if not _cur.configured:
                print(
                    "Error: please ensure CUR is enabled, if yes allow it some time to propagate")
                exit(1)
            print(f'\tAthena table: {_cur.tableName}')
            print('\tResource IDs: {}'.format(
                'yes' if _cur.hasResourceIDs else 'no'))
            if not _cur.hasResourceIDs:
                print("Error: CUR has to be created with Resource IDs")
                exit(1)
            print('\tSavingsPlans: {}'.format(
                'yes' if _cur.hasSavingsPlans else 'no'))
            print('\tReserved Instances: {}'.format(
                'yes' if _cur.hasReservations else 'no'))
            print('done')
            self._clients.update({
                'cur': _cur
            })
        return self._clients.get('cur')

    @property
    def accountMap(self) -> AccountMap:
        if not self._clients.get('accountMap'):
            _account_map = AccountMap(self.session)
            _account_map.athena = self.athena
            _account_map.cur = self.cur

            self._clients.update({
                'accountMap': _account_map
            })
        return self._clients.get('accountMap')

    def __loadPlugins(self) -> dict:
        if sys.version_info < (3, 8):
            from importlib_metadata import entry_points
        else:
            from importlib.metadata import entry_points

        plugins = dict()
        _entry_points = entry_points().get('cid.plugins')
        print('Loading plugins...')
        for ep in _entry_points:
            plugin = Plugin(ep.value)
            print(f"\t{ep.name} loaded")
            plugins.update({ep.value: plugin})
            try:
                self.resources = always_merger.merge(
                    self.resources, plugin.provides())
            except AttributeError:
                pass
        print('done\n')
        return plugins

    def getPlugin(self, plugin) -> dict:
        return self.plugins.get(plugin)

    def run(self, **kwargs):
        print('Checking AWS environment...')
        try:
            self.session = utils.get_boto_session(**kwargs)
            if kwargs.get('profile_name'):
                print('\tprofile name: {name}'.format(
                    name=kwargs.get('profile_name')))
            sts = utils.get_boto_client(service_name='sts', **kwargs)
            self.awsIdentity = sts.get_caller_identity()
        except NoCredentialsError:
            print('Error: Not authenticated, please check AWS credentials')
            exit()
        print('\taccountId: {}\n\tAWS userId: {}'.format(
            self.awsIdentity.get('Account'),
            self.awsIdentity.get('Arn').split(':')[5]
        ))
        print('\tRegion: {}'.format(kwargs.get('region_name')))
        print('done\n')


    def deploy(self, **kwargs):
        """ Deploy Dashboard """

        selection = list()
        for k, dashboard in self.resources.get('dashboards').items():
            selection.append(
                questionary.Choice(
                    title=f"{dashboard.get('name')}",
                    value=k
                )
            )
        try:
            selected_dashboard = questionary.select(
                "\nPlease select dashboard to install",
                choices=selection
            ).ask()
        except:
            print('\nEnd: No updates available or dashboard(s) is/are broken\n')
            return

        # Get selected dashboard definition
        dashboard_definition = self.resources.get(
            'dashboards').get(selected_dashboard)
        required_datasets = dashboard_definition.get(
            'dependsOn', dict()).get('datasets', list())
        self.create_datasets(required_datasets)

        # Prepare API parameters
        if not dashboard_definition.get('datasets'):
            dashboard_definition.update({'datasets': {}})
        dashboard_datasets = dashboard_definition.get('datasets')
        for dataset_name in required_datasets:
            dashboard_datasets.update(
                {dataset_name: self.qs._datasets.get(dataset_name).get('Arn')})

        kwargs = dict()
        local_overrides = f'work/{self.awsIdentity.get("Account")}/{dashboard_definition.get("dashboardId")}.json'
        print(
            f'Looking for local overrides file "{local_overrides}"...', end='')
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
            print('not found')

        # Get QuickSight template details
        latest_template = self.qs.describe_template(template_id=dashboard_definition.get(
            'templateId'), account_id=dashboard_definition.get('sourceAccountId'))
        dashboard_definition.update({'sourceTemplate': latest_template})

        # Create dashboard
        click.echo(
            f"Latest template: {latest_template.get('Arn')}/version/{latest_template.get('Version').get('VersionNumber')}")
        click.echo('\nDeploying...', nl=False)
        _url = self.qs_url.format(
            account_id=self.awsIdentity.get('Account'),
            region=self.session.region_name,
            dashboard_id=dashboard_definition.get('dashboardId')
        )
        try:
            self.qs.create_dashboard(dashboard_definition, **kwargs)
            click.echo('completed')
            click.echo(
                f"#######\n####### Congratulations!\n####### {dashboard_definition.get('name')} is available at: {_url}\n#######")
        except self.qs.client.exceptions.ResourceExistsException:
            click.echo('error, already exists')
            click.echo(
                f"#######\n####### {dashboard_definition.get('name')} is available at: {_url}\n#######")
        except Exception as e:
            # Catch exception and dump a reason
            click.echo('failed, dumping error message')
            print(json.dumps(e, indent=4, sort_keys=True, default=str))
            exit(1)

        return dashboard.get('dashboardId')


    def open(self, dashboard_id):
        """Open QuickSight dashboard in browser"""

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
            _url = self.qs_url.format(
                account_id=self.awsIdentity.get('Account'),
                region=self.session.region_name,
                dashboard_id=dashboard_id
            )
            click.echo('healthy, opening...')
            click.launch(_url)
        else:
            click.echo('not deployed.')
        
        return dashboard_id

    def status(self, dashboard_id, **kwargs):
        """Check QuickSight dashboard status"""

        if not dashboard_id:
            dashboard_id = self.qs.select_dashboard(force=True)
            if not dashboard_id:
                click.echo('No deployed dashboard found')
                return
            dashboard = self.qs.dashboards.get(dashboard_id)
        else:
            # Describe dashboard by the ID given, no discovery
            result = self.qs.describe_dashboard(DashboardId=dashboard_id)
            if result:
                dashboard = Dashboard(result.get('Dashboard'))
            else:
                dashboard = None

        click.echo('Getting dashboard status...', nl=False)
        if dashboard is not None:
            print('\n'+json.dumps(dashboard.dashboard,
                  indent=4, sort_keys=True, default=str))
            if dashboard.version.get('Status') in ['CREATION_SUCCESSFUL']:
                click.echo(f'\nDashboard is healthy.')
            else:
                print(json.dumps(dashboard.version.get('Errors'),
                      indent=4, sort_keys=True, default=str))
                click.echo(
                    f'\nDashboard is unhealthy, please check errors above.')
            _url = self.qs_url.format(
                account_id=self.awsIdentity.get('Account'),
                region=self.session.region_name,
                dashboard_id=dashboard_id
            )
            click.echo(
                f"#######\n####### {dashboard.name} is available at: " + _url + "\n#######")
        else:
            click.echo('not deployed.')


    def delete(self, dashboard_id, **kwargs):
        """Delete QuickSight dashboard"""

        if not dashboard_id:
            dashboard_id = self.qs.select_dashboard(force=True)
        if not dashboard_id:
            click.echo('No selection, exiting.')
            exit()
        try:
            # Execute query
            click.echo('Deleting dashboard...', nl=False)
            self.qs.delete_dashboard(dashboard_id=dashboard_id)
            print('deleted')
            return dashboard_id
        except self.qs.client.exceptions.ResourceNotFoundException:
            print('not found')
        except Exception as e:
            # Catch exception and dump a reason
            click.echo('failed, dumping error message')
            print(json.dumps(e, indent=4, sort_keys=True, default=str))


    def update(self, dashboard_id, **kwargs):
        """Update Dashboard"""

        if not dashboard_id:
            dashboard_id = self.qs.select_dashboard(force=kwargs.get('force'))
        if not dashboard_id:
            exit()
        dashboard = self.qs.dashboards.get(dashboard_id)
        if not dashboard:
            click.echo(f'Dashboard "{dashboard_id}" is not deployed')
            return

        print(f'\nChecking for updates...')
        try:
            deployed_template = dashboard.version.get('SourceEntityArn')
        except AttributeError:
            click.echo(f'not deployed')
            return
        click.echo(f'Deployed template: {dashboard.deployed_arn}')
        click.echo(
            f"Latest template: {dashboard.sourceTemplate.get('Arn')}/version/{dashboard.latest_version}")
        if not deployed_template.startswith(dashboard.sourceTemplate.get('Arn')):
            click.confirm(
                "\nDashboard template changed, update it anyway?", abort=True)
        elif not (dashboard.deployed_version < dashboard.latest_version):
            click.confirm(
                "\nNo updates available, should I update it anyway?", abort=True)

        kwargs = dict()
        local_overrides = f'work/{self.awsIdentity.get("Account")}/{dashboard.id}.json'
        print(
            f'Looking for local overrides file "{local_overrides}"...', end='')
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
            print('not found')

        # Update dashboard
        click.echo('\nUpdating...', nl=False)
        try:
            self.qs.update_dashboard(dashboard, **kwargs)
            click.echo('completed')
            _url = self.qs_url.format(
                account_id=self.awsIdentity.get('Account'),
                region=self.session.region_name,
                dashboard_id=dashboard_id
            )
            print(f"#######\n####### {dashboard.name} is available at: {_url}\n#######")
            if click.confirm('Do you wish to open it in your browser?'):
                click.launch(_url)
        except Exception as e:
            # Catch exception and dump a reason
            click.echo('failed, dumping error message')
            print(json.dumps(e, indent=4, sort_keys=True, default=str))

        return dashboard_id


    def create_datasets(self, _datasets: list) -> dict:
        # Check dependencies
        required_datasets = sorted(_datasets)
        print('\nRequired datasets: \n - {}'.format('\n - '.join(required_datasets)))
        try:
            print('\nDetecting existing datasets...', end='')
            for dataset in self.qs.list_data_sets():
                try:
                    self.qs.describe_dataset(dataset.get('DataSetId'))
                except:
                    continue
        except self.qs.client.exceptions.AccessDeniedException:
            print('no permissions, performing full discrovery...', end='')
            self.qs.dashboards
            for dataset in required_datasets:
                dataset_definition = self.resources.get(
                    'datasets').get(dataset)
        finally:
            print('complete')

        found_datasets = sorted(
            set(required_datasets).intersection(self.qs._datasets.keys()))
        missing_datasets = sorted(
            list(set(required_datasets).difference(found_datasets)))

        # If we miss required datasets look in saved deployments
        if len(missing_datasets):
            # TODO: remove below 2 lines ?
            if len(found_datasets):
                print('\nFound: \n - {}'.format('\n - '.join(found_datasets)))
            print('\nMissing: \n - {}'.format('\n - '.join(missing_datasets)))
            # Look for previously saved deployment info
            print('\nLooking in saved deployments...', end='')
            saved_datasets = self.find_saved_datasets(missing_datasets)
            print('{}'.format('nothing found' if not len(
                saved_datasets) else 'complete'))
            for k, v in saved_datasets.items():
                print(f'\tfound: {k}', end='')
                if len(v.keys()) > 1:
                    # Multiple datasets
                    selected = questionary.select(
                        f'Multiple "{k}" datasets detected, please select one',
                        choices=v.keys()
                    ).ask()
                    self.qs._datasets.update({k: v.get(selected)})
                    missing_datasets.remove(k)
                elif len(v.keys()):
                    # Single dataset
                    print(', using')
                    self.qs._datasets.update({k: next(iter(v.values()))})
                    missing_datasets.remove(k)

        # Look by DataSetId from dataset_template file
        if len(missing_datasets):
            # Look for previously saved deployment info
            print('\nLooking by DataSetId defined in template...', end='')
            for dataset_name in missing_datasets[:]:
                try:
                    dataset_definition = self.resources.get(
                        'datasets').get(dataset_name)
                    dataset_file = dataset_definition.get('File')
                    # Load TPL file
                    if dataset_file:
                        raw_template = json.loads(resource_string(dataset_definition.get(
                            'providedBy'), f'data/datasets/{dataset_file}').decode('utf-8'))
                        ds = self.qs.describe_dataset(raw_template.get('DataSetId'))
                        if ds.get('Name') == dataset_name:
                            missing_datasets.remove(dataset_name)
                        print(f"\n\tFound {dataset_name} as {raw_template.get('DataSetId')}")
                except self.qs.client.exceptions.ResourceNotFoundException:
                    pass
                except self.qs.client.exceptions.AccessDeniedException:
                    pass
                except:
                    raise
            print('complete')

        # If there still datasets missing try automatic creation
        if len(missing_datasets):
            missing_str = ', '.join(missing_datasets)
            print(
                f'\nThere are still {len(missing_datasets)} datasets missing: {missing_str}')
            for dataset_name in missing_datasets[:]:
                print(f'Creating dataset: {dataset_name}...', end='')
                try:
                    dataset_definition = self.resources.get(
                        'datasets').get(dataset_name)

                except:
                    logger.critical(
                        'dashboard definition is broken, unable to proceed.')
                    logger.critical(
                        f'dataset definition not found: {dataset_name}')
                    raise
                try:
                    if self.create_dataset(dataset_definition):
                        missing_datasets.remove(dataset_name)
                        print('created')
                    else:
                        print('failed')
                except self.qs.client.exceptions.AccessDeniedException:
                    print(f'unable to create, missing permissions')

        # Last chance to enter DataSetIds manually by user
        if len(missing_datasets):
            missing_str = '\n - '.join(missing_datasets)
            print(
                f'\nThere are still {len(missing_datasets)} datasets missing: \n - {missing_str}')
            print(
                f"\nCan't move forward without full list, please manually create datasets and provide DataSetIds")
            # Loop over the list unless we get it empty
            while len(missing_datasets):
                # Make a copy and then get an item from the list
                dataset_name = missing_datasets.copy().pop()
                _id = click.prompt(
                    f'\tDataSetId/Arn for {dataset_name}', type=str)
                id = _id.split('/')[-1]
                try:
                    _dataset = self.qs.describe_dataset(id)
                    if _dataset.get('Name') != dataset_name:
                        print(f"\tFound dataset with a different name: {_dataset.get('Name')}, please provide another one")
                        continue
                    self.qs._datasets.update({dataset_name: _dataset})
                    missing_datasets.remove(dataset_name)
                    print(f'\tFound, using it')
                except:
                    print(f"\tProvided DataSetId '{id}' can't be found\n")
                    continue


    def create_dataset(self, dataset_definition) -> bool:

        # Check for required views
        _views = dataset_definition.get('dependsOn').get('views')
        required_views = [self.cur.tableName if name ==
                          '${cur_table_name}' else name for name in _views]
        self.athena.discover_views(required_views)
        found_views = sorted(set(required_views).intersection(
            self.athena._metadata.keys()))
        missing_views = sorted(
            list(set(required_views).difference(found_views)))
        # try discovering missing views
        self.athena.discover_views(missing_views)
        # repeat comparison
        found_views = sorted(set(required_views).intersection(
            self.athena._metadata.keys()))
        missing_views = sorted(
            list(set(required_views).difference(found_views)))
        # create missing views
        if len(missing_views):
            print(f'\tmissing Athena views: {missing_views}')
            self.create_views(missing_views)

        # Read dataset definition from template
        dataset_file = dataset_definition.get('File')
        if dataset_file:
            athena_datasources = {
                k: v for (k, v) in self.qs.datasources.items() if v.get('Type') == 'ATHENA'}
            if not len(athena_datasources):
                return False
            # Load TPL file
            columns_tpl = dict()
            columns_tpl.update({
                'cur_table_name': self.cur.tableName if dataset_definition.get('dependsOn').get('cur') else None,
                'athena_datasource_arn': next(iter(athena_datasources)),
                'athena_database_name': self.athena.DatabaseName,
                'user_arn': self.qs.user.get('Arn')
            })
            template = Template(resource_string(dataset_definition.get(
                'providedBy'), f'data/datasets/{dataset_file}').decode('utf-8'))
            compiled_dataset = json.loads(template.substitute(columns_tpl))
            self.qs.create_dataset(compiled_dataset)
        else:
            print(f"Error: {dataset_definition.get('Name')} definition is broken")
            exit(1)
        
        return True


    def find_saved_datasets(self, datasets: list) -> dict:
        """Look for datasets in saved deployments"""
        # Get all saved deployment found
        saved_deployments = self.find_saved_deployments()
        found_datasets = dict()
        for deployment in saved_deployments:
            try:
                # extract dataset references from saved deployment
                _datasets = deployment.get('SourceEntity').get(
                    'SourceTemplate').get('DataSetReferences', list())
                for dataset in _datasets:
                    # we're interested only in datsets from the list
                    if dataset.get('DataSetPlaceholder') in datasets:
                        # check if the dataset exists by describing it
                        try:
                            _dataset = self.qs.describe_dataset(
                                dataset.get('DataSetArn').split('/')[1])
                        except:
                            continue
                        # Create a list of found datasets per dataset name
                        if not found_datasets.get(_dataset.get('Name')):
                            found_datasets.update(
                                {_dataset.get('Name'): dict()})
                        # Add datasets using Arn as a key
                        if not found_datasets.get(_dataset.get('Name')).get(_dataset.get('Arn')):
                            found_datasets.get(_dataset.get('Name')).update(
                                {_dataset.get('Arn'): _dataset})
            except AttributeError:
                # move to next saved deployment if the key is not present
                continue
        return found_datasets


    def find_saved_deployments(self) -> list:
        """Look for saved deployment information"""
        # Set base paths
        abs_path = Path().absolute()

        # Find all saved deployments for current AWS account
        file_path = os.path.join(
            abs_path, f'work/{self.awsIdentity.get("Account")}')
        found_deployments = list()
        if os.path.isdir(file_path):
            files = [f for f in os.listdir(file_path) if f.endswith('.json')]
            for file in files:
                with open(os.path.join(file_path, file)) as f:
                    found_deployments.append(json.loads(f.read()))

        return found_deployments


    def create_views(self, views: list) -> None:
        for view in views:
            self.create_view(view)


    def create_view(self, view_name: str) -> None:
        # For account mappings create a view using a special helper
        if view_name in ['account_map', 'aws_accounts']:
            self.accountMap.create(view_name)
            return
        # Create a view
        print(f'\nCreating view: {view_name}')
        view_definition = self.resources.get('views').get(view_name, dict())
        # Discover dependency views (may not be discovered earlier)
        dependency_views = view_definition.get(
            'dependsOn', dict()).get('views', list())
        self.athena.discover_views(dependency_views)
        while dependency_views:
            dep = dependency_views.copy().pop()
        # for dep in dependency_views:
            if dep not in self.athena._metadata.keys():
                print(f'Missing dependency view: {dep}, trying to create')
                self.create_view(dep)
            dependency_views.remove(dep)
        view_query = self.get_view_query(view_name=view_name)
        if view_definition.get('type') == 'Glue_Table':
            try:
                self.glue.create_table(json.loads(view_query))
            except self.glue.client.exceptions.AlreadyExistsException:
                print(f'\nError: Glue table "{view_name}" exists but not found, please check your configuration, exiting')
                exit(1)
        else:
            self.athena.execute_query(view_query)


    def get_view_query(self, view_name: str) -> str:
        """ Returns a fully compiled AHQ """
        # View path
        view_definition = self.resources.get('views').get(view_name, dict())
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
            logger.critical(
                f'\n"{view_name}" view information is incorrect, skipping')

        # Load TPL file
        template = Template(resource_string(view_definition.get(
            'providedBy'), f'data/queries/{view_file}').decode('utf-8'))

        # Prepare template parameters
        columns_tpl = dict()
        columns_tpl.update({
            'cur_table_name': self.cur.tableName if cur_required else None,
            'athena_database_name': self.athena.DatabaseName if view_definition.get('parameters', dict()).get('athenaDatabaseName') else None
        })
        for k,v in view_definition.get('parameters', dict()).items():
            if k == 'athenaDatabaseName':
                param = {'athena_database_name': self.athena.DatabaseName}
            elif v.get('value'):
                param = {k:v.get('value')}
            else:
                value = None
                while not value:
                    value = click.prompt(f"Required parameter: {k} ({v.get('description')})", default=v.get('value'), show_default=True)
                param = {k:value}
            # Add parameter
            columns_tpl.update(param)
        # Compile template
        compiled_query = template.substitute(columns_tpl)

        return compiled_query

    def map(self):
        """Create account mapping Athena views"""

        self.accountMap.create('account_map')
        self.accountMap.create('aws_accounts')
