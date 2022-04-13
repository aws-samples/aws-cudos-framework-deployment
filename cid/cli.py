import logging

import click

from cid.common import Cid
from cid.utils import get_parameters, set_parameters
from cid._version import __version__

logger = logging.getLogger(__name__)
version = f'{__version__} Beta'
prog_name="CLOUD INTELLIGENCE DASHBOARDS (CID) CLI"
print(f'{prog_name} {version}\n')


def cid_command(func):
    def wrapper(ctx, **kwargs):
        # Complete kwargs with other parameters
        if len(ctx.args) % 2 != 0:
            print(f"Unknown extra argument, or an option without value {ctx.args}")
            exit(-1)
        for i in range(0, len(ctx.args), 2):
            kwargs[ctx.args[i][2:].replace('-', '_')] = ctx.args[i+1]
        set_parameters(kwargs)
        res = func(ctx, **kwargs)
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
@click.option('--profile_name', help='AWS Profile name to use', default=None)
@click.option('--region_name', help="AWS Region (default:'us-east-1')", default=None)
@click.option('--aws_access_key_id', help='', default=None)
@click.option('--aws_secret_access_key', help='', default=None)
@click.option('--aws_session_token', help='', default=None)
@click.option('-v', '--verbose', count=True)
@click.pass_context
def main(ctx, **kwargs):

    app = Cid(
        verbose = kwargs.get('verbose')
    )

    app.run(
        profile_name=kwargs.get('profile_name', None),
        region_name=kwargs.get('region_name', None),
        aws_access_key_id=kwargs.get('aws_access_key_id', None),
        aws_secret_access_key=kwargs.get('aws_secret_access_key', None),
        aws_session_token=kwargs.get('aws_session_token', None)
    )
    ctx.obj = app


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


@cid_command
def deploy(ctx, **kwargs):
    """Deploy Dashboard
    
    \b
    Command options:
     --dashboard-id TEXT                   QuickSight dashboard id (cudos, cost_intelligence_dashboard, kpi_dashboard, ta-organizational-view, trends-dashboard etc)
     --athena-database TEXT                Athena database
     --glue-data-catalog TEXT              Glue data catalog
     --cur-table-name TEXT                 CUR table name
     --quicksight-user TEXT                QuickSight user
     --dataset-{dataset_name}-id TEXT      QuickSight dataset id for a specific dataset
     --view-{view_name}-{parameter} TEXT   a custom parameter for a view creation, can use variable: {account_id}
     --account-map-source TEXT             csv, dummy, organization (if autodiscovery impossible)
     --account-map-file TEXT               csv file path relative to current directory (if autodiscovery impossible and csv selected as a source )
    """
    ctx.obj.deploy(**kwargs)


@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@cid_command
def status(ctx, dashboard_id):
    """Show Dashboard status"""
    ctx.obj.status(dashboard_id)


@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@cid_command
def delete(ctx, dashboard_id):
    """Delete Dashboard"""
    ctx.obj.delete(dashboard_id)


@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.option('--force/--noforce', help='Allow force update', default=False)
@cid_command
def update(ctx, dashboard_id, force):
    """Update Dashboard"""
    ctx.obj.update(dashboard_id, force=force)


@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@cid_command
def open(ctx, dashboard_id):
    """Open Dashboard in browser"""
    ctx.obj.open(dashboard_id)


@cid_command
def cleanup(ctx):
    """Delete unused resources (QuickSight datasets, Athena views)"""
    ctx.obj.cleanup()


@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.option('--share-method', help='Sharing method', default=None, type=click.Choice(['folder', 'user']))
@click.option('--folder-method', help='Folder to use', default=None, type=click.Choice(['new', 'existing']))
@click.option('--folder-id', help='QuickSight folder id (existing)', default=None)
@click.option('--folder-name', help='QuickSight folder name (new)', default=None)
@click.option('--quicksight-user', help='QuickSight user', default=None)
@cid_command
def share(ctx, dashboard_id, **kwargs):
    """Share QuickSight resources (Dashboard, Datasets, DataSource)"""
    
    ctx.obj.share(dashboard_id)

if __name__ == '__main__':
    main()
