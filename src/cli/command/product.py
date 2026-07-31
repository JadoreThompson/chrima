import asyncio
import logging

import click
from web3 import AsyncWeb3

from chrima.product.event import ProductEventDeserialiser
from chrima.product.service.sync import ProductSyncService
from chrima.wallet import WalletService
from config import (
    CHRIMA_PAYMENT_CONTRACT_ABI,
    CHRIMA_PAYMENT_CONTRACT_ADDRESS,
    RPC_URL,
    SIGNER_PRIVATE_KEY,
)

logger = logging.getLogger("product_sync_cli")


async def _run_product_sync() -> None:
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URL))
    contract = w3.eth.contract(
        address=AsyncWeb3.to_checksum_address(CHRIMA_PAYMENT_CONTRACT_ADDRESS),
        abi=CHRIMA_PAYMENT_CONTRACT_ABI,
    )

    sync_service = ProductSyncService(
        w3=w3,
        contract=contract,
        signer_private_key=SIGNER_PRIVATE_KEY,
        deserialiser=ProductEventDeserialiser(),
        wallet_service=WalletService()
    )

    await sync_service.run()


@click.group("product")
def product():
    pass


@product.group("sync")
def sync():
    pass


@sync.command(name="run")
def sync_run() -> None:
    asyncio.run(_run_product_sync())
