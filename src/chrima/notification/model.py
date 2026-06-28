import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, datetime_column
from util import get_datetime, get_uuid
from .channel import NotificationChannelType
from .enums import NotificationStatus, NotificationType


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=get_uuid
    )
    recipient: Mapped[str] = mapped_column(sa.String, nullable=False)
    type: Mapped[NotificationType] = mapped_column(sa.String, nullable=False)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    channel_type: Mapped[NotificationChannelType] = mapped_column(sa.String, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        sa.String, nullable=False, default=NotificationStatus.PENDING
    )
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
