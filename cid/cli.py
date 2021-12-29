import logging
import click
from os import environ as env

from cid import Cid

logger = logging.getLogger('cid')
# create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s')
# File handler logs everything down to DEBUG level
fh = logging.FileHandler('cid.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
# Console handler logs everything down to ERROR level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
ch.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)

version = '1.0 Beta'
prog_name="CLOUD INTELLIGENCE DASHBOARDS (CID) CLI"
print(f'{prog_name} {version}\n')

App = None

@click.group()
@click.option('--profile_name', help='AWS Profile name to use', default=env.get('AWS_PROFILE'))
@click.option('--region_name', help="AWS Region (default:'us-east-1')", default=env.get('AWS_REGION', env.get('AWS_DEFAULT_REGION', 'us-east-1')))
@click.option('--aws_access_key_id', help='', default=env.get('AWS_ACCESS_KEY_ID'))
@click.option('--aws_secret_access_key', help='', default=env.get('AWS_SECRET_ACCESS_KEY'))
@click.option('--aws_session_token', help='', default=env.get('AWS_SESSION_TOKEN'))
@click.option('-v', '--verbose', count=True)
@click.pass_context
def main(ctx, **kwargs):
    global App
    _verbose = kwargs.pop('verbose')
    if _verbose:
        # Limit Logging level to DEBUG, base level is WARNING
        _verbose = 2 if _verbose > 2 else _verbose
        logger.setLevel(logger.getEffectiveLevel()-10*_verbose)
        # Logging application start here due to logging configuration
        logger.info(f'{prog_name} {version} starting')
        print(f'Logging level set to: {logging.getLevelName(logger.getEffectiveLevel())}')
    App = Cid()
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
