import logging
import click
from os import environ as env

from cid import Cid

logger = logging.getLogger(__name__)

version = '1.0 Beta'
prog_name="CLOUD INTELLIGENCE DASHBOARDS (CID) CLI"
print(f'{prog_name} {version}\n')

App = Cid()

@click.group()
@click.option('--profile_name', help='AWS Profile name to use', default=env.get('AWS_PROFILE'))
@click.option('--region_name', help="AWS Region (default:'us-east-1')", default=env.get('AWS_REGION', env.get('AWS_DEFAULT_REGION', 'us-east-1')))
@click.option('--aws_access_key_id', help='', default=env.get('AWS_ACCESS_KEY_ID'))
@click.option('--aws_secret_access_key', help='', default=env.get('AWS_SECRET_ACCESS_KEY'))
@click.option('--aws_session_token', help='', default=env.get('AWS_SESSION_TOKEN'))
@click.option('-v', '--verbose', count=True)
@click.pass_context
def main(ctx, **kwargs):
    logger.setLevel(logger.getEffectiveLevel()-10*kwargs.pop('verbose'))
    App.run(**kwargs)


@main.command()
def map():
    """Create account mapping"""
    App.map()


@main.command()
def deploy():
    """Deploy Dashboard"""

    App.deploy()


@main.command()
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
def status(**kwargs):
    """Show Dashboard status"""

    App.status(dashboard_id=kwargs.get('dashboard_id'))

@main.command()
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
def delete(**kwargs):
    """Delete Dashboard"""

    App.delete(dashboard_id=kwargs.get('dashboard_id'))

@main.command()
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.option('--force', help='Allow force update', is_flag=True)
def update(**kwargs):
    """Update Dashboard"""

    App.update(dashboard_id=kwargs.get('dashboard_id'), force=kwargs.get('force'))


@main.command()
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
def open(**kwargs):
    """Open Dashboard in browser"""

    App.open(dashboard_id=kwargs.get('dashboard_id'))


if __name__ == '__main__':
    main()
