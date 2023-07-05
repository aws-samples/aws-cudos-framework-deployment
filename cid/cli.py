import logging

import click

from cid.common import Cid
from cid.utils import get_parameters, set_parameters, get_latest_tool_version
from cid._version import __version__
from cid.exceptions import CidCritical, CidError

logger = logging.getLogger(__name__)
version = f'{__version__} Beta'
latest_version = get_latest_tool_version()
prog_name="CLOUD INTELLIGENCE DASHBOARDS (CID) CLI"
print(f'{prog_name} {version}\n')

if __version__ != latest_version and latest_version != 'UNDEFINED':
    
    print('\033[93mUPDATE AVAILABLE\033[0m')
    print(f'\033[93mA new version {latest_version} is available, please consider update cid-cmd package via pip\033[0m\n\n')
    logger.info(f'A new version {latest_version} is available, please consider update cid-cmd package via pip')

def cid_command(func):
    def wrapper(ctx, **kwargs):
        # Complete kwargs with other parameters
        if len(ctx.args) % 2 != 0:
            print(f"Unknown extra argument, or an option without value {ctx.args}")
            exit(-1)
        for i in range(0, len(ctx.args), 2):
            kwargs[ctx.args[i][2:].replace('-', '_')] = ctx.args[i+1]

        set_parameters(kwargs, all_yes=ctx.obj.all_yes)
        res = None
        try:
            res = func(ctx, **kwargs)
        except CidCritical as exc:
            logger.debug(exc, exc_info=True)
            logger.critical(exc)
        except CidError as exc:
            logger.debug(exc, exc_info=True)
            logger.error(exc)
        params = get_parameters()
        logger.info('Next time you can use following command:')
        logger.info('   cid-cmd ' + ctx.info_name
            + ''.join([f" --{k.replace('_','-')}" for k, v in ctx.params.items() if isinstance(v, bool) and v])
            + ''.join([f" --{k.replace('_','-')} '{v}'" for k, v in ctx.params.items() if not isinstance(v, bool) and v is not None])
            + ''.join([f" --{k} '{v}' " for k, v in params.items() if not isinstance(v, bool) and v is not None])
        )
        return res
    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__
    return main.command(
        context_settings=dict(
            ignore_unknown_options=True,
            allow_extra_args=True,
        )
    )(click.pass_context(wrapper))


@click.group()
@click.option('--profile_name', '--profile', help='AWS Profile name to use', default=None)
@click.option('--region_name', help="AWS Region (default:'us-east-1')", default=None)
@click.option('--aws_access_key_id', help='', default=None)
@click.option('--aws_secret_access_key', help='', default=None)
@click.option('--aws_session_token', help='', default=None)
@click.option('--log_filename', help='log file name', default='cid.log')
@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@click.pass_context
def main(ctx, **kwargs):
    ctx.obj = Cid(**kwargs)


@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@cid_command
def map(ctx, **kwargs):
    """Create account mapping

    \b
    Command options:
     --cur-table-name TEXT                 CUR table name
     --athena-database TEXT                Athena database
     --glue-data-catalog TEXT              Glue data catalog
     --account-map-source TEXT             csv, dummy, organization (if autodiscovery impossible)
     --account-map-file TEXT               csv file path relative to current directory (if autodiscovery impossible and csv selected as a source )
    """
    ctx.obj.map(**kwargs)


@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@cid_command
def csv2view(ctx, **kwargs):
    """Create account sql code from CSV file

    \b
    Command options:
     --input                         csv file
     --name                          Athena View name
    """
    ctx.obj.csv2view(**kwargs)


@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@click.option('--share-with-account', help='Share dashboard with all users in the current account', is_flag=True, default=None)
@click.option('--quicksight-delete-failed-datasource', help='Delete datasoruce if creation failed', is_flag=True, default=None)
@cid_command
def deploy(ctx, **kwargs):
    """Deploy Dashboard
    
    \b
    Command options:
     --dashboard-id TEXT                   QuickSight dashboard id (cudos, cost_intelligence_dashboard, kpi_dashboard, ta-organizational-view, trends-dashboard etc)
     --athena-database TEXT                Athena database
     --athena-workgroup TEXT               Athena workgroup
     --glue-data-catalog TEXT              Glue data catalog
     --cur-table-name TEXT                 CUR table name
     --quicksight-datasource-id TEXT       QuickSight Datasource ARN (if not found one with provided Athena workgroup)
     --quicksight-user TEXT                QuickSight user
     --dataset-{dataset_name}-id TEXT      QuickSight dataset id for a specific dataset
     --view-{view_name}-{parameter} TEXT   a custom parameter for a view creation, can use variable: {account_id}
     --account-map-source TEXT             csv, dummy, organization (if autodiscovery impossible)
     --account-map-file TEXT               csv file path relative to current directory (if autodiscovery impossible and csv selected as a source )
     --on-drift (show|override)            Action if a drift of view and dataset is discovered. 'override' = override drift(will destroy customization) or 'show' (default) = show a diff. In Unattended mode (without terminal on-drift will have allways override behaviour)
     --update (yes|no)                     Update if some elements are already installed. Default = 'no'
     --resources TEXT                      CID resources yaml file or url
    """
    ctx.obj.deploy(**kwargs)


@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@cid_command
def export(ctx, **kwargs):
    """Expot Dashboard
    
    \b
    Command options:
        --analysis-name              Analysis you want to share (not needed if analysis-id is provided).
        --analysis-id                ID of analysis you want to share (open analysis in browser and copy id from url)
        --template-id                Template Id
        --dashboard-id               Target Dashboard Id
        --template-version           Version description vX.Y.Z
        --reader-account             Account id with whom you want to share with or *
        --dashboard-export-method
               (definition|template) A method (definition=pull json definition of Analysis OR template=create QuickSught Teamplate)
        --export-known-datasets
            (no|yes)                 If 'yes' the export will include DataSets that are already in resources file. Default = no
        --output                     A filename (.yaml)
    """
    ctx.obj.export(**kwargs)


@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@cid_command
def status(ctx, dashboard_id, **kwargs):
    """Show Dashboard status"""
    ctx.obj.status(dashboard_id, **kwargs)


@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@cid_command
def delete(ctx, dashboard_id, **kwargs):
    """Delete Dashboard and all dependencies unused by other CID-managed dasboards
    (including QuickSight datasets, Athena views and tables)

    \b
    Command options:
     --dashboard-id TEXT                   QuickSight dashboard id (cudos, cost_intelligence_dashboard, kpi_dashboard, ta-organizational-view, trends-dashboard etc)
     --athena-database TEXT                Athena database
     """
    ctx.obj.delete(dashboard_id, **kwargs)


@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.option('--force/--noforce', help='allow selecting  up to date dashboards (flags must be before options)', default=False)
@click.option('--recursive/--norecursive', help='Recursive update all Datasets and Views (flags must be before options)', default=False)
@cid_command
def update(ctx, dashboard_id, force, recursive, **kwargs):
    """Update Dashboard

    \b

     --on-drift (show|override)            Action if a drift of view and dataset is discovered. 'override' = override drift(will destroy customization) or 'show' (default) = show a diff. In Unattended mode (without terminal on-drift will have allways override behaviour)

    """
    ctx.obj.update(dashboard_id, force=force, recursive=recursive, **kwargs)


@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@cid_command
def open(ctx, dashboard_id, **kwargs):
    """Open Dashboard in browser"""
    ctx.obj.open(dashboard_id, **kwargs)


@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@cid_command
def cleanup(ctx, **kwargs):
    """Delete unused resources (QuickSight datasets, Athena views)"""
    ctx.obj.cleanup(**kwargs)


@click.option('-v', '--verbose', count=True)
@click.option('-y', '--yes', help='confirm all', is_flag=True, default=False)
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.option('--share-method', help='Sharing method', default=None, type=click.Choice(['folder', 'user', 'account']))
@click.option('--folder-method', help='Folder to use', default=None, type=click.Choice(['new', 'existing']))
@click.option('--folder-id', help='QuickSight folder id (existing)', default=None)
@click.option('--folder-name', help='QuickSight folder name (new)', default=None)
@click.option('--quicksight-user', help='QuickSight user', default=None)
@cid_command
def share(ctx, dashboard_id, **kwargs):
    """Share QuickSight resources (Dashboard, Datasets, DataSource)"""
    
    ctx.obj.share(dashboard_id)

@cid_command
def initqs(ctx, **kwargs):
    """Initialize QuickSight resources for deployment"""

    ctx.obj.initqs(**kwargs)

if __name__ == '__main__':
    main()
