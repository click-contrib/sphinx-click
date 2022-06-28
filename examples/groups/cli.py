# file: cli.py
import click


@click.group()
@click.option(
    '--debug',
    default=False,
    is_flag=True,
    help="Output more information about what's going on.",
)
def cli():
    """A sample command group."""
    pass


@cli.command()
@click.option('--param', envvar='PARAM', help='A sample option')
@click.option('--another', metavar='[FOO]', help='Another option')
def hello():
    """A sample command."""
    pass
