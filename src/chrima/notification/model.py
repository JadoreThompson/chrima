import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)

    channels: Mapped[list["NotificationChannel"]] = relationship(
        "NotificationChannel", back_populates="notification"
    )


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    notification_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("notifications.id", ondelete="CASCADE"),
        primary_key=True,
    )
    type: Mapped[NotificationChannelType] = mapped_column(
        sa.String, primary_key=True, nullable=False
    )
    status: Mapped[NotificationStatus] = mapped_column(
        sa.String, nullable=False, default=NotificationStatus.PENDING
    )
    retries: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=sa.text("0")
    )
    max_retries: Mapped[int] = mapped_column(sa.Integer, nullable=True)
    expires_at: Mapped[int] = mapped_column(sa.Integer, nullable=True)
    last_attempted_at: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    notification: Mapped[Notification] = relationship(
        "Notification", back_populates="channels"
    )
