import asyncio
import logging

from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract
from web3.types import LogReceipt

from chrima.event_bus.publisher import EventPublisher
from config import CONTRACT_ABI, CHRIMA_PAYMENT_CONTRACT_ADDRESS, RPC_URL
from core.db import get_db_session
from util import get_datetime
from ..enums import TransactionStatus
from ..event import TransactionCompletedEvent
from ..model import Transaction

TRANSACTION_COMPLETE_TOPIC = AsyncWeb3.keccak(
    text="TransactionComplete(string,string,string,address,address,address,uint256)"
)
TRANSACTION_FAILED_TOPIC = AsyncWeb3.keccak(
    text="TransactionFailed(string,string,string,address,address,address,string)"
)


class EthListener:
    def __init__(
        self,
        event_publisher: EventPublisher,
        rpc_url: str = RPC_URL,
        contract_address: str = CHRIMA_PAYMENT_CONTRACT_ADDRESS,
        abi: list[dict] = CONTRACT_ABI,
    ):
        self._w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
        self._contract: AsyncContract = self._w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=abi,
        )
        self._publisher = event_publisher
        self._logger = logging.getLogger("eth_listener")

    async def _handle_transaction_complete(self, event: LogReceipt) -> None:
        parsed = self._contract.events.TransactionComplete().process_log(event)
        args = parsed["args"]

        async with get_db_session() as db_sess:
            txn = Transaction(
                product_id=args["product_id"],
                price_id=args["price_id"],
                group_user_id=args["group_user_id"],
                sender=args["sender"],
                recipient=args["recipient"],
                address=args["token"],
                amount=float(args["tokenAmount"]),
                status=TransactionStatus.COMPLETE,
                timestamp=int(get_datetime().timestamp()),
            )
            db_sess.add(txn)

            await db_sess.refresh()
            await db_sess.refresh(txn)

            await self._publisher.publish(
                TransactionCompletedEvent(
                    transaction_id=txn.id,
                    product_id=txn.product_id,
                    price_id=txn.price_id,
                    sender=txn.sender,
                    recipient=txn.recipient,
                    token_address=txn.address,
                    token_amount=int(txn.amount),
                    group_user_id=txn.platform_user_id,
                ),
                db_sess=db_sess,
            )

        self._logger.info(
            "Persisted transaction %s: product=%s price=%s user=%s sender=%s recipient=%s",
            txn.id,
            args["product_id"],
            args["price_id"],
            args["group_user_id"],
            args["sender"],
            args["recipient"],
        )

    def _handle_transaction_failed(self, event: LogReceipt) -> None:
        parsed = self._contract.events.TransactionFailed().process_log(event)
        args = parsed["args"]
        self._logger.warning(
            "Transaction failed: product=%s price=%s user=%s sender=%s recipient=%s token=%s reason=%s",
            args["product_id"],
            args["price_id"],
            args["group_user_id"],
            args["sender"],
            args["recipient"],
            args["token"],
            args["reason"],
        )

    async def poll_events(
        self, from_block: int | None = None, to_block: int | None = None
    ) -> None:
        latest = await self._w3.eth.block_number
        from_block = from_block or latest - 100
        to_block = to_block or latest

        logs = await self._w3.eth.get_logs(
            {
                "address": self._contract.address,
                "fromBlock": from_block,
                "toBlock": to_block,
                "topics": [[TRANSACTION_COMPLETE_TOPIC, TRANSACTION_FAILED_TOPIC]],
            }
        )

        for log in logs:
            topic = log["topics"][0].hex()
            if topic == TRANSACTION_COMPLETE_TOPIC.hex():
                await self._handle_transaction_complete(log)
            elif topic == TRANSACTION_FAILED_TOPIC.hex():
                self._handle_transaction_failed(log)

    async def listen(self, poll_interval: int = 5) -> None:
        self._logger.info("Starting event listener ...")
        last_block = await self._w3.eth.block_number

        while True:
            try:
                current_block = await self._w3.eth.block_number
                if current_block > last_block + 5:
                    await self.poll_events(
                        from_block=last_block + 1, to_block=current_block
                    )
                    last_block = current_block

                await asyncio.sleep(poll_interval)
            except Exception as e:
                self._logger.exception("Error during event polling", exc_info=e)
                await asyncio.sleep(poll_interval)
