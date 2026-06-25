from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, uuid_pk, datetime_column
from util import get_datetime


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(nullable=False)
    wallet_address: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
