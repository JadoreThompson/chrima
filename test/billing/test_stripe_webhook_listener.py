from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import stripe
from sqlalchemy import select

from chrima.billing import BillingService
from chrima.billing.enums import BillingProvider, BillingStatus
from chrima.billing.exception import BillingWebhookVerificationException
from chrima.billing.listener.stripe import (
    CHECKOUT_SESSION_COMPLETED,
    SUBSCRIPTION_DELETED,
    StripeBillingWebhookListener,
)
from chrima.billing.model import Billing, BillingWebhookEvent
from chrima.billing.provider import BillingProvider as BillingProviderProtocol
from chrima.notification import NotificationPublisher
from chrima.user.enums import Tier
from chrima.user.model import User
from infra.db import get_db_session


@pytest.fixture
def mock_stripe():
    with patch("chrima.billing.listener.stripe.stripe") as mock:
        yield mock


@pytest.fixture
def mock_redis():
    return AsyncMock()


def _event(event_type: str, object_data: object, event_id: str = "evt_1"):
    return SimpleNamespace(id=event_id, type=event_type, data=SimpleNamespace(object=object_data))


def _headers(sig: str = "t=1,v1=abc"):
    return {"stripe-signature": sig}


def _session_data(user_id: str, **kw):
    data = {
        "id": "cs_1",
        "payment_status": "paid",
        "metadata": {"user_id": user_id},
        "customer": "cus_1",
        "subscription": "sub_1",
    }
    data.update(kw)
    return stripe.checkout.Session.construct_from(data, None)


async def _create_user(user_service, db_sess):
    return await user_service.create(
        username=f"user_{uuid4().hex[:8]}",
        email=f"{uuid4().hex[:8]}@example.com",
        password="secure_pass_123",
        db_sess=db_sess,
    )


def _service(user_service, event_publisher, mock_redis):
    return BillingService(
        billing_provider=AsyncMock(spec=BillingProviderProtocol),
        user_service=user_service,
        event_publisher=event_publisher,
        notification_publisher=AsyncMock(spec=NotificationPublisher),
        redis_client=mock_redis,
    )


class TestVerify:
    def test_raises_on_missing_signature(self, mock_stripe):
        listener = StripeBillingWebhookListener(
            billing_service=AsyncMock(spec=BillingService), webhook_secret="whsec"
        )

        with pytest.raises(BillingWebhookVerificationException):
            listener._verify(b"{}", {})

    def test_raises_on_missing_secret(self, mock_stripe):
        listener = StripeBillingWebhookListener(
            billing_service=AsyncMock(spec=BillingService), webhook_secret=None
        )

        with pytest.raises(BillingWebhookVerificationException):
            listener._verify(b"{}", _headers())

    def test_raises_on_invalid_signature(self, mock_stripe):
        mock_stripe.Webhook.construct_event.side_effect = (
            stripe.error.SignatureVerificationError("bad signature", "sig")
        )
        listener = StripeBillingWebhookListener(
            billing_service=AsyncMock(spec=BillingService), webhook_secret="whsec"
        )

        with pytest.raises(BillingWebhookVerificationException):
            listener._verify(b"{}", _headers())

    def test_verifies_valid_signature(self, mock_stripe):
        mock_stripe.Webhook.construct_event.return_value = _event(
            SUBSCRIPTION_DELETED,
            stripe.Subscription.construct_from({"id": "sub_1"}, None),
        )
        listener = StripeBillingWebhookListener(
            billing_service=AsyncMock(spec=BillingService), webhook_secret="whsec"
        )

        event = listener._verify(b'{"type":"x"}', _headers())

        assert event.id == "evt_1"
        mock_stripe.Webhook.construct_event.assert_called_once_with(
            b'{"type":"x"}', "t=1,v1=abc", "whsec"
        )


@pytest.mark.asyncio(loop_scope="session")
class TestHandle:
    async def test_processes_checkout_session_completed(
        self, mock_stripe, user_service, event_publisher, mock_redis, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)

        mock_stripe.Webhook.construct_event.return_value = _event(
            CHECKOUT_SESSION_COMPLETED, _session_data(str(user.id))
        )
        listener = StripeBillingWebhookListener(
            billing_service=_service(user_service, event_publisher, mock_redis),
            webhook_secret="whsec",
        )

        async with get_db_session() as db_sess:
            await listener.handle(_headers(), b'{"payload":"x"}', db_sess)

        async with get_db_session() as db_sess:
            billing = await db_sess.scalar(select(Billing))
            assert billing is not None
            assert billing.subscription_id == "sub_1"
            assert billing.customer_id == "cus_1"
            assert billing.billing_provider == BillingProvider.STRIPE
            assert billing.status == BillingStatus.ACTIVE

            user_row = await db_sess.get(User, user.id)
            assert user_row.tier == Tier.PRO

    async def test_processes_subscription_deleted(
        self, mock_stripe, user_service, event_publisher, mock_redis, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)
            db_sess.add(
                Billing(
                    user_id=user.id,
                    subscription_id="sub_1",
                    billing_provider=BillingProvider.STRIPE,
                    customer_id="cus_1",
                    status=BillingStatus.ACTIVE,
                )
            )
            await user_service.set_tier(user.id, Tier.PRO, db_sess)

        mock_stripe.Webhook.construct_event.return_value = _event(
            SUBSCRIPTION_DELETED,
            stripe.Subscription.construct_from({"id": "sub_1"}, None),
        )
        listener = StripeBillingWebhookListener(
            billing_service=_service(user_service, event_publisher, mock_redis),
            webhook_secret="whsec",
        )

        async with get_db_session() as db_sess:
            await listener.handle(_headers(), b'{"payload":"x"}', db_sess)

        async with get_db_session() as db_sess:
            billing = await db_sess.scalar(select(Billing))
            assert billing.status == BillingStatus.CANCELLED

            user_row = await db_sess.get(User, user.id)
            assert user_row.tier == Tier.FREE

    async def test_ignores_unpaid_checkout(
        self, mock_stripe, user_service, event_publisher, mock_redis, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)

        mock_stripe.Webhook.construct_event.return_value = _event(
            CHECKOUT_SESSION_COMPLETED,
            _session_data(str(user.id), payment_status="unpaid"),
        )
        listener = StripeBillingWebhookListener(
            billing_service=_service(user_service, event_publisher, mock_redis),
            webhook_secret="whsec",
        )

        async with get_db_session() as db_sess:
            await listener.handle(_headers(), b'{"payload":"x"}', db_sess)

        async with get_db_session() as db_sess:
            billing = await db_sess.scalar(select(Billing))
            assert billing is None

    async def test_is_idempotent(
        self, mock_stripe, user_service, event_publisher, mock_redis, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            user = await _create_user(user_service, db_sess)

        mock_stripe.Webhook.construct_event.return_value = _event(
            CHECKOUT_SESSION_COMPLETED, _session_data(str(user.id))
        )
        listener = StripeBillingWebhookListener(
            billing_service=_service(user_service, event_publisher, mock_redis),
            webhook_secret="whsec",
        )

        async with get_db_session() as db_sess:
            await listener.handle(_headers(), b'{"payload":"x"}', db_sess)
        async with get_db_session() as db_sess:
            await listener.handle(_headers(), b'{"payload":"x"}', db_sess)

        async with get_db_session() as db_sess:
            billings = (await db_sess.execute(select(Billing))).scalars().all()
            assert len(billings) == 1

            markers = (
                (await db_sess.execute(select(BillingWebhookEvent))).scalars().all()
            )
            assert len(markers) == 1

    async def test_raises_on_invalid_signature(
        self, mock_stripe, user_service, event_publisher, mock_redis, create_drop_tables
    ):
        mock_stripe.Webhook.construct_event.side_effect = (
            stripe.error.SignatureVerificationError("bad", "sig")
        )
        listener = StripeBillingWebhookListener(
            billing_service=_service(user_service, event_publisher, mock_redis),
            webhook_secret="whsec",
        )

        async with get_db_session() as db_sess:
            with pytest.raises(BillingWebhookVerificationException):
                await listener.handle(_headers(), b"{}", db_sess)
