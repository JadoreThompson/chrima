import configparser
import os
import shutil
from urllib.parse import quote

from sqlalchemy import UUID, DateTime
from sqlalchemy.orm import mapped_column

from config import (
    POSTGRES_HOST,
    POSTGRES_NAME,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USERNAME,
    PROJECT_PATH,
)
from util import get_uuid, get_datetime


def uuid_pk(**kw):
    """Helper function for UUID primary key columns."""
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=get_uuid, **kw)


def datetime_column(**kw):
    """Helper function for timezone-aware datetime columns."""
    if "nullable" not in kw:
        kw["nullable"] = False

    return mapped_column(DateTime(timezone=True), default=get_datetime, **kw)


def write_db_url_alembic_ini():
    db_password = quote(POSTGRES_PASSWORD).replace("%", "%%")
    db_url = f"postgresql+psycopg2://{POSTGRES_USERNAME}:{db_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_NAME}"

    config = configparser.ConfigParser()
    fp = os.path.join(PROJECT_PATH, "alembic.ini")
    example_fp = os.path.join(PROJECT_PATH, "alembic.ini.example")

    if not os.path.exists(fp):
        shutil.copyfile(example_fp, fp)

    config.read(fp)
    config["alembic"]["sqlalchemy.url"] = db_url

    with open(fp, "w") as f:
        config.write(f)
