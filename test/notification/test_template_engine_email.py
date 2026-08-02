from uuid import uuid4

import pytest

from chrima.notification.enums import NotificationType
from chrima.notification.schema import (
    Notification,
    BillingSubscriptionActivatedNotificationContext,
    BillingSubscriptionCancelledNotificationContext,
    SubscriptionExpiredNotificationContext,
    SubscriptionExpiringNotificationContext,
    SubscriptionSufficientNotificationContext,
)
from chrima.notification.template import EmailNotificationTemplateEngine
from chrima.notification.template.email.types import EmailTemplate
from chrima.notification.template.exception import (
    NotificationTemplateEngineException,
)


@pytest.fixture
def engine():
    return EmailNotificationTemplateEngine()


@pytest.fixture
def sufficient_context():
    return SubscriptionSufficientNotificationContext(
        guild_id="guild_1",
        channel_id="ch_1",
        platform_user_id="usr_1",
        product_id=uuid4(),
        product_name="Test Product",
        product_price=9.99,
        currency="USD",
        remaining_amount=15.0,
        transaction_id=uuid4(),
    )


@pytest.fixture
def expiring_context():
    return SubscriptionExpiringNotificationContext(
        guild_id="guild_1",
        channel_id="ch_1",
        platform_user_id="usr_1",
        product_id=uuid4(),
        product_name="Test Product",
        cycle_end=1_800_000_000,
    )


@pytest.fixture
def expired_context():
    return SubscriptionExpiredNotificationContext(
        guild_id="guild_1",
        channel_id="ch_1",
        platform_user_id="usr_1",
        product_id=uuid4(),
        product_name="Test Product",
        cycle_end=1_700_000_000,
    )


def test_render_sufficient_returns_template(engine, sufficient_context):
    notification = Notification(
        recipient="usr_1",
        type=NotificationType.SUBSCRIPTION_SUFFICIENT,
        context=sufficient_context,
    )

    template = engine.render(notification)

    assert isinstance(template, EmailTemplate)
    assert (
        sufficient_context.product_name in template.subject
        or sufficient_context.product_name in template.body
    )
    assert (
        sufficient_context.platform_user_id in template.subject
        or sufficient_context.platform_user_id in template.body
    )


def test_render_expiring_returns_template(engine, expiring_context):
    notification = Notification(
        recipient="usr_1",
        type=NotificationType.SUBSCRIPTION_EXPIRING,
        context=expiring_context,
    )

    template = engine.render(notification)

    assert isinstance(template, EmailTemplate)
    assert "Expiring" in template.subject or "Expiring" in template.body
    assert (
        expiring_context.product_name in template.subject
        or expiring_context.product_name in template.body
    )
    assert (
        str(expiring_context.cycle_end) in template.subject
        or str(expiring_context.cycle_end) in template.body
    )


def test_render_expired_returns_template(engine, expired_context):
    notification = Notification(
        recipient="usr_1",
        type=NotificationType.SUBSCRIPTION_EXPIRED,
        context=expired_context,
    )

    template = engine.render(notification)

    assert isinstance(template, EmailTemplate)
    assert "Expired" in template.subject or "Expired" in template.body
    assert (
        expired_context.product_name in template.subject
        or expired_context.product_name in template.body
    )
    assert "expired" in template.body or "expired" in template.subject


@pytest.fixture
def billing_activated_context():
    return BillingSubscriptionActivatedNotificationContext(
        user_id=str(uuid4()),
        username="pro_user",
        email="pro@example.com",
        tier="pro",
        billing_provider="stripe",
        subscription_id="sub_123",
    )


@pytest.fixture
def billing_cancelled_context():
    return BillingSubscriptionCancelledNotificationContext(
        user_id=str(uuid4()),
        username="pro_user",
        email="pro@example.com",
        tier="free",
    )


def test_render_billing_activated_returns_template(engine, billing_activated_context):
    notification = Notification(
        recipient=billing_activated_context.email,
        type=NotificationType.BILLING_SUBSCRIPTION_ACTIVATED,
        context=billing_activated_context,
    )

    template = engine.render(notification)

    assert isinstance(template, EmailTemplate)
    assert billing_activated_context.username in template.body
    assert billing_activated_context.subscription_id in template.body
    assert "PRO" in template.subject


def test_render_billing_cancelled_returns_template(engine, billing_cancelled_context):
    notification = Notification(
        recipient=billing_cancelled_context.email,
        type=NotificationType.BILLING_SUBSCRIPTION_CANCELLED,
        context=billing_cancelled_context,
    )

    template = engine.render(notification)

    assert isinstance(template, EmailTemplate)
    assert billing_cancelled_context.username in template.body
    assert "free" in template.body
    assert "PRO" in template.subject


def test_render_unknown_type_raises(engine, sufficient_context):
    notification = Notification.model_construct(
        recipient="usr_1",
        type="unknown.type",
        context=sufficient_context,
    )

    with pytest.raises(
        NotificationTemplateEngineException, match="Unknown notification type"
    ):
        engine.render(notification)
