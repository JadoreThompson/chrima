import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, datetime_column
from util import get_datetime
from .enums import EventStatus


class EventOutbox(Base):
    __tablename__ = "event_outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), nullable=False, primary_key=True
    )
    type: Mapped[str] = mapped_column(sa.String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[EventStatus] = mapped_column(sa.String, nullable=False)
    timestamp: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
