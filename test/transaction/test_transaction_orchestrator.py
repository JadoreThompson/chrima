from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from chrima.discord import DiscordMembershipService, DiscordService
from chrima.notification import NotificationPublisher
from chrima.notification.enums import NotificationType
from chrima.price.enums import Currency, PriceType
from chrima.product.enums import FulfilmentType
from chrima.product.exception import ProductNotFoundException
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.transaction.event import TransactionCompletedEventV2
from chrima.transaction.service import TransactionOrchestrator
from chrima.workspace.enums import MessagePlatformType
from core.db import get_db_session


@pytest.fixture
def mock_discord_service():
    mock = AsyncMock(spec=DiscordService)
    mock.get_access_token.return_value = "mock_token"
    return mock


@pytest.fixture
def mock_discord_membership_service():
    return AsyncMock(spec=DiscordMembershipService)


@pytest.fixture
def mock_notification_publisher():
    return AsyncMock(spec=NotificationPublisher)


@pytest.fixture
def setup_scenario(
    user_service,
    workspace_service,
    workspace_wallet_service,
    product_service,
    token_service,
    price_service,
    faker,
):
    async def _setup(
        price_amount: float = 10.0,
        fulfilment_type: FulfilmentType = FulfilmentType.ROLE,
        roles: list[str] | None = None,
    ):
        if roles is None:
            roles = ["123456789012345678"]
        async with get_db_session() as db_sess:
            owner = await user_service.create(
                username=faker.user_name(),
                email=faker.email(),
                password=faker.password(),
                db_sess=db_sess,
            )
            workspace = await workspace_service.create(
                user_id=owner.id,
                name=faker.user_name() + "-ws",
                platform=MessagePlatformType.DISCORD,
                external_id=str(uuid4().int)[:18],
                notification_channel_id="ch_test",
                db_sess=db_sess,
            )
            token = await token_service.create(
                name="TST",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xtoken",
                db_sess=db_sess,
            )
            wallet = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="main",
                wallet_address="0xwallet",
                token_ids=[token.id],
                db_sess=db_sess,
            )
            product = await product_service.create(
                workspace_id=workspace.id,
                name="test-product",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=roles,
                fulfilment_type=fulfilment_type,
                db_sess=db_sess,
            )
            price = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=price_amount,
                db_sess=db_sess,
            )
            await db_sess.commit()
            return workspace, product, price.id

    return _setup


@pytest.fixture
def make_event():
    def _make(amount: int = 5, product_id=None, price_id=None, group_user_id="67890"):
        return TransactionCompletedEventV2(
            transaction_id=uuid4(),
            product_id=product_id or uuid4(),
            price_id=price_id or uuid4(),
            group_user_id=group_user_id,
            amount=amount,
        )

    return _make


def _orchestrator(
    mock_oauth,
    mock_membership,
    mock_notification,
    product_service,
    price_service,
    workspace_service,
):
    return TransactionOrchestrator(
        discord_service=mock_oauth,
        discord_membership_service=mock_membership,
        product_service=product_service,
        price_service=price_service,
        workspace_service=workspace_service,
        deserialiser=None,
        notification_publisher=mock_notification,
    )


@pytest.mark.asyncio(loop_scope="session")
class TestHandleTransactionCompleted:

    async def test_raises_on_nonexistent_product(
        self,
        mock_discord_service,
        mock_discord_membership_service,
        mock_notification_publisher,
        product_service,
        price_service,
        workspace_service,
        make_event,
        create_drop_tables,
    ):
        orch = _orchestrator(
            mock_discord_service,
            mock_discord_membership_service,
            mock_notification_publisher,
            product_service,
            price_service,
            workspace_service,
        )
        event = make_event(product_id=uuid4())
        async with get_db_session() as db_sess:
            with pytest.raises(ProductNotFoundException):
                await orch.handle_transaction_completed(event, db_sess)
        assert mock_notification_publisher.publish.call_count == 0
        assert mock_discord_membership_service.assign_roles.call_count == 0
        assert mock_discord_membership_service.add_user_to_guild.call_count == 0
        assert mock_discord_service.get_access_token.call_count == 0

    async def test_raises_on_nonexistent_price(
        self,
        mock_discord_service,
        mock_discord_membership_service,
        mock_notification_publisher,
        product_service,
        price_service,
        workspace_service,
        setup_scenario,
        make_event,
        create_drop_tables,
    ):
        user, product, price_id = await setup_scenario()
        orch = _orchestrator(
            mock_discord_service,
            mock_discord_membership_service,
            mock_notification_publisher,
            product_service,
            price_service,
            workspace_service,
        )
        event = make_event(product_id=product.id)
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await orch.handle_transaction_completed(event, db_sess)
        assert mock_notification_publisher.publish.call_count == 0
        assert mock_discord_membership_service.assign_roles.call_count == 0
        assert mock_discord_membership_service.add_user_to_guild.call_count == 0
        assert mock_discord_service.get_access_token.call_count == 0

    async def test_invite_fulfilment(
        self,
        mock_discord_service,
        mock_discord_membership_service,
        mock_notification_publisher,
        product_service,
        price_service,
        workspace_service,
        setup_scenario,
        make_event,
        create_drop_tables,
    ):
        user, product, price_id = await setup_scenario(
            price_amount=10.0,
            fulfilment_type=FulfilmentType.INVITE,
        )
        orch = _orchestrator(
            mock_discord_service,
            mock_discord_membership_service,
            mock_notification_publisher,
            product_service,
            price_service,
            workspace_service,
        )
        event = make_event(product_id=product.id, price_id=price_id)

        async with get_db_session() as db_sess:
            await orch.handle_transaction_completed(event, db_sess)

        assert mock_discord_service.get_access_token.call_count == 1
        assert mock_discord_membership_service.add_user_to_guild.call_count == 1
        assert (
            mock_discord_membership_service.add_user_to_guild.call_args[1][
                "access_token"
            ]
            == "mock_token"
        )
        assert mock_discord_membership_service.assign_roles.call_count == 0
        assert mock_notification_publisher.publish.call_count == 1
        assert (
            mock_notification_publisher.publish.call_args[1]["type"]
            == NotificationType.SUBSCRIPTION_SUFFICIENT
        )

    async def test_role_fulfilment(
        self,
        mock_discord_service,
        mock_discord_membership_service,
        mock_notification_publisher,
        product_service,
        price_service,
        workspace_service,
        setup_scenario,
        make_event,
        create_drop_tables,
    ):
        user, product, price_id = await setup_scenario(
            price_amount=10.0,
            fulfilment_type=FulfilmentType.ROLE,
            roles=["111111111111111111", "222222222222222222"],
        )
        orch = _orchestrator(
            mock_discord_service,
            mock_discord_membership_service,
            mock_notification_publisher,
            product_service,
            price_service,
            workspace_service,
        )
        event = make_event(
            product_id=product.id,
            price_id=price_id,
            group_user_id="954075156215635998",
        )

        async with get_db_session() as db_sess:
            await orch.handle_transaction_completed(event, db_sess)

        assert mock_discord_membership_service.assign_roles.call_count == 1
        assert mock_discord_membership_service.add_user_to_guild.call_count == 0
        assert mock_discord_service.get_access_token.call_count == 0

        assign_kw = mock_discord_membership_service.assign_roles.call_args[1]
        assert assign_kw["roles"] == [111111111111111111, 222222222222222222]
        assert assign_kw["user_id"] == 954075156215635998

        assert mock_notification_publisher.publish.call_count == 1
        notif_kw = mock_notification_publisher.publish.call_args[1]
        assert notif_kw["type"] == NotificationType.SUBSCRIPTION_SUFFICIENT

        ctx = notif_kw["context"]
        assert ctx.platform_user_id == event.group_user_id
        assert ctx.product_id == product.id
        assert ctx.product_name == product.name
        assert ctx.product_price == 10.0
        assert ctx.remaining_amount == 10.0
        assert ctx.transaction_id == event.transaction_id
