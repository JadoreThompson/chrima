import click
from .command import db, notification, orchestrator, seed, transaction


@click.group()
def cli():
    pass


cli.add_command(db)
cli.add_command(notification)
cli.add_command(orchestrator)
cli.add_command(seed)
cli.add_command(transaction)
