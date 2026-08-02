from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infra.db import Base, uuid_pk, datetime_column
from util import get_datetime
from .enums import BillingProvider, BillingStatus


class Billing(Base):
    __tablename__ = "billing"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True
    )
    subscription_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    billing_provider: Mapped[BillingProvider] = mapped_column(sa.String, nullable=False)
    """Payment provider used for this user's billing (e.g. stripe)."""
    customer_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    """Customer id of the user on the billing provider."""
    status: Mapped[BillingStatus] = mapped_column(
        sa.String, nullable=False, default=BillingStatus.ACTIVE.value
    )
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)

    __table_args__ = (
        sa.UniqueConstraint(
            "billing_provider",
            "subscription_id",
            name="uq_billing_provider_subscription",
        ),
    )


class BillingWebhookEvent(Base):
    __tablename__ = "billing_webhook_events"

    provider: Mapped[BillingProvider] = mapped_column(sa.String, primary_key=True)
    event_id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    type: Mapped[str] = mapped_column(sa.String, nullable=False)
    processed_at: Mapped[datetime] = datetime_column()
