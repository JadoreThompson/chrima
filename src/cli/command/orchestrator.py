import asyncio
import logging

import click
import discord

from chrima.message_platform import MessagePlatformService
from chrima.message_platform.service.discord import DiscordService
from chrima.message_platform.service.orchestrator import MessagePlatformOrchestrator
from chrima.message_platform.service.oauth.discord import DiscordOauthService
from chrima.product.service import ProductService
from chrima.transaction.event import TransactionEventDeserialiser
from config import DISCORD_BOT_TOKEN

logger = logging.getLogger("orchestrator_cli")


async def _run_orchestrator() -> None:
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    mp_service = MessagePlatformService(discord_oauth_service=DiscordOauthService())
    discord_service = DiscordService(
        discord_client=client, message_platform_service=mp_service
    )
    product_service = ProductService(price_service=None)
    deserialiser = TransactionEventDeserialiser()

    orchestrator = MessagePlatformOrchestrator(
        discord_service=discord_service,
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
