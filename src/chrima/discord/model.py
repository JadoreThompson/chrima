from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base
from core.db.util import datetime_column
from util import get_datetime


class DiscordAccessToken(Base):
    __tablename__ = "discord_access_tokens"

    user_id: Mapped[int] = mapped_column(
        sa.BigInteger, nullable=False, primary_key=True
    )
    oauth_payload: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
