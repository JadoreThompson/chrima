import discord

from .base import NotificationChannel
from ..enums import NotificationType
from ..schema import (
    Notification,
    SubscriptionIncompleteNotificationContext,
    SubscriptionNowSufficientNotificationContext,
    SubscriptionSufficientNotificationContext,
)
from ..template.engine import DiscordNotificationTemplateEngine


class DiscordNotificationChannel(NotificationChannel):
    def __init__(
        self,
        discord_client: discord.Client,
        template_engine: DiscordNotificationTemplateEngine,
    ):
        super().__init__()
        self._discord_client = discord_client
        self._template_engine = template_engine

    async def send(self, notification: Notification) -> None:
        embed = self._template_engine.render(notification)

        ctx = notification.context
        if not hasattr(ctx, "channel_id") or not hasattr(ctx, "platform_user_id"):
            return

        channel = self._discord_client.get_channel(int(ctx.channel_id))
        if channel is None:
            return

        mention = f"<@{ctx.platform_user_id}>"
        await channel.send(content=mention, embed=embed)
