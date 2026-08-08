import click
from .command import (
    alembic,
    db,
    discord,
    event_bus,
    notification,
    price,
    product,
    seed,
    subscription,
    transaction,
)


@click.group()
def cli():
    pass


cli.add_command(alembic)
cli.add_command(db)
cli.add_command(discord)
cli.add_command(event_bus)
cli.add_command(notification)
cli.add_command(price)
cli.add_command(product)
cli.add_command(seed)
cli.add_command(subscription)
cli.add_command(transaction)