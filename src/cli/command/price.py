import asyncio
import logging

import click
from web3 import AsyncWeb3

from chrima.price.event import PriceEventDeserialiser
from chrima.price.service.sync import PriceSyncService
from config import (
    CHRIMA_PAYMENT_CONTRACT_ABI,
    CHRIMA_PAYMENT_CONTRACT_ADDRESS,
    RPC_URL,
    SIGNER_PRIVATE_KEY,
)

logger = logging.getLogger("price_sync_cli")


async def _run_price_sync() -> None:
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URL))
    contract = w3.eth.contract(
        address=AsyncWeb3.to_checksum_address(CHRIMA_PAYMENT_CONTRACT_ADDRESS),
        abi=CHRIMA_PAYMENT_CONTRACT_ABI,
    )

    sync_service = PriceSyncService(
        w3=w3,
        contract=contract,
        signer_private_key=SIGNER_PRIVATE_KEY,
        deserialiser=PriceEventDeserialiser(),
    )

    await sync_service.run()


@click.group("price")
def price():
    pass


@price.group("sync")
def sync():
    pass


@sync.command(name="run")
def sync_run() -> None:
    asyncio.run(_run_price_sync())
