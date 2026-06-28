from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, datetime_column, uuid_pk
from util import get_datetime
from .enums import AccessType, GroupType


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = uuid_pk()
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("merchants.id", ondelete="CASCADE", name="fk_products_merchant_id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    description: Mapped[str] = mapped_column(sa.String(256), nullable=True)
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("merchant_wallets.id", name="fk_products_wallet_id"),
        nullable=False,
    )
    price_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("prices.id", name="fk_products_price_id"),
        nullable=True,
    )
    group_type: Mapped[GroupType] = mapped_column(sa.String, nullable=False)
    group_url: Mapped[str] = mapped_column(sa.String, nullable=True)
    group_id: Mapped[str] = mapped_column(sa.String, nullable=True)
    roles: Mapped[list[str]] = mapped_column(sa.JSON, nullable=True)
    access_type: Mapped[AccessType] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
