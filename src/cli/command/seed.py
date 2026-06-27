import asyncio

import click
from chrima.seeder import DbSeeder


@click.command(name="seed")
def seed():
    seeder = DbSeeder()
    asyncio.run(seeder.run())
