from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from infra.db import Base, uuid_pk, datetime_column
from util import get_datetime
from .enums import TransactionStatus


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = uuid_pk()
    product_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "products.id", ondelete="CASCADE", name="fk_transactions_product_id"
        ),
        nullable=False,
    )
    price_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("prices.id", ondelete="CASCADE", name="fk_transactions_price_id"),
        nullable=False,
    )
    platform_user_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    "User id on the specific group platform (discord, telegram, etc.) of the sender"
    sender: Mapped[str] = mapped_column(sa.String, nullable=False)
    "Sender's wallet address"
    recipient: Mapped[str] = mapped_column(sa.String, nullable=False)
    address: Mapped[str] = mapped_column(sa.String, nullable=False)
    amount: Mapped[float] = mapped_column(sa.Float, nullable=False)
    "Amount in price's currency paid"
    status: Mapped[TransactionStatus] = mapped_column(sa.String, nullable=False)
    timestamp: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class EthBlocks(Base):
    __tablename__ = "eth_blocks"

    id: Mapped[uuid.UUID] = uuid_pk()
    address: Mapped[str] = mapped_column(sa.String, nullable=False)
    "Contract address the filter is scoped to"
    topics: Mapped[list] = mapped_column(JSONB, nullable=False)
    "Event topics the filter is scoped to"
    from_block: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    "Lowest block number of the range persisted before polling"
    to_block: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    "Highest block number of the range persisted before polling"
    completed: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
