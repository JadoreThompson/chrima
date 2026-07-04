import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, uuid_pk
from core.db.util import datetime_column
from util import get_datetime


class DiscordAccessToken(Base):
    __tablename__ = "discord_access_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, unique=True)
    """
    Discord user ID of the user who owns this access token.
    We use bigint because Discord user IDs are 64-bit integers.
    """
    oauth_payload: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
