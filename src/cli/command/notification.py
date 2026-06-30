import asyncio

import click
import discord

from chrima.email.brevo import BrevoEmailService
from chrima.notification import NotificationPoller
from chrima.notification.channel import (
    NotificationChannelType,
    DiscordNotificationChannel,
    EmailNotificationChannel,
)
from chrima.notification.template.engine import (
    DiscordNotificationTemplateEngine,
    EmailNotificationTemplateEngine,
)


@click.command(name="notification")
@click.option("--interval", required=True, type=int, help="Polling interval in seconds")
@click.option("--batch-size", required=True, type=int, help="Batch size per poll cycle")
@click.option(
    "--timeout",
    required=False,
    type=int,
    default=30,
    help="Timeout in seconds for each notification to be sent",
)
def notification(interval, batch_size, timeout):
    async def _run():
        intents = discord.Intents.default()
        discord_client = discord.Client(intents=intents)

        discord_channel = DiscordNotificationChannel(
            discord_client=discord_client,
            template_engine=DiscordNotificationTemplateEngine(),
        )

        email_channel = EmailNotificationChannel(
            email_service=BrevoEmailService(...),
            template_engine=EmailNotificationTemplateEngine(),
        )

        notification_poller = NotificationPoller(
            notification_channels={
                NotificationChannelType.DISCORD: discord_channel,
                NotificationChannelType.EMAIL: email_channel,
            },
            interval=interval,
            batch_size=batch_size,
            timeout=timeout,
        )

        await notification_poller.run()

    try:
        asyncio.run(_run())
    except KeyError:
        pass
