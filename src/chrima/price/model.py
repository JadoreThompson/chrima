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
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("workspaces.id", ondelete="CASCADE", name="fk_prices_merchant_id"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("products.id", ondelete="CASCADE", name="fk_prices_product_id"),
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
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)


class PriceToken(Base):
    __tablename__ = "price_tokens"

    price_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("prices.id", ondelete="CASCADE", name="fk_price_tokens_price_id"),
        primary_key=True,
    )
    token_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("tokens.id", name="fk_price_tokens_token_id"),
        primary_key=True,
    )
