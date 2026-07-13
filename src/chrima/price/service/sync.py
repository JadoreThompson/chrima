import asyncio
import logging
from decimal import Decimal

from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract

from config import KAKFA_PRICE_EVENTS_TOPIC
from core.kafka import AsyncKafkaConsumer
from ..event import PriceEventDeserialiser, PriceEventType, PriceUpdatedEvent


class PriceSyncService:
    def __init__(
        self,
        w3: AsyncWeb3,
        contract: AsyncContract,
        signer_private_key: str,
        deserialiser: PriceEventDeserialiser,
        interval: float = 5,
    ):
        self._w3 = w3
        self._contract = contract
        self._signer_private_key = signer_private_key
        self._interval = interval
        self._deserialiser = deserialiser
        self._stopped = False
        self._logger = logging.getLogger("price_sync_service")

    async def run(self):
        self._logger.info("Starting PriceSyncService (interval=%ss)", self._interval)
        consumer = AsyncKafkaConsumer.create(KAKFA_PRICE_EVENTS_TOPIC)

        try:
            await consumer.start()

            async for msg in consumer:
                event = self._deserialiser.deserialise_json(msg.value)
                if event.type == PriceEventType.PRICE_UPDATED:
                    await self._handle_price_updated(event)
        finally:
            await consumer.stop()

    async def _handle_price_updated(self, event: PriceUpdatedEvent) -> None:
        account = self._w3.eth.account.from_key(self._signer_private_key)
        usd_amount = int(Decimal(str(event.amount)) * 10**6)

        for attempt in range(3):
            try:
                latest_block = await self._w3.eth.get_block("latest")
                max_fee = int(latest_block["baseFeePerGas"]) * 3

                tx = await self._contract.functions.setPrice(
                    str(event.price_id), usd_amount
                ).build_transaction(
                    {
                        "from": account.address,
                        "nonce": await self._w3.eth.get_transaction_count(
                            account.address, "pending"
                        ),
                        "maxFeePerGas": max_fee,
                        "maxPriorityFeePerGas": self._w3.to_wei(2, "gwei"),
                    }
                )

                signed = account.sign_transaction(tx)
                tx_hash = await self._w3.eth.send_raw_transaction(
                    signed.raw_transaction
                )
                receipt = await self._w3.eth.wait_for_transaction_receipt(tx_hash)

                self._logger.info(
                    "setPrice tx hash=%s price_id=%s amount=%s status=%s",
                    tx_hash.hex(),
                    event.price_id,
                    event.amount,
                    receipt["status"],
                )
                return
            except Exception as e:
                if "nonce too low" in str(e) and attempt < 2:
                    self._logger.warning("Nonce conflict, retrying (%s/3)", attempt + 1)
                    await asyncio.sleep(1)
                    continue
                raise

    def stop(self):
        self._stopped = True
