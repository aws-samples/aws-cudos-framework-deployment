import os
import sys
import json
import urllib
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
from botocore.exceptions import ClientError, NoCredentialsError, CredentialRetrievalError


from cid import utils
from cid.base import CidBase
from cid.plugin import Plugin
from cid.utils import get_parameter, get_parameters, set_parameters, unset_parameter, get_yesno_parameter, cid_print, isatty, merge_objects
from cid.helpers.account_map import AccountMap
from cid.helpers import Athena, CUR, Glue, QuickSight, Dashboard, Dataset, Datasource, csv2view, Organizations
from cid.helpers.quicksight.template import Template as CidQsTemplate
from cid._version import __version__
from cid.export import export_analysis
from cid.logger import set_cid_logger
from cid.exceptions import CidError, CidCritical
from cid.commands import InitQsCommand

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
        self.catalog_urls = [
            'https://raw.githubusercontent.com/aws-samples/aws-cudos-framework-deployment/main/dashboards/catalog.yaml',
        ]

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
    def organizations(self) -> Organizations:
        if not self._clients.get('organizations'):
            self._clients.update({
                'organizations': Organizations(self.base.session)
            })
        return self._clients.get('organizations')

    @property
    def cur(self) -> CUR:
        if not self._clients.get('cur'):
            _cur = CUR(self.base.session)
            _cur.athena = self.athena
            _cur.glue = self.glue
            print('Checking if CUR is enabled and available...')

            if not _cur.metadata:
                raise CidCritical("Error: please ensure CUR is enabled, if yes allow it some time to propagate")

            print(f'\tAthena table: {_cur.table_name}')
            print(f"\tResource IDs: {'yes' if _cur.has_resource_ids else 'no'}")
            if not _cur.has_resource_ids:
                raise CidCritical("Error: CUR has to be created with Resource IDs")
            print(f"\tSavingsPlans: {'yes' if _cur.has_savings_plans else 'no'}")
            print(f"\tReserved Instances: {'yes' if _cur.has_reservations else 'no'}")
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
                resources = plugin.provides()
                if ep.value != 'cid.builtin.core':
                    resources.get('views', {}).pop('account_map', None) # protect account_map from overriding
                self.resources = merge_objects(self.resources, resources, depth=1)
            except AttributeError:
                logger.warning(f'Failed to load {ep.name}')
        print('\n')
        logger.info('Finished loading plugins')
        return plugins

    def resources_with_global_parameters(self, resources):
        """ render resources with global parameters """
        params = self.get_template_parameters(self.resources.get('parameters', {}))
        def _recursively_process_strings(item, str_func):
            """ recursively update elements of a dict """
            if isinstance(item, str):
                return str_func(item)
            elif isinstance(item, dict):
                res = {}
                for key, value in item.items():
                    res[_recursively_process_strings(key, str_func)] = _recursively_process_strings(value, str_func)
                return res
            elif isinstance(item, list):
                return [_recursively_process_strings(value, str_func) for value in item]
            return item
        def _str_func(text):
            return Template(text).safe_substitute(params)
        return _recursively_process_strings(resources, _str_func)


    def getPlugin(self, plugin) -> dict:
        return self.plugins.get(plugin)


    def get_definition(self, type: str, name: str=None, id: str=None, noparams: bool=False) -> dict:
        """ return resource definition that matches parameters 
        :noparams: do not process parameters as they may not exist by this time
        """
        res = None
        if type not in ['dashboard', 'dataset', 'view', 'schedule']:
            raise ValueError(f'{type} is not a valid definition type')
        if type in ['dataset', 'view', 'schedule'] and name:
            res = self.resources.get(f'{type}s').get(name)
        elif type in ['dashboard']:
            for definition in self.resources.get(f'{type}s').values():
                if name is not None and definition.get('name') != name:
                    continue
                if id is not None and definition.get('dashboardId') != id:
                    continue
                res = definition
                break

        # template
        if isinstance(res, dict) and not noparams:
            name = name or res.get('name')
            params = self.get_template_parameters(res.get('parameters', {}), param_prefix=f'{type}-{name}-')
            # FIXME: can be recursive?
            for key, value in res.items():
                if isinstance(value, str):
                    res[key] = Template(value).safe_substitute(params)
        return res


    @command
    def export(self, **kwargs):
        export_analysis(self.qs, self.athena)

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

    def get_page(self, source):
        resp = requests.get(source, timeout=10)
        resp.raise_for_status()
        return resp

    def load_resources(self):
        ''' load additional resources from command line parameters
        '''
        if get_parameters().get('catalog'):
            self.catalog_urls = get_parameters().get('catalog').split(',')
        for catalog_url in self.catalog_urls:
            self.load_catalog(catalog_url)
        if get_parameters().get('resources'):
            source = get_parameters().get('resources')
            self.load_resource_file(source)
        self.resources = self.resources_with_global_parameters(self.resources)

    def load_resource_file(self, source):
        ''' load additional resources from resource file
        '''
        logger.debug(f'Loading resources from {source}')
        resources = {}
        try:
            if source.startswith('https://'):
                resources = yaml.safe_load(self.get_page(source).text)
                if not isinstance(resources, dict):
                    raise CidCritical(f'Failed to load {source}. Got {type(resources)} ({repr(resources)[:150]}...)')
            else:
                with open(source, encoding='utf-8') as file_:
                    resources = yaml.safe_load(file_)
        except Exception as exc:
            logger.warning(f'Failed to load resources from {source}: {exc}')
            return
        resources.get('views', {}).pop('account_map', None) # Exclude account map as it is a special view
        self.resources = merge_objects(self.resources, resources, depth=1)

    def load_catalog(self, catalog_url):
        ''' load additional resources from catalog
        '''
        try:
            catalog = yaml.safe_load(self.get_page(catalog_url).text)
        except requests.exceptions.HTTPError as exc:
            logger.warning(f'Failed to load catalog url: {exc}')
            logger.debug(exc, exc_info=True)
            return
        for resource_ref in catalog.get('Resources', []):
            url = urllib.parse.urljoin(catalog_url, resource_ref.get("Url"))
            self.load_resource_file(url)


    def get_template_parameters(self, parameters: dict, param_prefix: str='', others: dict=None):
        """ Get template parameters. """
        params = get_parameters()
        for key, value in parameters.items():
            logger.debug(f'reading template parameter: {key} / {value}')
            prefix = '' if value.get('global') else param_prefix
            if isinstance(value, str):
                params[key] = value
            elif isinstance(value, dict) and value.get('type') == 'cur.tag_and_cost_category_fields':
                params[key] = get_parameter(
                    param_name=prefix + key,
                    message=f"Required parameter: {key} ({value.get('description')})",
                    choices=self.cur.tag_and_cost_category_fields + ["'none'"],
                )
            elif isinstance(value, dict) and value.get('type') == 'athena':
                if 'query' not in value:
                    raise CidCritical(f'Failed fetching parameter {prefix}{key}: paramter with type ahena must have query value.')
                query = value['query']
                try:
                    res = self.athena.query(query)[0]
                except (self.athena.client.exceptions.ClientError, CidError, CidCritical) as exc:
                    raise CidCritical(f'Failed fetching parameter {prefix}{key}: {exc}') from exc
                if not res:
                    raise CidCritical(f'Failed fetching parameter {prefix}{key}, {value}. Athena returns empty result')
                params[key] = res[0]
            elif isinstance(value, dict):
                params[key] = value.get('value')
                while params[key] is None:
                    if value.get('silentDefault') is not None and get_parameters().get(key) is None:
                        params[key] = value.get('silentDefault')
                    else:
                        params[key] = get_parameter(
                            param_name=prefix + key,
                            message=f"Required parameter: {key} ({value.get('description')})",
                            default=value.get('default'),
                            template_variables=dict(account_id=self.base.account_id),
                        )
            else:
                raise CidCritical(f'Unknown parameter type for "{key}". Must be a string or a dict with value or with default key')
        return merge_objects(params, others or {}, depth=1)


    @command
    def deploy(self, dashboard_id: str=None, recursive=True, update=False, **kwargs):
        """ Deploy Dashboard Command"""
        self._deploy(dashboard_id, recursive, update, **kwargs)


    def _deploy(self, dashboard_id: str=None, recursive=True, update=False, **kwargs):
        """ Deploy Dashboard """

        self.qs.ensure_subscription()

        # In case if we cannot discover datasets, we need to discover dashboards
        # TODO: check if datasets returns explicit permission denied and only then discover dashboards as a workaround
        self.qs.discover_dashboards()

        dashboard_id = dashboard_id or get_parameters().get('dashboard-id')
        category_filter = [cat for cat in get_parameters().get('category', '').upper().split(',') if cat]
        if not dashboard_id:
            standard_categories = ['Foundational', 'Advanced', 'Additional'] # Show these categories first
            all_categories = set([f"{dashboard.get('category', 'Other')}" for dashboard in self.resources.get('dashboards').values()])
            non_standard_categories = [cat for cat in all_categories if cat not in standard_categories]
            categories =  standard_categories + sorted(non_standard_categories)
            dashboard_options = {}
            for category in categories:
                if category_filter and category.upper() not in category_filter:
                    continue
                dashboard_options[f'{category.upper()}'] = '[category]'
                counter = 0
                for dashboard in self.resources.get('dashboards').values():
                    if dashboard.get('deprecationNotice'):
                        continue
                    if dashboard.get('category', 'Other') == category:
                        check = '✓' if dashboard.get('dashboardId') in self.qs.dashboards else ' '
                        dashboard_options[f" {check}[{dashboard.get('dashboardId')}] {dashboard.get('name')}"] = dashboard.get('dashboardId')
                        counter += 1
                if not counter: # remove empty categories
                    del dashboard_options[f'{category.upper()}']
            while True:
                dashboard_id = get_parameter(
                    param_name='dashboard-id',
                    message="Please select a dashboard to deploy",
                    choices=dashboard_options,
                )
                if dashboard_id == '[category]':
                    unset_parameter('dashboard-id')
                    continue
                break

        if not dashboard_id:
            print('No dashboard selected')
            return

        # Get selected dashboard definition
        dashboard_definition = self.get_definition("dashboard", id=dashboard_id)
        dashboard = None
        try:
            dashboard = self.qs.discover_dashboard(dashboardId=dashboard_id)
        except CidCritical:
            pass

        if not dashboard_definition:
            if isinstance(dashboard, Dashboard):
                dashboard_definition = dashboard.definition
            else:
                raise ValueError(f'Cannot find dashboard with id={dashboard_id} in resources file.')

        definition_dependency_datasets = dashboard_definition.get('dependsOn', {}).get('datasets', [])
        required_datasets_names = [dsname for dsname in definition_dependency_datasets]
        ds_map = definition_dependency_datasets if isinstance(definition_dependency_datasets, dict) else {}

        dashboard_datasets = dashboard.datasets if dashboard else {}

        for name, id in dashboard_datasets.items():
            if id not in self.qs.datasets:
                logger.info(f'Removing unknown dataset "{name}" ({id}) from dashboard {dashboard_id}')
                del dashboard_datasets[name]

        compatible = True
        if dashboard_definition.get('templateId'):
            # Get QuickSight template details
            try:
                source_template = self.qs.describe_template(
                    template_id=dashboard_definition.get('templateId'),
                    account_id=dashboard_definition.get('sourceAccountId'),
                    region=dashboard_definition.get('region', 'us-east-1')
                )
            except CidError as exc:
                raise CidCritical(exc) # Cannot proceed without a valid template
            dashboard_definition['sourceTemplate'] = source_template
            print(f'\nLatest template: {source_template.arn}/version/{source_template.version}')
            compatible = self.check_dashboard_version_compatibility(dashboard_id)
        elif dashboard_definition.get('data'):
            data = dashboard_definition.get('data')
            params = self.get_template_parameters(dashboard_definition.get('parameters', dict()))
            if isinstance(data, dict):
                #TODO: need to apply template to data structure as well
                data = yaml.safe_dump(data)
            if isinstance(data, str):
                data = Template(data).safe_substitute(params)
            dashboard_definition['definition'] = yaml.safe_load(data)
        elif dashboard_definition.get('file'):
            raise NotImplementedError('File option is not implemented')
        else:
            raise CidCritical('Definition of dashboard resource must contain data or template_id')


        if not recursive and compatible == False:
            if get_parameter(
                param_name=f'confirm-recursive',
                message=f'This is a major update and require recursive action. This could lead to the loss of dataset customization. Continue anyway?',
                choices=['yes', 'no'],
                default='yes') != 'yes':
                return
            logger.info("Switch to recursive mode")
            recursive = True

        if recursive:
            self.create_datasets(required_datasets_names, dashboard_datasets, recursive=recursive, update=update)

        # Find datasets for template or definition
        if not dashboard_definition.get('datasets'):
            dashboard_definition['datasets'] = {}

        for dataset_name in required_datasets_names:
            dataset = None
            # First try to find the dataset with the id
            try:
                dataset = self.qs.describe_dataset(id=dataset_name)
            except Exception as exc:
                logger.debug(f'Failed to describe_dataset {dataset_name} {exc}')

            if isinstance(dataset, Dataset):
                logger.debug(f'Found dataset {dataset_name} with id match = {dataset.arn}')
                dashboard_definition['datasets'][dataset_name] = dataset.arn

            else:
                # Then search dataset by name.
                # This is not ideal as there can be several with the same name,
                # but if dataset is created manually we cannot use id.
                matching_datasets = []
                for ds in self.qs.datasets.values():
                    if not isinstance(ds, Dataset) or ds.name != dataset_name:
                        continue
                    if dashboard_definition.get('templateId'):
                        # For templates we can additionally verify dataset fields
                        dataset_fields = {col.get('Name'): col.get('Type') for col in ds.columns}
                        src_fields = source_template.datasets.get(ds_map.get(dataset_name, dataset_name) )
                        required_fields = {col.get('Name'): col.get('DataType') for col in src_fields}
                        unmatched = {}
                        for k, v in required_fields.items():
                            if k not in dataset_fields or dataset_fields[k] != v:
                                unmatched.update({k: {'expected': v, 'found': dataset_fields.get(k)}})
                        logger.debug(f'unmatched_fields={unmatched}')
                        if unmatched:
                            logger.warning(f'Found Dataset "{dataset_name}" ({ds.id}) but it is missing required fields. {(unmatched)}')
                        else:
                            matching_datasets.append(ds)
                    else:
                        # for definitions datasets we do not have any possibility to check if dataset with a given name matches
                        matching_datasets.append(ds)

                if not matching_datasets:
                    reco = ''
                    logger.warning(f'Dataset {dataset_name} is not found')
                    if utils.exec_env()['shell'] == 'lambda':
                        # We are in lambda
                        reco = 'You can try deleting existing dataset and re-run.'
                    else:
                        # We are in command line mode
                        reco = 'Please retry with --update "yes" --force --recursive flags.'
                    raise CidCritical(f'Failed to find a Dataset "{dataset_name}" with required fields. ' + reco)
                elif len(matching_datasets) >= 1:
                    if len(matching_datasets) > 1:
                        # FIXME: propose a choice?
                        logger.warning(
                            f'Found {len(matching_datasets)} Datasets found with name "{dataset_name}":'
                            f' {str([ds.id for ds in matching_datasets])}'
                        )
                    ds = matching_datasets[0]
                    print(f'Using dataset {dataset_name}: {ds.id}')
                    dashboard_definition['datasets'][dataset_name] = ds.arn

        # Update datasets to the mapping name if needed
        # Dashboard definition must contain names that are specific to template.
        dashboard_definition['datasets'] = {ds_map.get(name, name): arn for name, arn in dashboard_definition['datasets'].items() }
        logger.debug(f"datasets: {dashboard_definition['datasets']}")

        _url = self.qs_url.format(dashboard_id=dashboard_id, **self.qs_url_params)

        dashboard = self.qs.describe_dashboard(DashboardId=dashboard_id)
        if isinstance(dashboard, Dashboard):
            if update:
                return self.update_dashboard(dashboard_id, dashboard_definition)
            else:
                print(f'Dashboard {dashboard_id} exists. See {_url}')
                return dashboard_id

        print(f'Deploying dashboard {dashboard_id}')
        try:
            dashboard = self.qs.create_dashboard(dashboard_definition)
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

        dashboard = self.qs.discover_dashboard(dashboardId=dashboard_id)

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
            dashboard = self.qs.discover_dashboard(dashboardId=dashboard_id)
        else:
            dashboard = self.qs.discover_dashboard(dashboardId=dashboard_id)

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
            datasets = self.qs.discover_dashboard(dashboardId=dashboard_id).datasets # save for later
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
                        logger.debug(f'Picking the first of dataset databases: {dataset.schemas}')
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
                if athena_datasource and not get_parameters().get('athena-workgroup'):
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
        """Delete unused resources (QuickSight datasets not used in Dashboards)"""

        self.qs.discover_dashboards()
        self.qs.discover_datasets()
        references = {}
        for dashboard in self.qs.dashboards.values():
            for dataset_id in dashboard.datasets.values():
                if dataset_id not in references:
                    references[dataset_id] = []
                references[dataset_id].append(dashboard.id)
        for dataset in self.qs._datasets.values():
            if dataset.id in references:
                cid_print(f'Dataset {dataset.name} ({dataset.id}) is in use ({", ".join(references[dataset.id])})')
                continue
            if get_yesno_parameter(f'confirm-delete-dataset-{dataset.id}',
                message=f'Delete dataset "{dataset.name}" (not used in dashboards, but can be used in analysis)?',
                default='no',
                ):
                logger.info(f'Deleting dataset {dataset.name} ({dataset.id})')
                self.qs.delete_dataset(dataset.id)
                cid_print(f'Deleted dataset {dataset.name} ({dataset.id})')

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

        dashboard = self.qs.discover_dashboard(dashboardId=dashboard_id)

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
                print('Fetching QuickSight users. Duration will scale with the number of users.')
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


    def check_dashboard_version_compatibility(self, dashboard_id):
        """ Returns True | False | None if could not check """
        try:
            dashboard = self.qs.discover_dashboard(dashboardId=dashboard_id)
        except CidCritical:
            dashboard = None
        if not dashboard:
            print(f'Dashboard "{dashboard_id}" is not deployed')
            return None
        if not isinstance(dashboard.deployedTemplate, CidQsTemplate):
            print(f'Dashboard "{dashboard_id}" does not have a versioned template')
            return None
        if not isinstance(dashboard.sourceTemplate, CidQsTemplate):
            print(f"Cannot access QuickSight source template for {dashboard_id}")
            return None
        try:
            cid_version = dashboard.deployedTemplate.cid_version
        except ValueError:
            logger.debug("The cid version of the deployed dashboard could not be retrieved")
            cid_version = "N/A"

        try:
            cid_version_latest = dashboard.sourceTemplate.cid_version
        except ValueError:
            logger.debug("The latest version of the dashboard could not be retrieved")
            cid_version_latest = "N/A"

        if dashboard.latest:
            cid_print("You are up to date!")
            cid_print(f"  Version    {cid_version}")
            cid_print(f"  VersionId  {dashboard.deployed_version} ")
        else:
            cid_print(f"An update is available:")
            cid_print("              Deployed -> Latest")
            cid_print(f"  Version    {str(cid_version): <9}   {str(cid_version_latest): <9}")
            cid_print(f"  VersionId  {str(dashboard.deployedTemplate.version): <9}   {dashboard.latest_version: <9}")

        # Check if version are compatible
        compatible = None
        try:
            compatible = dashboard.sourceTemplate.cid_version.compatible_versions(dashboard.deployedTemplate.cid_version)
        except ValueError as exc:
            logger.info(exc)

        return compatible

    def update_dashboard(self, dashboard_id, dashboard_definition):

        dashboard = self.qs.discover_dashboard(dashboardId=dashboard_id)
        if not dashboard:
            print(f'Dashboard "{dashboard_id}" is not deployed')
            return

        print(f'\nChecking for updates...')
        if isinstance(dashboard.deployedTemplate, CidQsTemplate):
            print(f'Deployed template: {dashboard.deployedTemplate.arn}')
        else:
            print(f'Deployed template: Not available')
        if isinstance(dashboard.sourceTemplate, CidQsTemplate):
            print(f"Latest template: {dashboard.sourceTemplate.arn}/version/{dashboard.latest_version}")
        else:
            print('Unable to determine dashboard source.')

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
        logger.debug(f"Updating {dashboard_id}")

        try:
            self.qs.update_dashboard(dashboard, dashboard_definition)
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
                    _found_dsc = self.qs.get_datasets(id=known_datasets.get(dataset_name))
                    if len(_found_dsc) != 1:
                        logger.warning(f'Found more than one dataset in known datasets with name {dataset_name} {len(_found_dsc)}. Taking the first one.')
                    dataset_id = _found_dsc[0].id
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
                    dataset_definition = self.get_definition(type='dataset', name=dataset_name, noparams=True)
                    raw_template = self.get_data_from_definition('dataset', dataset_definition)
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
                    if not dataset_definition:
                        raise Exception(f'Failed to find dataset {dataset_name}. Check if Datasets section in your resources file has that.')
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

    def get_data_from_definition(self, asset_type, definition):
        """ Returns an json object for json resource file and a text for all other definitions
        """
        subfolder = {
            'dataset': 'datasets',
            'view': 'queries',
            'table': 'queries',
        }.get(asset_type)
        data = None
        file_name = definition.get('File')
        if definition.get('Data'):
            data = definition.get('Data')
        elif definition.get('data'):
            data = definition.get('data')
        elif file_name:
            text = resource_string(
                definition.get('providedBy'), f'data/{subfolder}/{file_name}'
            ).decode('utf-8')
            if file_name.endswith('.json') or file_name.endswith('.jsn'):
                data = json.loads(text)
            else:
                data = text
        if data is None:
            raise CidCritical(f"Error: definition is broken. Cannot find data for {repr(definition)}. Check resources file.")
        return data

    def create_datasource(self, datasource_id) -> str:
        role_arn = get_parameters().get('quicksight-datasource-role-arn')
        if not role_arn:
            role_name = get_parameters().get('quicksight-datasource-role')
            if role_name:
                role_arn = f'arn:aws:iam::{self.base.account_id}:role/{role_name}'
        athena_datasource = self.qs.create_data_source(
            athena_workgroup=self.athena.WorkGroup,
            datasource_id=datasource_id,
            role_arn=role_arn
        )
        return athena_datasource



    def create_or_update_dataset(self, dataset_definition: dict, dataset_id: str=None,recursive: bool=True, update: bool=False) -> bool:
        # Read dataset definition from template
        data = self.get_data_from_definition('dataset', dataset_definition)
        template = Template(json.dumps(data))
        cur_required = dataset_definition.get('dependsOn', dict()).get('cur')
        athena_datasource = None

        # Manage datasource
        # We must do it here. In case if dastasource is not defined by user, we can take it from dataset

        datasource_id = get_parameters().get('quicksight-datasource-id')

        if datasource_id:
            # We have explicit choice of datasource
            try:
                athena_datasource = self.qs.describe_data_source(datasource_id)
            except self.qs.client.exceptions.ResourceNotFoundException:
                logger.info(f'DataSource {datasource_id} not found. Creating.')
                athena_datasource = self.create_datasource(datasource_id)
            except self.qs.client.exceptions.AccessDeniedException:
                logger.warning(f'AccessDenied reading QuickSight DataSource {datasource_id}. Trying to continue.')
                athena_datasource = Datasource(raw={
                    'AthenaParameters':{},
                    "Id": datasource_id,
                    "Arn": f"arn:aws:quicksight:{self.base.session.region_name}:{self.base.account_id}:datasource/{datasource_id}",
                })
            except Exception as exc:
                raise CidCritical(
                    f'quicksight-datasource-id={datasource_id} not found or not in a valid state.'
                ) from exc
        else:
                # We have no explicit DataSource in parameters
                # QuickSight DataSources are not obvious for customer so we will try to do our best guess
                # - if there is just one? -> silently take that one
                # - if DataSource is references in existing DataSet? -> silently take that one
                # - if athena WorkGroup defined -> Try to find a DataSource with this WorkGroup
                # - and if still nothing -> ask an explicit choice from the user
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
                    logger.debug(f'Related to dataset {dataset_name}: {[ds.id for ds in found_datasets]}')
                    if found_datasets:
                        schemas = list(set(sum([d.schemas for d in found_datasets], [])))
                        datasources = list(set(sum([d.datasources for d in found_datasets], [])))
                        logger.debug(f'Found following schemas={schemas}, related to dataset with name {dataset_name}')
                logger.info(f'Found {len(datasources)} Athena DataSources related to the DataSet {dataset_name}')

                if not get_parameters().get('athena-database') and len(schemas) == 1 and schemas[0]:
                    logger.debug(f'Picking the database={schemas[0]}')
                    self.athena.DatabaseName = schemas[0]
                # else user will be suggested to choose database anyway

                if len(datasources) == 1 and datasources[0] in self.qs.athena_datasources:
                    athena_datasource = self.qs.get_datasources(id=datasources[0])[0]
                    logger.info(f'Silently selecting the only available DataSources: {datasources[0]}.')
                else:
                    #try to find a datasource with defined workgroup
                    workgroup = self.athena.WorkGroup
                    datasources_with_workgroup = self.qs.get_datasources(
                        athena_workgroup_name=workgroup,
                    )
                    logger.info(f'Found {len(datasources_with_workgroup)} Athena DataSources with WorkGroup={workgroup}.')
                    if len(datasources_with_workgroup) == 1:
                        athena_datasource = datasources_with_workgroup[0]
                        logger.info(f'Silently selecting the only available option: {athena_datasource}.')
                    else:
                        #cannot find the right athena_datasource
                        datasource_choices = {
                            f"{datasource.name} {datasource.id} (workgroup={datasource.AthenaParameters.get('WorkGroup')})": datasource.id
                            for datasource in datasources_with_workgroup
                        }
                        datasource_choices['Create New DataSource'] = 'Create New DataSource'
                        datasource_id = get_parameter(
                            param_name='quicksight-datasource-id',
                            message=f"Please choose DataSource (Choose the first one if not sure).",
                            choices=datasource_choices,
                        )
                        if not datasource_id or datasource_id == 'Create New DataSource':
                            datasource_id = 'CID-CMD-Athena'
                            logger.info(f'Creating DataSource {datasource_id}')
                            athena_datasource = self.create_datasource(datasource_id)
                        else:
                            athena_datasource = self.qs.get_datasources(id=datasource_id)[0]
                        logger.info(f'Using  DataSource = {athena_datasource.id}')
        if not get_parameters().get('athena-workgroup'):
            # set default workgroup from datasource if not provided via parameters
            if isinstance(athena_datasource, Datasource) and athena_datasource.AthenaParameters.get('WorkGroup', None):
                self.athena.WorkGroup = athena_datasource.AthenaParameters.get('WorkGroup')
            else:
                logger.debug('Athena_datasource is not defined. Will only create views')

        # Check for required views
        _views = dataset_definition.get('dependsOn', {}).get('views', [])
        required_views = [(self.cur.table_name if cur_required and name =='${cur_table_name}' else name) for name in _views]

        self.athena.discover_views(required_views)
        found_views = utils.intersection(required_views, self.athena._metadata.keys())
        missing_views = utils.difference(required_views, found_views)

        if recursive:
            print(f"Detected views: {', '.join(found_views)}")
            for view_name in found_views:
                if cur_required and view_name == self.cur.table_name:
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
            'cur_table_name': self.cur.table_name if cur_required else None
        }

        logger.debug(f'dataset_id={dataset_id}')
        logger.debug(f'columns_tpl={columns_tpl}')

        columns_tpl = self.get_template_parameters(
            dataset_definition.get('parameters', dict()),
            f"dataset-{dataset_id or data.get('DataSetId')}-",
            columns_tpl,
        )
        logger.debug(columns_tpl)
        compiled_dataset_text = template.safe_substitute(columns_tpl)
        try:
            compiled_dataset = json.loads(compiled_dataset_text)
        except json.JSONDecodeError as exc:
            logger.error('The json of dataset is not correct. Please check parameters of the dasbhoard.')
            logger.debug(compiled_dataset_text)
            raise
        if dataset_id:
            compiled_dataset.update({'DataSetId': dataset_id})

        found_dataset = self.qs.describe_dataset(compiled_dataset.get('DataSetId'))
        if isinstance(found_dataset, Dataset):
            update_dataset = False
            if update:
                update_dataset = True
            elif found_dataset.name != compiled_dataset.get('Name'):
                print(f"Dataset found with name {found_dataset.name}, but {compiled_dataset.get('Name')} expected. Updating.")
                update_dataset = True
            if update_dataset and get_parameters().get('on-drift', 'show').lower() != 'override' and isatty() and not cur_required:
                while True:
                    diff = self.qs.dataset_diff(found_dataset.raw, compiled_dataset)
                    if diff and diff['diff']:
                        cid_print(f'<BOLD>Found a difference between existing dataset <YELLOW>{found_dataset.name}<END> <BOLD>and the one we want to deploy. <END>')
                        cid_print(diff['printable'])
                        choice = get_parameter(
                            param_name='dataset-' + found_dataset.name.lower().replace(' ', '-') + '-override',
                            message=f'The existing dataset is different. Override?',
                            choices=['retry diff', 'proceed and override', 'keep existing', 'exit'],
                            default='retry diff'
                        )
                        if choice == 'retry diff':
                            unset_parameter('dataset-' + found_dataset.name.lower().replace(' ', '-') + '-override')
                            continue
                        elif choice == 'proceed and override':
                            update_dataset = True
                            break
                        elif choice == 'keep existing':
                            update_dataset = False
                            break
                        else:
                            raise CidCritical(f'User choice is not to update {found_dataset.name}.')
                    elif not diff:
                        if get_parameter(
                            param_name=found_dataset.name.lower().replace(' ', '-') + '-override',
                            message=f'Cannot get sql diff for {found_dataset.name}. Continue?',
                            choices=['override', 'exit'],
                            default='override'
                            ) != 'override':
                            raise CidCritical(f'User choice is not to update {found_dataset.name}.')
                        update_dataset = True
                    break
            if update_dataset:
                self.qs.update_dataset(compiled_dataset)
                if compiled_dataset.get("ImportMode") == "SPICE":
                    dataset_id = compiled_dataset.get('DataSetId')
                    schedules_definitions = []
                    for schedule_name in dataset_definition.get('schedules', []):
                        schedules_definitions.append(self.get_definition("schedule", name=schedule_name))
                        self.qs.ensure_dataset_refresh_schedule(dataset_id, schedules_definitions)
            else:
                print(f'No update requested for dataset {compiled_dataset.get("DataSetId")} {compiled_dataset.get("Name")}={found_dataset.name} ')
        else:
            dataset_id = self.qs.create_dataset(compiled_dataset)
            if dataset_id and compiled_dataset.get("ImportMode") == "SPICE":
                schedules_definitions = []
                for schedule_name in dataset_definition.get('schedules', []):
                    schedules_definitions.append(self.get_definition("schedule", name=schedule_name))
                    self.qs.ensure_dataset_refresh_schedule(dataset_id, schedules_definitions)
        return True


    def create_or_update_view(self, view_name: str, recursive: bool=True, update: bool=False) -> None:
        # Avoid checking a views multiple times in one cid session
        if view_name in self._visited_views:
            return
        self._visited_views.append(view_name)
        logger.info(f'Processing view: {view_name}')

        # For account mappings create a view using a special helper
        if view_name in ['account_map', 'aws_accounts']:
            if view_name in self.athena._metadata.keys():
                print(f'Account map {view_name} exists. Skipping.')
            else:
                self.accountMap.create(view_name) #FIXME: add or_update
            return

        # Create a view
        logger.info(f'Getting view definition {view_name}')
        view_definition = self.get_definition("view", name=view_name)
        if not view_definition and view_name in self.athena._metadata.keys():
            logger.info(f"Definition is unavailable but view exists: {view_name}, skipping")
            return
        if not view_definition:
            logger.info(f"Definition is unavailable {view_name}")
            return
        logger.debug(f'View definition: {view_definition}')
        dependencies = view_definition.get('dependsOn', {})

        # Process CUR columns
        if isinstance(dependencies.get('cur'), list):
            for column in dependencies.get('cur'):
                self.cur.ensure_column(column)
        elif isinstance(dependencies.get('cur'), dict):
            for column, column_type in dependencies.get('cur').items():
                self.cur.ensure_column(column, column_type)

        if recursive:
            dependency_views = dependencies.get('views', [])
            if 'cur' in dependency_views:
                dependency_views.remove('cur')
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
                    if 'CREATE EXTERNAL TABLE' in view_query.upper():
                        logger.warning('Cannot recreate table {view_name}')

                    elif 'CREATE OR REPLACE' in view_query.upper():
                        update_view = False
                        while get_parameters().get('on-drift', 'show').lower() != 'override' and isatty():
                            cid_print(f'Analysing view {view_name}')
                            diff = self.athena.get_view_diff(view_name, view_query)
                            if diff and diff['diff']:
                                cid_print(f'<BOLD>Found a difference between existing view <YELLOW>{view_name}<END> <BOLD>and the one we want to deploy. <END>')
                                cid_print(diff['printable'])
                                choice = get_parameter(
                                    param_name='view-' + view_name + '-override',
                                    message=f'The existing view is different. Override?',
                                    choices=['retry diff', 'proceed and override', 'keep existing', 'exit'],
                                    default='retry diff'
                                )
                                if choice == 'retry diff':
                                    unset_parameter('view-' + view_name + '-override')
                                    continue
                                elif choice == 'proceed and override':
                                    update_view = True
                                    break
                                elif choice == 'keep existing':
                                    update_view = False
                                    break
                                else:
                                    raise CidCritical(f'User choice is not to update {view_name}.')
                            elif not diff:
                                if not get_yesno_parameter(
                                    param_name='view-' + view_name + '-override',
                                    message=f'Cannot get sql diff for {view_name}. Continue?',
                                    default='yes'
                                    ):
                                    raise CidCritical(f'User choice is not to update {view_name}.')
                                update_view = True
                            break
                        if update_view:
                            print(f'Updating view: "{view_name}"')
                            self.athena.execute_query(view_query)
                    else:
                        print(f'View "{view_name}" is not compatible with update. Skipping.')
                if 'CREATE OR REPLACE VIEW' in view_query.upper() or 'CREATE VIEW' in view_query.upper():
                    logger.debug('Start waiting')
                    assert self.athena.wait_for_view(view_name), f"Failed to update a view {view_name}"
                    logger.info(f'View "{view_name}" updated')
            else:
                return
        else: # No found -> creation
            logger.info(f'Creating view: "{view_name}"')
            if view_definition.get('type') == 'Glue_Table':
                self.glue.create_or_update_table(view_name, view_query)
                logger.info(f'Table "{view_name}" created')
            elif 'CREATE EXTERNAL TABLE' in view_query.upper():
                print(f'Creating table: "{view_name}"')
                try:
                    self.athena.execute_query(view_query)
                except CidCritical as exc:
                    logger.exception(exc)
                    pass
            else:
                self.athena.execute_query(view_query)
                assert self.athena.wait_for_view(view_name), f"Failed to create a view {view_name}"
                logger.info(f'View "{view_name}" created')


    def get_view_query(self, view_name: str) -> str:
        """ Returns a fully compiled AHQ """
        # View path
        view_definition = self.get_definition("view", name=view_name)
        cur_required = view_definition.get('dependsOn', dict()).get('cur')
        if cur_required and self.cur.has_savings_plans and self.cur.has_reservations and view_definition.get('spriFile'):
            view_definition['File'] = view_definition.get('spriFile')
        elif cur_required and self.cur.has_savings_plans and view_definition.get('spFile'):
            view_definition['File'] = view_definition.get('spFile')
        elif cur_required and self.cur.has_reservations and view_definition.get('riFile'):
            view_definition['File'] = view_definition.get('riFile')
        elif view_definition.get('File') or view_definition.get('Data') or view_definition.get('data'):
            pass
        else:
            logger.critical(f'\nCannot find view {view_name}. View information is incorrect, please check resources.yaml')
            raise Exception(f'\nCannot find view {view_name}')

        # Load TPL file
        data = self.get_data_from_definition('view', view_definition)
        if isinstance(data, dict):
            template = Template(json.dumps(data))
        else:
            template = Template(data)

        # Prepare template parameters
        columns_tpl = {
            'cur_table_name': self.cur.table_name if cur_required else None,
            'athenaTableName': view_name,
            'athena_database_name': self.athena.DatabaseName,
        }

        columns_tpl = self.get_template_parameters(
            view_definition.get('parameters', dict()),
            f'view-{view_name}-',
            columns_tpl,
        )
        logger.debug(f"Rendering template for {view_name}")
        logger.debug(str(columns_tpl))
        columns_tpl = {key: str(value) for key, value in columns_tpl.items()}
        compiled_query = template.safe_substitute(columns_tpl)

        return compiled_query

    @command
    def csv2view(self, **kwargs):
        """CSV 2 SQL"""
        input_file = get_parameter('input', message='Enter csv filename')
        file_name = os.path.splitext(os.path.split(input_file)[-1])[0]
        name = get_parameter('name', message='Enter view name', default=file_name)
        csv2view(input_file, name)

    @command
    def map(self, **kwargs):
        """Create account mapping Athena views"""
        for v in ['account_map', 'aws_accounts']:
            self.accountMap.create(v)

    @command
    def initqs(self, **kwargs):
        """ Initialize QuickSight resources for deployment """
        return InitQsCommand(cid=self, **kwargs).execute()
