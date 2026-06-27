import asyncio
import logging

import click

from config import CONTRACT_ABI, CONTRACT_ADDRESS, RPC_URL
from chrima.transaction.service.eth_listener import EthListener

logging.basicConfig(level=logging.INFO)


@click.group("listener")
def listener():
    pass


@listener.command(name="eth")
@click.option("--rpc-url", default=RPC_URL, help="Ethereum RPC URL")
@click.option(
    "--contract-address",
    default=CONTRACT_ADDRESS,
    help="ChrimaPayment contract address",
)
@click.option("--poll-interval", default=5, type=int, help="Poll interval in seconds")
def listen_eth(rpc_url: str, contract_address: str, poll_interval: int) -> None:
    el = EthListener(rpc_url=rpc_url, contract_address=contract_address, abi=CONTRACT_ABI)
    asyncio.run(el.listen(poll_interval=poll_interval))


@click.group("transaction")
def transaction():
    pass


transaction.add_command(listener)
