import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, uuid_pk, datetime_column


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "workspaces.id",
            ondelete="CASCADE",
            name="fk_wallets_workspace_id",
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    wallet_address: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()


class WalletTokens(Base):
    __tablename__ = "wallet_tokens"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "wallets.id",
            ondelete="CASCADE",
            name="fk_wallet_tokens_wallet_id",
        ),
        primary_key=True,
    )
    token_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("tokens.id", name="fk_wallet_tokens_token_id"),
        primary_key=True,
    )
