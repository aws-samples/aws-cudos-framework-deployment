import click

from cid.common import Cid
from cid.tracker import track

from cid._version import __version__

version = f'{__version__} Beta'
prog_name="CLOUD INTELLIGENCE DASHBOARDS (CID) CLI"
print(f'{prog_name} {version}\n')
analitycs_data = dict()

@click.group()
@click.option('--profile_name', help='AWS Profile name to use', default=None)
@click.option('--region_name', help="AWS Region (default:'us-east-1')", default=None)
@click.option('--aws_access_key_id', help='', default=None)
@click.option('--aws_secret_access_key', help='', default=None)
@click.option('--aws_session_token', help='', default=None)
@click.option('-v', '--verbose', count=True)
@click.pass_context
def main(ctx, **kwargs):
    params = {
        'verbose': kwargs.pop('verbose'),
    }
    App = Cid(**params)
    App.run(**kwargs)
    ctx.obj = App
    if click.get_current_context().invoked_subcommand:
        analitycs_data.update( {
            'dashboard_id': None,
            'account_id': App.awsIdentity.get('Account'),
            'operation': click.get_current_context().invoked_subcommand,
        })

@main.command()
@click.pass_obj
def map(App):
    """Create account mapping"""
    App.map()


@main.command()
@click.pass_obj
def deploy(App):
    """Deploy Dashboard"""

    id = App.deploy()
    analitycs_data['dashboard_id'] = id
    track(**analitycs_data)


@main.command()
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.pass_obj
def status(App, **kwargs):
    """Show Dashboard status"""

    App.status(dashboard_id=kwargs.get('dashboard_id'))

@main.command()
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.pass_obj
def delete(App, **kwargs):
    """Delete Dashboard"""

    id = App.delete(dashboard_id=kwargs.get('dashboard_id'))
    analitycs_data['dashboard_id'] = id
    track(**analitycs_data)

@main.command()
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.option('--force', help='Allow force update', is_flag=True)
@click.pass_obj
def update(App, **kwargs):
    """Update Dashboard"""

    id = App.update(dashboard_id=kwargs.get('dashboard_id'), force=kwargs.get('force'))
    analitycs_data['dashboard_id'] = id
    track(**analitycs_data)


@main.command()
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.pass_obj
def open(App, **kwargs):
    """Open Dashboard in browser"""

    App.open(dashboard_id=kwargs.get('dashboard_id'))


@main.command()
@click.pass_obj
def cleanup(App: Cid):
    """Delete unused resources (QuickSight datasets, Athena views)"""
    
    App.cleanup()


if __name__ == '__main__':
    main()
