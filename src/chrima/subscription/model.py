from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, uuid_pk, datetime_column
from util import get_datetime
from .enums import SubscriptionStatus


class SubscriptionBalance(Base):
    __tablename__ = "subscription_balances"

    id: Mapped[UUID] = uuid_pk()
    platform_group_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    platform_user_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    product_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("products.id", ondelete="CASCADE", name="fk_subscription_balances_product_id"),
        nullable=False,
    )
    credit_amount: Mapped[float] = mapped_column(sa.Float, nullable=False)
    cycle_start: Mapped[int] = mapped_column(sa.Integer, nullable=True)
    cycle_end: Mapped[int] = mapped_column(sa.Integer, nullable=True)
    status: Mapped[SubscriptionStatus] = mapped_column(sa.String, nullable=False)
    last_processed_tx: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("transactions.id", name="fk_subscription_balances_last_processed_tx"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)

    __table_args__ = (
        sa.UniqueConstraint("platform_group_id", "platform_user_id", "product_id", name="uq_subscription_balances_group_user_product"),
    )
