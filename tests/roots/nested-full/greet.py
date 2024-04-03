"""The greet example taken from the README."""

import click


@click.group()
def greet():
    """A sample command group."""
    pass


@greet.command()
@click.argument('user', envvar='USER')
def hello(user):
    """Greet a user."""
    click.echo('Hello %s' % user)


@greet.group()
def world():
    """Greet the world."""
    click.echo('Hello world!')


@world.command()
def peace():
    """Greet the world peace."""
    click.echo('Hello world peace!')


@world.command()
def traveler():
    """Greet a globetrotter."""
    click.echo('Hello world traveler!')


@world.group()
def wide():
    """Greet all world wide things."""
    click.echo('Hello world wide ...!')


@wide.command()
def web():
    """Greet the internet."""
    click.echo('Hello world wide web!')
