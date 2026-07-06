import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from chrima.message_platform.enums import MessagePlatformType
from core.db import Base, uuid_pk, datetime_column
from util import get_datetime


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_workspaces_user_id"),
    )
    platform: Mapped[MessagePlatformType] = mapped_column(sa.String, nullable=False)
    external_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    """Id of the server (discord), group (telegram)"""
    notification_channel_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    """This is where we send subscription notifications (complete, trail period over, etc.)"""
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
