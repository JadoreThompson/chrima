import asyncio

import click
from chrima.seeder import DbSeeder


@click.group("seed")
def seed():
    pass


@seed.command(name="run")
def seed_run():
    seeder = DbSeeder()
    asyncio.run(seeder.run())
