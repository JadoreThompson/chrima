from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, datetime_column, uuid_pk
from util import get_datetime
from .enums import Currency, PriceType, RecurringInterval


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[uuid.UUID] = uuid_pk()
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[PriceType] = mapped_column(sa.String, nullable=False)
    currency: Mapped[Currency] = mapped_column(sa.String, nullable=False)
    amount: Mapped[float] = mapped_column(sa.Float, nullable=False)
    recurring_interval: Mapped[RecurringInterval] = mapped_column(
        sa.String, nullable=True
    )
    recurring_interval_count: Mapped[int] = mapped_column(sa.Integer, nullable=True)
    trial_period_days: Mapped[int] = mapped_column(sa.Integer, nullable=True)
    active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
