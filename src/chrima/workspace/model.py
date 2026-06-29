import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from chrima.message_platform.enums import MessagePlatform
from core.db import Base, uuid_pk, datetime_column
from util import get_datetime


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_workspaces_user_id"),
    )
    platform: Mapped[MessagePlatform] = mapped_column(sa.String, nullable=False)
    external_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    """Id of the server (discord), group (telegram)"""
    notification_channel_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    """This is where we send subscription notifications (complete, trail period over, etc.)"""
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()
    updated_at: Mapped[datetime] = datetime_column(onupdate=get_datetime)


class WorkspaceWallet(Base):
    __tablename__ = "workspace_wallets"

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "workspaces.id",
            ondelete="CASCADE",
            name="fk_workspace_wallets_workspace_id",
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    wallet_address: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_at: Mapped[datetime] = datetime_column()


class WorkspaceWalletTokens(Base):
    __tablename__ = "workspace_wallet_tokens"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "workspace_wallets.id",
            ondelete="CASCADE",
            name="fk_workspace_wallet_tokens_wallet_id",
        ),
        primary_key=True,
    )
    token_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("tokens.id", name="fk_workspace_wallet_tokens_token_id"),
        primary_key=True,
    )
