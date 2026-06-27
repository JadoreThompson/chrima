from urllib.parse import quote

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from config import (
    POSTGRES_HOST,
    POSTGRES_DB_NAME,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USERNAME,
)

db_password = quote(POSTGRES_PASSWORD)
DB_ENGINE = create_async_engine(
    f"postgresql+asyncpg://{POSTGRES_USERNAME}:{db_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB_NAME}"
)
DB_ENGINE_SYNC = create_engine(
    f"postgresql+psycopg2://{POSTGRES_USERNAME}:{db_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB_NAME}"
)
