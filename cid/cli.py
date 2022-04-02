import click

from cid.common import Cid
from cid.utils import params

from cid._version import __version__

version = f'{__version__} Beta'
prog_name="CLOUD INTELLIGENCE DASHBOARDS (CID) CLI"
print(f'{prog_name} {version}\n')

command_params = dict(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)

def update_params(ctx):
    if len(ctx.args) % 2 != 0:
        print(f"Unknown extra argument, or an option without value {ctx.args}")
        exit(-1)
    for i in range(0, len(ctx.args), 2):
        params [ctx.args[i][2:]] = ctx.args[i+1]

@click.group()
@click.option('--profile_name', help='AWS Profile name to use', default=None)
@click.option('--region_name', help="AWS Region (default:'us-east-1')", default=None)
@click.option('--aws_access_key_id', help='', default=None)
@click.option('--aws_secret_access_key', help='', default=None)
@click.option('--aws_session_token', help='', default=None)
@click.option('-v', '--verbose', count=True)
@click.pass_context
def main(ctx, **kwargs):

    if len(ctx.args) % 2 != 0:
        print(f"Unknown extra argument, or an option without value {ctx.args}")
        exit(-1)
    for i in range(0, len(ctx.args), 2):
        params [ctx.args[i][2:]] = ctx.args[i+1]
    App = Cid(
        verbose = kwargs.get('verbose')
    )

    App.run(
        profile_name=kwargs.get('profile_name', None),
        region_name=kwargs.get('region_name', None),
        aws_access_key_id=kwargs.get('aws_access_key_id', None),
        aws_secret_access_key=kwargs.get('aws_secret_access_key', None),
        aws_session_token=kwargs.get('aws_session_token', None)
    )
    ctx.obj = App


@main.command(**command_params)
@click.pass_context
def map(ctx):
    """Create account mapping"""
    update_params(ctx)
    app = ctx.obj
    app.map()


@main.command(**command_params)
@click.pass_context
def deploy(ctx):
    """Deploy Dashboard"""
    update_params(ctx)
    app = ctx.obj
    app.deploy()


@main.command(**command_params)
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.pass_context
def status(ctx, **kwargs):
    """Show Dashboard status"""
    update_params(ctx)
    app = ctx.obj
    app.status(dashboard_id=kwargs.get('dashboard_id'))


@main.command(**command_params)
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.pass_context
def delete(ctx, **kwargs):
    """Delete Dashboard"""
    update_params(ctx)
    app = ctx.obj
    app.delete(dashboard_id=kwargs.get('dashboard_id'))


@main.command(**command_params)
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.option('--force', help='Allow force update', is_flag=True)
@click.pass_context
def update(ctx, **kwargs):
    """Update Dashboard"""
    update_params(ctx)
    app = ctx.obj
    app.update(dashboard_id=kwargs.get('dashboard_id'), force=kwargs.get('force'))


@main.command(**command_params)
@click.option('--dashboard-id', help='QuickSight dashboard id', default=None)
@click.pass_context
def open(ctx, **kwargs):
    """Open Dashboard in browser"""
    update_params(ctx)
    app = ctx.obj
    app.open(dashboard_id=kwargs.get('dashboard_id'))


@main.command(**command_params)
@click.pass_context
def cleanup(ctx: Cid):
    """Delete unused resources (QuickSight datasets, Athena views)"""
    update_params(ctx)
    app = ctx.obj
    app.cleanup()


if __name__ == '__main__':
    main()
