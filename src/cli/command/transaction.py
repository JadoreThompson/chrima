import asyncio
import logging

import click

from chrima.event_bus.publisher import OutboxEventPublisher
from chrima.transaction.service import EthListener
from config import CHRIMA_PAYMENT_CONTRACT_ABI, CHRIMA_PAYMENT_CONTRACT_ADDRESS, RPC_URL

logging.basicConfig(level=logging.INFO)


@click.group("listener")
def listener():
    pass


@listener.command(name="eth")
@click.option("--rpc-url", default=RPC_URL, help="Ethereum RPC URL")
@click.option(
    "--contract-address",
    default=CHRIMA_PAYMENT_CONTRACT_ADDRESS,
    help="ChrimaPayment contract address",
)
@click.option("--poll-interval", default=5, type=int, help="Poll interval in seconds")
def listen_eth(rpc_url: str, contract_address: str, poll_interval: int) -> None:
    el = EthListener(
        event_publisher=OutboxEventPublisher(),
        rpc_url=rpc_url,
        contract_address=contract_address,
        abi=CHRIMA_PAYMENT_CONTRACT_ABI,
    )
    asyncio.run(el.listen(poll_interval=poll_interval))


@click.group("transaction")
def transaction():
    pass


transaction.add_command(listener)
