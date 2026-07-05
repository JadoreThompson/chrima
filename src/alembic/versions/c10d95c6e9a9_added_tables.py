"""Added tables

Revision ID: c10d95c6e9a9
Revises:
Create Date: 2026-06-29 12:33:58.753092

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c10d95c6e9a9"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_outbox",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("timestamp", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "notification_channels",
        sa.Column("notification_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("retries", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.Integer(), nullable=True),
        sa.Column("last_attempted_at", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("notification_id", "type"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("recipient", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("standard", sa.String(), nullable=False),
        sa.Column("chain", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("jwt_token", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_table(
        "workspaces",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("notification_channel_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_workspaces_user_id", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "workspace_wallets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("wallet_address", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_workspace_wallets_workspace_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "prices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("merchant_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("recurring_interval", sa.String(), nullable=True),
        sa.Column("recurring_interval_count", sa.Integer(), nullable=True),
        sa.Column("trial_period_days", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(length=256), nullable=True),
        sa.Column("wallet_id", sa.UUID(), nullable=False),
        sa.Column("fulfilment_type", sa.String(), nullable=False),
        sa.Column("external_url", sa.String(), nullable=True),
        sa.Column("roles", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["wallet_id"],
            ["workspace_wallets.id"],
            name="fk_products_wallet_id",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_products_workspace_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "workspace_wallet_tokens",
        sa.Column("wallet_id", sa.UUID(), nullable=False),
        sa.Column("token_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["token_id"], ["tokens.id"], name="fk_workspace_wallet_tokens_token_id"
        ),
        sa.ForeignKeyConstraint(
            ["wallet_id"],
            ["workspace_wallets.id"],
            name="fk_workspace_wallet_tokens_wallet_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("wallet_id", "token_id"),
    )
    op.create_table(
        "price_tokens",
        sa.Column("price_id", sa.UUID(), nullable=False),
        sa.Column("token_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["price_id"],
            ["prices.id"],
            name="fk_price_tokens_price_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["token_id"], ["tokens.id"], name="fk_price_tokens_token_id"
        ),
        sa.PrimaryKeyConstraint("price_id", "token_id"),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("price_id", sa.UUID(), nullable=False),
        sa.Column("platform_user_id", sa.String(), nullable=False),
        sa.Column("sender", sa.String(), nullable=False),
        sa.Column("recipient", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("timestamp", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["price_id"],
            ["prices.id"],
            name="fk_transactions_price_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_transactions_product_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "subscription_balances",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("platform_user_id", sa.String(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("credit_amount", sa.Float(), nullable=False),
        sa.Column("cycle_start", sa.Integer(), nullable=True),
        sa.Column("cycle_end", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_processed_tx", sa.UUID(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_notified_at", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["last_processed_tx"],
            ["transactions.id"],
            name="fk_subscription_balances_last_processed_tx",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_subscription_balances_product_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "external_id",
            "platform_user_id",
            "product_id",
            name="uq_subscription_balances_group_user_product",
        ),
    )
    op.create_foreign_key(
        "fk_prices_merchant_id",
        "prices", "workspaces",
        ["merchant_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_prices_product_id",
        "prices", "products",
        ["product_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_notification_channels_notification_id",
        "notification_channels", "notifications",
        ["notification_id"], ["id"],
        ondelete="CASCADE",
    )



def downgrade() -> None:
    op.drop_table("subscription_balances")
    op.drop_table("transactions")
    op.drop_table("price_tokens")
    op.drop_table("workspace_wallet_tokens")
    op.drop_table("products")
    op.drop_table("prices")
    op.drop_table("workspace_wallets")
    op.drop_table("workspaces")
    op.drop_table("notification_channels")
    op.drop_table("notifications")
    op.drop_table("event_outbox")
    op.drop_table("tokens")
    op.drop_table("users")
