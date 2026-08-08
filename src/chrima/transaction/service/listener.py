import asyncio
import logging
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract
from web3.types import LogReceipt, FilterParams

from chrima.event_bus.publisher import EventPublisher
from chrima.monitoring import trace_class
from chrima.price import PriceService
from chrima.price.exception import PriceNotFoundException
from chrima.product import ProductService
from chrima.product.exception import ProductNotFoundException
from config import (
    CHRIMA_PAYMENT_CONTRACT_ABI,
    CHRIMA_PAYMENT_CONTRACT_ADDRESS,
    RPC_URL,
)
from infra.db import get_db_session
from util import get_datetime
from ..enums import TransactionStatus
from ..event import TransactionCompletedEvent
from ..model import EthBlocks, Transaction

TRANSACTION_COMPLETE_TOPIC = AsyncWeb3.keccak(
    text="TransactionComplete(bytes16,bytes16,string,address,address,uint256)"
)


@trace_class()
class EthListener:
    def __init__(
        self,
        event_publisher: EventPublisher,
        product_service: ProductService,
        price_service: PriceService,
        rpc_url: str = RPC_URL,
        contract_address: str = CHRIMA_PAYMENT_CONTRACT_ADDRESS,
        abi: list[dict] = CHRIMA_PAYMENT_CONTRACT_ABI,
    ):
        self._event_publisher = event_publisher
        self._product_service = product_service
        self._price_service = price_service
        self._w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
        self._contract: AsyncContract = self._w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=abi,
        )
        self._logger = logging.getLogger("eth_listener")

    async def listen(self, poll_interval: int) -> None:
        prev_block = await self._get_latest_block()

        if prev_block is not None:
            params = self._build_filter_params(
                prev_block.from_block, prev_block.to_block
            )
            logs = await self._w3.eth.get_logs(params)

            async with get_db_session() as db_sess:
                for log in logs:
                    await self._process_event(log, db_sess)

                await db_sess.execute(
                    sa.update(EthBlocks)
                    .where(EthBlocks.id == prev_block.id)
                    .values(completed=True)
                )

                await db_sess.commit()

            from_block, on_chain = prev_block.from_block, False
        else:
            from_block, on_chain = await self._w3.eth.block_number, True

        while True:
            cur_block = await self._w3.eth.block_number
            self._logger.info("Current block '%s'", cur_block)

            if cur_block > from_block:
                start_block = from_block + 1 if not on_chain else from_block
                # Alchemy Free Plan restricts you to query a block range of 10
                to_block = min(from_block + 10, cur_block)

                filter_params = self._build_filter_params(start_block, to_block)

                # Checkpointing
                async with get_db_session() as db_sess:
                    prev_block_id = await db_sess.scalar(
                        sa.insert(EthBlocks)
                        .values(
                            address=filter_params["address"],
                            from_block=filter_params["fromBlock"],
                            to_block=filter_params["toBlock"],
                            topics=[f"0x{t.hex()}" for t in filter_params["topics"]],
                        )
                        .returning(EthBlocks.id)
                    )
                    await db_sess.commit()

                self._logger.info("Fetching blocks from %s to %s", start_block, to_block)
                logs = await self._w3.eth.get_logs(filter_params)
                self._logger.info("Found %s logs", len(logs))
                async with get_db_session() as db_sess:
                    for log in logs:
                        await self._process_event(log, db_sess)

                    await db_sess.execute(
                        sa.update(EthBlocks)
                        .where(EthBlocks.id == prev_block_id)
                        .values(completed=True)
                    )
                    await db_sess.commit()

                from_block = to_block
                on_chain = False

            await asyncio.sleep(poll_interval)

    async def _process_event(self, log: LogReceipt, db_sess: AsyncSession) -> None:
        processed_log = self._contract.events.TransactionComplete().process_log(log)
        event = dict(processed_log["args"])

        product_id = UUID(event["product_id"].hex())
        try:
            await self._product_service.get_by_id(product_id, db_sess)
        except ProductNotFoundException as e:
            self._logger.error(str(e))
            return
        
        price_id = UUID(event["price_id"].hex())
        try:
            await self._price_service.get_by_id(price_id, db_sess)
        except PriceNotFoundException as e:
            self._logger.error(str(e))
            return

        transaction = Transaction(
            product_id=product_id,
            price_id=price_id,
            platform_user_id=event["user_id"],
            sender=event["sender"],
            recipient=event["recipient"],
            address=event["sender"],
            amount=float(event["amount"]),
            status=TransactionStatus.COMPLETE,
            timestamp=int(get_datetime().timestamp()),
        )

        db_sess.add(transaction)
        await db_sess.flush()
        await db_sess.refresh(transaction)
        await self._event_publisher.publish(
            TransactionCompletedEvent(
                transaction_id=transaction.id,
                product_id=transaction.product_id,
                price_id=transaction.price_id,
                amount=transaction.amount / 10**6,
                platform_user_id=transaction.platform_user_id,
            ),
            db_sess=db_sess,
        )

        self._logger.info(
            "Persisted transaction id=%s product=%s price=%s user=%s sender=%s recipient=%s",
            transaction.id,
            transaction.product_id,
            transaction.price_id,
            transaction.platform_user_id,
            transaction.sender,
            transaction.recipient,
        )

    async def _get_latest_block(self) -> EthBlocks | None:
        async with get_db_session() as db_sess:
            return await db_sess.scalar(
                sa.select(EthBlocks).order_by(EthBlocks.created_at.desc()).limit(1)
            )

    def _build_filter_params(self, from_block: int, to_block: int) -> FilterParams:
        return {
            "address": self._contract.address,
            "fromBlock": from_block,
            "toBlock": to_block,
            "topics": [TRANSACTION_COMPLETE_TOPIC],
        }
