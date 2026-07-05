from uuid import uuid4

import pytest

from chrima.notification.enums import NotificationType
from chrima.notification.schema import (
    Notification,
    SubscriptionExpiredNotificationContext,
    SubscriptionExpiringNotificationContext,
    SubscriptionSufficientNotificationContext,
)
from chrima.notification.template.engine import EmailNotificationTemplateEngine
from chrima.notification.template.engine.email.types import EmailTemplate
from chrima.notification.template.engine.exception import (
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
