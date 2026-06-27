import click

from .command import seed, transaction


@click.group()
def cli():
    pass


cli.add_command(seed)
cli.add_command(transaction)
