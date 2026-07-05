import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import discord
import pytest
import pytest_asyncio

from chrima.notification.channel.discord import DiscordNotificationChannel
from chrima.notification.enums import NotificationType
from chrima.notification.schema import (
    Notification,
    SubscriptionSufficientNotificationContext,
)
from chrima.notification.template.engine import DiscordNotificationTemplateEngine


require_discord = pytest.mark.skipif(
    not os.getenv("DISCORD_BOT_TOKEN") or not os.getenv("DISCORD_CHANNEL_ID"),
    reason="Requires DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID",
)


@pytest.fixture
def mock_discord_client():
    return MagicMock(spec=discord.Client)


@pytest.fixture
def mock_template_engine():
    return MagicMock(spec=DiscordNotificationTemplateEngine)


@pytest.fixture
def channel(mock_discord_client, mock_template_engine):
    return DiscordNotificationChannel(
        discord_client=mock_discord_client,
        template_engine=mock_template_engine,
    )


@pytest.fixture
def sample_embed():
    return discord.Embed(title="test", description="test")


@pytest.fixture
def sufficient_context():
    return SubscriptionSufficientNotificationContext(
        guild_id="guild_1",
        channel_id="12345",
        platform_user_id="67890",
        product_id=uuid4(),
        product_name="test-product",
        product_price=10.0,
        currency="USD",
        remaining_amount=10.0,
        transaction_id=uuid4(),
    )


@pytest_asyncio.fixture(scope="session")
async def discord_client():
    client = discord.Client(intents=discord.Intents.default())
    bg = asyncio.create_task(client.start(os.environ["DISCORD_BOT_TOKEN"]))
    await asyncio.sleep(1)
    await client.wait_until_ready()

    yield client

    bg.cancel()
    try:
        await client.close()
    except Exception:
        pass


@pytest.fixture(scope="session")
def integration_channel(discord_client):
    return DiscordNotificationChannel(
        discord_client=discord_client,
        template_engine=DiscordNotificationTemplateEngine(),
    )


@pytest.mark.asyncio(loop_scope="session")
class TestUnit:

    async def test_send_success(
        self, channel, mock_discord_client, mock_template_engine, sample_embed, sufficient_context
    ):
        """A notification with valid channel_id and platform_user_id renders the
        template, fetches the Discord channel, and sends the embed with a mention."""
        mock_template_engine.render.return_value = sample_embed
        mock_channel = AsyncMock(spec=discord.TextChannel)
        mock_discord_client.get_channel.return_value = mock_channel

        notification = Notification(
            recipient="usr_1",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sufficient_context,
        )

        await channel.send(notification)

        mock_channel.send.assert_called_once_with(
            content="<@67890>", embed=sample_embed
        )

    async def test_send_missing_channel_id(
        self, channel, mock_discord_client, mock_template_engine, sample_embed, sufficient_context
    ):
        """When the notification context lacks channel_id, send returns early
        without sending a message."""
        mock_template_engine.render.return_value = sample_embed
        del sufficient_context.channel_id

        notification = Notification(
            recipient="usr_1",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sufficient_context,
        )

        mock_channel = AsyncMock(spec=discord.TextChannel)
        mock_discord_client.get_channel.return_value = mock_channel

        await channel.send(notification)

        mock_channel.send.assert_not_called()

    async def test_send_missing_platform_user_id(
        self, channel, mock_discord_client, mock_template_engine, sample_embed, sufficient_context
    ):
        """When the notification context lacks platform_user_id, send returns early
        without sending a message."""
        mock_template_engine.render.return_value = sample_embed
        del sufficient_context.platform_user_id

        notification = Notification(
            recipient="usr_1",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sufficient_context,
        )

        mock_channel = AsyncMock(spec=discord.TextChannel)
        mock_discord_client.get_channel.return_value = mock_channel

        await channel.send(notification)

        mock_channel.send.assert_not_called()

    async def test_send_channel_not_found(
        self, channel, mock_discord_client, mock_template_engine, sample_embed, sufficient_context
    ):
        """When discord_client.get_channel returns None, no message is sent."""
        mock_template_engine.render.return_value = sample_embed
        mock_discord_client.get_channel.return_value = None

        notification = Notification(
            recipient="usr_1",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sufficient_context,
        )

        mock_channel = AsyncMock(spec=discord.TextChannel)

        await channel.send(notification)

        mock_channel.send.assert_not_called()

    async def test_send_raises_on_template_error(
        self, channel, mock_discord_client, mock_template_engine, sufficient_context
    ):
        """When the template engine raises, the exception propagates and no
        message is sent."""
        mock_template_engine.render.side_effect = ValueError("bad template")

        notification = Notification(
            recipient="usr_1",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sufficient_context,
        )

        mock_channel = AsyncMock(spec=discord.TextChannel)
        mock_discord_client.get_channel.return_value = mock_channel

        with pytest.raises(ValueError, match="bad template"):
            await channel.send(notification)

        mock_channel.send.assert_not_called()


@pytest.mark.asyncio(loop_scope="session")
class TestIntegration:

    @require_discord
    async def test_sends_embed_to_discord(self, integration_channel):
        """Sends a real SUBSCRIPTION_SUFFICIENT embed to the configured
        Discord channel and verifies no exception is raised."""
        ctx = SubscriptionSufficientNotificationContext(
            guild_id="guild_1",
            channel_id=os.environ["DISCORD_CHANNEL_ID"],
            platform_user_id=os.environ.get("DISCORD_USER_ID", "1"),
            product_id=uuid4(),
            product_name="Integration Test Product",
            product_price=9.99,
            currency="USD",
            remaining_amount=9.99,
            transaction_id=uuid4(),
        )
        notification = Notification(
            recipient="integration_test",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=ctx,
        )

        await integration_channel.send(notification)
