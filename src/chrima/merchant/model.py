import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, uuid_pk, datetime_column
from util import get_datetime


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    wallet_address: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)


class MerchantWallet(Base):
    __tablename__ = "merchant_wallets"

    id: Mapped[uuid.UUID] = uuid_pk()
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    wallet_address: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()


class MerchantWalletTokens(Base):
    __tablename__ = "merchant_wallet_tokens"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("merchant_wallets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    token_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("tokens.id"),
        primary_key=True,
    )
