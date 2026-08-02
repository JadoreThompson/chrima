import click
from infra.db import write_db_url_alembic_ini


@click.group(name="alembic")
def alembic():
    pass


@alembic.command(name="write")
def write_alembic_file():
    write_db_url_alembic_ini()
