import asyncio
import logging

import click

from chrima.discord import DiscordService, DiscordMembershipService, DiscordBot
from chrima.encryption import EncryptionService
from chrima.event_bus.publisher import OutboxEventPublisher
from chrima.notification.service.publisher import NotificationPublisher
from chrima.notification.template import DiscordNotificationTemplateEngine
from chrima.price import PriceService
from chrima.product import ProductService
from chrima.subscription import SubscriptionBalanceService
from chrima.transaction.event import TransactionEventDeserialiser
from chrima.transaction.service import TransactionOrchestrator, EthListener
from chrima.wallet import WalletService
from chrima.workspace import WorkspaceService
from config import (
    DISCORD_BOT_TOKEN,
    CHRIMA_PAYMENT_CONTRACT_ABI,
    CHRIMA_PAYMENT_CONTRACT_ADDRESS,
    RPC_URL,
)

logger = logging.getLogger("transaction_cli")


@click.group("transaction")
def transaction():
    pass


@transaction.group("listener")
def listener():
    pass


@listener.command(name="eth")
@click.option("--poll-interval", default=5, type=int, help="Poll interval in seconds")
def listen_eth(poll_interval: int) -> None:
    event_publisher = OutboxEventPublisher()
    price_service = PriceService(event_publisher=event_publisher)
    product_service = ProductService(
        event_publisher=event_publisher, wallet_service=WalletService()
    )
    el = EthListener(
        event_publisher=OutboxEventPublisher(),
        product_service=product_service,
        price_service=price_service,
    )
    asyncio.run(el.listen(poll_interval=poll_interval))


logger = logging.getLogger("orchestrator_cli")


async def _run_orchestrator() -> None:
    event_publisher = OutboxEventPublisher()

    price_service = PriceService(event_publisher=event_publisher)

    product_service = ProductService(
        event_publisher=event_publisher, wallet_service=WalletService()
    )

    workspace_service = WorkspaceService()

    subscription_service = SubscriptionBalanceService(event_publisher=event_publisher)

    client = DiscordBot(
        workspace_service=workspace_service,
        product_service=product_service,
        price_service=price_service,
        subscription_service=subscription_service,
        template_engine=DiscordNotificationTemplateEngine(),
    )

    discord_service = DiscordService(encryption_service=EncryptionService())

    discord_membership_service = DiscordMembershipService(
        discord_client=client, discord_service=discord_service
    )

    deserialiser = TransactionEventDeserialiser()

    orchestrator = TransactionOrchestrator(
        discord_service=discord_service,
        discord_membership_service=discord_membership_service,
        product_service=product_service,
        price_service=price_service,
        workspace_service=workspace_service,
        deserialiser=deserialiser,
        notification_publisher=NotificationPublisher(),
    )

    task = None

    try:
        task = asyncio.create_task(client.start(DISCORD_BOT_TOKEN))
        await asyncio.sleep(1)
        await client.wait_until_ready()

        await orchestrator.run()
    finally:
        if task:
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

        await orchestrator.close()
        await client.close()


@transaction.command(name="orchestrator")
def orchestrator() -> None:
    asyncio.run(_run_orchestrator())
