from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infra.db import Base, datetime_column
from util import get_datetime


class DiscordAccessToken(Base):
    """Stores OAuth tokens for product subscribers/purchasers (customers).

    Keyed by Discord user ID (snowflake). A customer is identified solely by
    their Discord snowflake — they have no Chrima user account UUID. There is
    at most one row per Discord user so the same person buying multiple
    products shares the same token row.
    """

    __tablename__ = "discord_access_tokens"

    user_id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    payload: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)


class UserDiscordAccessToken(Base):
    """Stores OAuth tokens for workspace owners (Chrima users).

    Keyed by the Chrima user UUID (1:1 with the users table). This is a
    standalone table holding the full encrypted token — NOT a bridge to
    DiscordAccessToken. This separation means a workspace owner can also be
    a customer without conflicting with DiscordAccessToken's unique constraint
    on Discord user ID: the owner's token lives here, the customer's token
    (if any) lives in DiscordAccessToken with a different row per purchase
    flow.
    """

    __tablename__ = "user_discord_access_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    discord_user_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    payload: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
