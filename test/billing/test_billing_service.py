from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from chrima.billing import BillingService
from chrima.billing.enums import BillingProvider, BillingStatus
from chrima.billing.event import BillingEventType
from chrima.billing.exception import (
    BillingAlreadyCancelledException,
    BillingNotFoundException,
)
from chrima.billing.model import Billing
from chrima.billing.provider import BillingProvider as BillingProviderProtocol
from chrima.billing.schema import CheckoutSession
from chrima.event_bus.model import EventOutbox
from chrima.notification import NotificationPublisher
from chrima.notification.enums import NotificationType
from chrima.user.enums import Tier
from chrima.user.model import User
from infra.db import get_db_session


@pytest.fixture
def mock_billing_provider():
    return AsyncMock(spec=BillingProviderProtocol)


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def mock_notification_publisher():
    return AsyncMock(spec=NotificationPublisher)


@pytest.fixture
def billing_service(
    user_service,
    event_publisher,
    mock_billing_provider,
    mock_notification_publisher,
    mock_redis,
):
    return BillingService(
        billing_provider=mock_billing_provider,
        user_service=user_service,
        event_publisher=event_publisher,
        notification_publisher=mock_notification_publisher,
        redis_client=mock_redis,
    )


async def _create_user(user_service, db_sess, **kw):
    params = {
        "username": f"user_{uuid4().hex[:8]}",
        "email": f"{uuid4().hex[:8]}@example.com",
        "password": "secure_pass_123",
    }
    params.update(kw)
    return await user_service.create(**params, db_sess=db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestCreateCheckoutSession:
    async def test_creates_checkout_session(
        self, billing_service, user_service, mock_billing_provider, mock_redis, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)
            mock_billing_provider.create_checkout_session.return_value = CheckoutSession(
                id="cs_123", url="https://checkout.stripe.com/pay/cs_123"
            )

            response = await billing_service.create_checkout_session(
                user.id, Tier.PRO, db_sess
            )

            assert response.url == "https://checkout.stripe.com/pay/cs_123"
            mock_billing_provider.create_checkout_session.assert_awaited_once_with(
                Tier.PRO, metadata={"user_id": str(user.id)}
            )
            mock_redis.set.assert_awaited_once_with(
                f"checkout_session:cs_123", str(user.id)
            )

    async def test_free_tier_raises(
        self, billing_service, user_service, mock_billing_provider, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)

            with pytest.raises(ValueError):
                await billing_service.create_checkout_session(user.id, Tier.FREE, db_sess)

            mock_billing_provider.create_checkout_session.assert_not_called()

    async def test_nonexistent_user_raises(
        self, billing_service, mock_billing_provider, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await billing_service.create_checkout_session(uuid4(), Tier.PRO, db_sess)

            mock_billing_provider.create_checkout_session.assert_not_called()


@pytest.mark.asyncio(loop_scope="session")
class TestActivateSubscription:
    async def test_activates_subscription(
        self,
        billing_service,
        user_service,
        mock_notification_publisher,
        create_drop_tables,
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)

            response = await billing_service.activate_subscription(
                user_id=user.id,
                subscription_id="sub_123",
                customer_id="cus_123",
                billing_provider=BillingProvider.STRIPE,
                db_sess=db_sess,
            )

            assert response.status == BillingStatus.ACTIVE
            assert response.subscription_id == "sub_123"
            assert response.customer_id == "cus_123"
            assert response.billing_provider == BillingProvider.STRIPE

            row = await db_sess.get(Billing, response.id)
            assert row is not None
            assert row.status == BillingStatus.ACTIVE

            user_row = await db_sess.get(User, user.id)
            assert user_row.tier == Tier.PRO

            events = (await db_sess.execute(select(EventOutbox))).scalars().all()
            assert len(events) == 1
            assert events[0].type == BillingEventType.SUBSCRIPTION_ACTIVATED

            mock_notification_publisher.publish.assert_awaited_once()
            assert (
                mock_notification_publisher.publish.call_args.kwargs["type"]
                == NotificationType.BILLING_SUBSCRIPTION_ACTIVATED
            )

    async def test_upgrades_existing_billing(
        self,
        billing_service,
        user_service,
        create_drop_tables,
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)
            billing = Billing(
                user_id=user.id,
                subscription_id="sub_old",
                billing_provider=BillingProvider.STRIPE,
                customer_id="cus_old",
                status=BillingStatus.CANCELLED,
            )
            db_sess.add(billing)
            await db_sess.flush()

            response = await billing_service.activate_subscription(
                user_id=user.id,
                subscription_id="sub_new",
                customer_id="cus_new",
                billing_provider=BillingProvider.STRIPE,
                db_sess=db_sess,
            )

            assert response.id == billing.id
            assert response.subscription_id == "sub_new"
            assert response.status == BillingStatus.ACTIVE

            rows = (await db_sess.execute(select(Billing))).scalars().all()
            assert len(rows) == 1


@pytest.mark.asyncio(loop_scope="session")
class TestCancelSubscription:
    async def test_cancels_subscription(
        self,
        billing_service,
        user_service,
        mock_billing_provider,
        mock_notification_publisher,
        create_drop_tables,
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)
            await billing_service.activate_subscription(
                user_id=user.id,
                subscription_id="sub_123",
                customer_id="cus_123",
                billing_provider=BillingProvider.STRIPE,
                db_sess=db_sess,
            )
            mock_billing_provider.cancel_subscription.reset_mock()
            mock_notification_publisher.publish.reset_mock()

            response = await billing_service.cancel_subscription(user.id, db_sess)

            assert response.status == BillingStatus.CANCELLED
            mock_billing_provider.cancel_subscription.assert_awaited_once_with(
                "sub_123"
            )

            user_row = await db_sess.get(User, user.id)
            assert user_row.tier == Tier.FREE

            events = (await db_sess.execute(select(EventOutbox))).scalars().all()
            assert len(events) == 2
            assert any(e.type == BillingEventType.SUBSCRIPTION_CANCELLED for e in events)

            mock_notification_publisher.publish.assert_awaited_once()
            assert (
                mock_notification_publisher.publish.call_args.kwargs["type"]
                == NotificationType.BILLING_SUBSCRIPTION_CANCELLED
            )

    async def test_already_cancelled_raises(
        self,
        billing_service,
        user_service,
        mock_billing_provider,
        create_drop_tables,
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)
            await billing_service.activate_subscription(
                user_id=user.id,
                subscription_id="sub_123",
                customer_id="cus_123",
                billing_provider=BillingProvider.STRIPE,
                db_sess=db_sess,
            )
            mock_billing_provider.cancel_subscription.reset_mock()
            await billing_service.cancel_subscription(user.id, db_sess)
            mock_billing_provider.cancel_subscription.reset_mock()

            with pytest.raises(BillingAlreadyCancelledException):
                await billing_service.cancel_subscription(user.id, db_sess)

            mock_billing_provider.cancel_subscription.assert_not_called()

    async def test_nonexistent_billing_raises(
        self, billing_service, user_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)

            with pytest.raises(BillingNotFoundException):
                await billing_service.cancel_subscription(user.id, db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestCancelSubscriptionWebhook:
    async def test_cancels_billing_by_subscription(
        self,
        billing_service,
        user_service,
        mock_notification_publisher,
        create_drop_tables,
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)
            await billing_service.activate_subscription(
                user_id=user.id,
                subscription_id="sub_123",
                customer_id="cus_123",
                billing_provider=BillingProvider.STRIPE,
                db_sess=db_sess,
            )
            mock_notification_publisher.publish.reset_mock()

            response = await billing_service.cancel_subscription_webhook(
                "sub_123", db_sess
            )

            assert response is not None
            assert response.status == BillingStatus.CANCELLED

            user_row = await db_sess.get(User, user.id)
            assert user_row.tier == Tier.FREE

    async def test_unknown_subscription_returns_none(
        self, billing_service, user_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            response = await billing_service.cancel_subscription_webhook(
                "sub_unknown", db_sess
            )
            assert response is None

    async def test_idempotent_when_already_cancelled(
        self,
        billing_service,
        user_service,
        create_drop_tables,
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)
            await billing_service.activate_subscription(
                user_id=user.id,
                subscription_id="sub_123",
                customer_id="cus_123",
                billing_provider=BillingProvider.STRIPE,
                db_sess=db_sess,
            )
            await billing_service.cancel_subscription_webhook("sub_123", db_sess)

            rows = (await db_sess.execute(select(EventOutbox))).scalars().all()
            cancelled_count = sum(
                1 for r in rows if r.type == BillingEventType.SUBSCRIPTION_CANCELLED
            )

            await billing_service.cancel_subscription_webhook("sub_123", db_sess)

            rows_after = (await db_sess.execute(select(EventOutbox))).scalars().all()
            cancelled_count_after = sum(
                1 for r in rows_after if r.type == BillingEventType.SUBSCRIPTION_CANCELLED
            )
            assert cancelled_count_after == cancelled_count


@pytest.mark.asyncio(loop_scope="session")
class TestGetBilling:
    async def test_returns_billing(
        self, billing_service, user_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)
            await billing_service.activate_subscription(
                user_id=user.id,
                subscription_id="sub_123",
                customer_id="cus_123",
                billing_provider=BillingProvider.STRIPE,
                db_sess=db_sess,
            )

            response = await billing_service.get_billing(user.id, db_sess)
            assert response.subscription_id == "sub_123"

    async def test_raises_when_not_found(
        self, billing_service, user_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)
            with pytest.raises(BillingNotFoundException):
                await billing_service.get_billing(user.id, db_sess)
