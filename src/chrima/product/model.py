from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, datetime_column, uuid_pk
from util import get_datetime
from .enums import FulfilmentType


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "workspaces.id", ondelete="CASCADE", name="fk_products_workspace_id"
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    description: Mapped[str] = mapped_column(sa.String(256), nullable=True)
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("wallets.id", name="fk_products_wallet_id"),
        nullable=False,
    )
    fulfilment_type: Mapped[FulfilmentType] = mapped_column(sa.String, nullable=False)
    external_url: Mapped[str] = mapped_column(sa.String, nullable=True)
    roles: Mapped[list[str]] = mapped_column(sa.JSON, nullable=True)
    """A list of role ids associated with the product."""
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)
