import asyncio
import logging

import click
import discord

from chrima.discord import DiscordMembershipService, DiscordOauthService
from chrima.encryption import EncryptionService
from chrima.product import ProductService
from chrima.transaction.event import TransactionEventDeserialiser
from chrima.transaction.service import TransactionOrchestrator
from config import DISCORD_BOT_TOKEN

logger = logging.getLogger("orchestrator_cli")


async def _run_orchestrator() -> None:
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    oauth_service = DiscordOauthService(
        encryption_service=EncryptionService()
    )
    membership_service = DiscordMembershipService(
        discord_client=client,
        oauth_service=oauth_service,
    )
    product_service = ProductService(price_service=None)
    deserialiser = TransactionEventDeserialiser()

    orchestrator = TransactionOrchestrator(
        oauth_service=oauth_service,
        membership_service=membership_service,
        product_service=product_service,
        deserialiser=deserialiser,
    )

    async def start_orchestrator():
        await client.wait_until_ready()
        logger.info("Discord client ready, starting orchestrator ...")
        await orchestrator.run()

    async def runner():
        async with asyncio.TaskGroup() as tg:
            tg.create_task(client.start(DISCORD_BOT_TOKEN))
            tg.create_task(start_orchestrator())

    try:
        await runner()
    finally:
        await orchestrator.close()
        await client.close()


@click.group("orchestrator")
def orchestrator():
    pass


@orchestrator.command(name="run")
def orchestrator_run():
    asyncio.run(_run_orchestrator())
