import asyncio
import pytest

from chrima.message_platform.enums import MessagePlatformType
from chrima.notification.enums import NotificationType
from chrima.notification.schema import SubscriptionExpiringNotificationContext
from chrima.price.enums import Currency, PriceType, RecurringInterval
from chrima.product.schema import ProductResponse
from chrima.product.enums import FulfilmentType
from chrima.product.schema import CreatePriceRequest
from chrima.subscription.enums import SubscriptionStatus
from chrima.subscription.schema import SubscriptionBalanceResponse
from chrima.subscription.service.expiry_checker import SubscriptionExpiryChecker
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.workspace.schema import WorkspaceResponse
from core.db import get_db_session
from util import get_datetime


@pytest.fixture
def subscription_expiry_checker(
    product_service, workspace_service, notification_publisher
):
    return SubscriptionExpiryChecker(
        product_service=product_service,
        workspace_service=workspace_service,
        notification_publisher=notification_publisher,
    )


@pytest.fixture
def create_subscription_balance(
    subscription_expiry_checker,
    subscription_balance_service,
    user_service,
    workspace_service,
    workspace_wallet_service,
    product_service,
    token_service,
    faker,
):
    async def _func(
        key: str,
        product: ProductResponse | None = None,
        workspace: WorkspaceResponse | None = None,
        **kw,
    ):
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username=faker.user_name(),
                email=faker.email(),
                password=faker.password(),
                db_sess=db_sess,
            )

            workspace = workspace or await workspace_service.create(
                user_id=user.id,
                name=f"{user.username}-workspace",
                platform=MessagePlatformType.DISCORD,
                external_id=f"dis_{key}",
                notification_channel_id=f"ntf_{key}",
                db_sess=db_sess,
            )

            token = await token_service.create(
                name="TEST-TOKEN",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xsomething",
                db_sess=db_sess,
            )

            wallet = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name=f"wal_{key}",
                wallet_address="0xsomething",
                token_ids=[token.id],
                db_sess=db_sess,
            )

            product = product or await product_service.create(
                workspace_id=workspace.id,
                name=f"prd_{key}",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=["premium"],
                fulfilment_type=FulfilmentType.ROLE,
                price_data=CreatePriceRequest(
                    type=PriceType.RECURRING,
                    currency=Currency.USD,
                    amount=1.0,
                    recurring_interval=RecurringInterval.MONTH,
                    recurring_interval_count=1,
                ),
                db_sess=db_sess,
            )

            now = int(get_datetime().timestamp())

            params = {
                "external_id": f"ext_{key}",
                "platform_user_id": f"usr_{key}",
                "product_id": product.id,
                "credit_amount": 0.0,
                "status": SubscriptionStatus.ACTIVE,
                "cycle_start": now - 6000,
                "cycle_end": now + subscription_expiry_checker.expiry_window,
                "last_processed_tx": None,
                "db_sess": db_sess,
            }

            params.update(kw)

            sub_balance = await subscription_balance_service.create(**params)

            await db_sess.commit()

            return sub_balance

    return _func


def _assert_notification(
    kw,
    workspace: WorkspaceResponse,
    product: ProductResponse,
    sub_balance: SubscriptionBalanceResponse,
):
    assert kw["type"] == NotificationType.SUBSCRIPTION_EXPIRING

    ctx = kw["context"]
    assert isinstance(ctx, SubscriptionExpiringNotificationContext)
    assert ctx.guild_id == workspace.external_id
    assert ctx.channel_id == workspace.notification_channel_id
    assert ctx.product_id == product.id
    assert ctx.cycle_end == sub_balance.cycle_end


@pytest.mark.asyncio(loop_scope="session")
async def test_expires_subscription(
    subscription_expiry_checker,
    subscription_balance_service,
    workspace_service,
    product_service,
    notification_publisher,
    create_subscription_balance,
    create_drop_tables,
):
    """
    Tests that subscription which is soon to expire is actually recognised
    as expiring. We check that the necessary notification is being emitted
    """
    sub_balance = await create_subscription_balance(key="123")

    async with get_db_session() as db_sess:
        product = await product_service.get_by_id(sub_balance.product_id, db_sess)
        workspace = await workspace_service.get_by_id(product.workspace_id, db_sess)

    await subscription_expiry_checker.check_expirations()

    notification_publisher.publish.assert_called_once()

    _, kw = notification_publisher.publish.call_args
    _assert_notification(kw, workspace, product, sub_balance)

    async with get_db_session() as db_sess:
        sub_balance = await subscription_balance_service.get_by_id(
            sub_balance.id, db_sess
        )

    assert sub_balance.attempt_count == 1
    assert sub_balance.last_notified_at is not None


@pytest.mark.asyncio(loop_scope="session")
async def test_doesnt_expire_subscription(
    subscription_expiry_checker,
    subscription_balance_service,
    notification_publisher,
    create_subscription_balance,
    create_drop_tables,
):
    """
    Tests that subscription which isn't gong to expire soon isn't actioned
    """
    sub_balance = await create_subscription_balance(
        key="123", cycle_end=int(get_datetime().timestamp()) + 48 * 3600
    )

    await subscription_expiry_checker.check_expirations()

    assert notification_publisher.publish.call_count == 0

    async with get_db_session() as db_sess:
        sub_balance = await subscription_balance_service.get_by_id(
            sub_balance.id, db_sess
        )

    assert sub_balance.attempt_count == 0
    assert sub_balance.last_notified_at is None


@pytest.mark.asyncio(loop_scope="session")
async def test_respects_max_attempts(
    subscription_expiry_checker,
    subscription_balance_service,
    product_service,
    workspace_service,
    notification_publisher,
    create_subscription_balance,
    create_drop_tables,
):
    """
    Tests that subscription which isn't gong to expire soon isn't actioned
    """
    subscription_expiry_checker.interval = 5
    subscription_expiry_checker.notification_cooldown = 1

    sub_balance = await create_subscription_balance(
        key="123", cycle_end=int(get_datetime().timestamp()) + 4
    )

    async with get_db_session() as db_sess:
        product = await product_service.get_by_id(sub_balance.product_id, db_sess)
        workspace = await workspace_service.get_by_id(product.workspace_id, db_sess)

    try:
        await asyncio.wait_for(
            subscription_expiry_checker.run(),
            timeout=subscription_expiry_checker.interval * 4,
        )
    except asyncio.TimeoutError:
        pass

    assert notification_publisher.publish.call_count == 2

    async with get_db_session() as db_sess:
        sub_balance = await subscription_balance_service.get_by_id(
            sub_balance.id, db_sess
        )

    assert sub_balance.attempt_count == 2
    assert sub_balance.last_notified_at is not None
    assert sub_balance.status == SubscriptionStatus.EXPIRED
