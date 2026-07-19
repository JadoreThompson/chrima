import asyncio
import logging

import click

from chrima.discord import DiscordService, DiscordMembershipService, DiscordBot
from chrima.encryption import EncryptionService
from chrima.event_bus.publisher import OutboxEventPublisher
from chrima.notification.template import DiscordNotificationTemplateEngine
from chrima.price import PriceService
from chrima.product import ProductService
from chrima.subscription import SubscriptionBalanceService
from chrima.tokens import TokenService
from chrima.transaction.event import TransactionEventDeserialiser
from chrima.transaction.service import TransactionOrchestrator
from chrima.workspace import WorkspaceService
from config import DISCORD_BOT_TOKEN

logger = logging.getLogger("orchestrator_cli")


async def _run_orchestrator() -> None:
    event_publisher = OutboxEventPublisher()
    workspace_service = WorkspaceService()
    token_service = TokenService()
    price_service = PriceService(
        token_service=token_service, event_publisher=event_publisher
    )
    product_service = ProductService(
        price_service=price_service, event_publisher=event_publisher
    )
    subscription_service = SubscriptionBalanceService()
    client = DiscordBot(
        workspace_service=workspace_service,
        product_service=product_service,
        price_service=price_service,
        subscription_service=subscription_service,
        template_engine=DiscordNotificationTemplateEngine(),
    )
    discord_service = DiscordService(encryption_service=EncryptionService())
    discord_membership_service = DiscordMembershipService(
        discord_client=client,
        discord_service=discord_service,
    )
    deserialiser = TransactionEventDeserialiser()

    orchestrator = TransactionOrchestrator(
        discord_service=discord_service,
        discord_membership_service=discord_membership_service,
        product_service=product_service,
        deserialiser=deserialiser,
    )

    try:
        task = asyncio.create_task(client.start(DISCORD_BOT_TOKEN))
        await asyncio.sleep(1)
        await client.wait_until_ready()

        await orchestrator.run()
    finally:
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass
        await orchestrator.close()
        await client.close()


@click.group("orchestrator")
def orchestrator():
    pass


@orchestrator.command(name="run")
def orchestrator_run():
    asyncio.run(_run_orchestrator())
