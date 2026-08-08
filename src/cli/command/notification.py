import asyncio

import click

from config import BREVO_API_KEY, BREVO_SENDER_EMAIL, BREVO_SENDER_NAME
from chrima.discord import DiscordClient
from chrima.email.brevo import BrevoEmailService
from chrima.notification import NotificationPoller
from chrima.notification.channel import (
    NotificationChannelType,
    DiscordNotificationChannel,
    EmailNotificationChannel,
)
from chrima.notification.template import (
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
        discord_client = DiscordClient()

        discord_channel = DiscordNotificationChannel(
            discord_client=discord_client,
            template_engine=DiscordNotificationTemplateEngine(),
        )

        notification_channels: dict = {
            NotificationChannelType.DISCORD: discord_channel,
        }

        if BREVO_API_KEY and BREVO_SENDER_EMAIL:
            email_channel = EmailNotificationChannel(
                email_service=BrevoEmailService(
                    name=BREVO_SENDER_NAME,
                    email_address=BREVO_SENDER_EMAIL,
                    api_key=BREVO_API_KEY,
                ),
                template_engine=EmailNotificationTemplateEngine(),
            )
            notification_channels[NotificationChannelType.EMAIL] = email_channel

        notification_poller = NotificationPoller(
            notification_channels=notification_channels,
            interval=interval,
            batch_size=batch_size,
            timeout=timeout,
        )

        await notification_poller.run()

    try:
        asyncio.run(_run())
    except KeyError:
        pass
