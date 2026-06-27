import click

from .command import seed


@click.group()
def cli():
    pass


cli.add_command(seed)
