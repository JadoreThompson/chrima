from uuid import uuid4

import discord
import pytest

from chrima.notification.enums import NotificationType
from chrima.notification.schema import (
    Notification,
    SubscriptionExpiredNotificationContext,
    SubscriptionExpiringNotificationContext,
    SubscriptionSufficientNotificationContext,
)
from chrima.notification.template import DiscordNotificationTemplateEngine
from chrima.notification.template.exception import (
    NotificationTemplateEngineException,
)


@pytest.fixture
def engine():
    return DiscordNotificationTemplateEngine()


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


def test_render_sufficient_returns_embed(engine, sufficient_context):
    notification = Notification(
        recipient="usr_1",
        type=NotificationType.SUBSCRIPTION_SUFFICIENT,
        context=sufficient_context,
    )

    embed = engine.render(notification)

    assert isinstance(embed, discord.Embed)
    assert embed.color == discord.Color.green()
    assert embed.author.name == "Chrima"
    assert "Covered" in embed.title
    assert sufficient_context.product_name in embed.description
    assert sufficient_context.platform_user_id in embed.description


def test_render_expiring_returns_embed(engine, expiring_context):
    notification = Notification(
        recipient="usr_1",
        type=NotificationType.SUBSCRIPTION_EXPIRING,
        context=expiring_context,
    )

    embed = engine.render(notification)

    assert isinstance(embed, discord.Embed)
    assert embed.color == discord.Color.gold()
    assert embed.author.name == "Chrima"
    assert "Expiring" in embed.title
    assert expiring_context.product_name in embed.description
    assert str(expiring_context.cycle_end) in str(embed.description)


def test_render_expired_returns_embed(engine, expired_context):
    notification = Notification(
        recipient="usr_1",
        type=NotificationType.SUBSCRIPTION_EXPIRED,
        context=expired_context,
    )

    embed = engine.render(notification)

    assert isinstance(embed, discord.Embed)
    assert embed.color == discord.Color.red()
    assert embed.author.name == "Chrima"
    assert "Expired" in embed.title
    assert expired_context.product_name in embed.description
    assert "expired" in embed.description


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
