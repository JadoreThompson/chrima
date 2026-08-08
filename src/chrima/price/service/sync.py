import asyncio
import logging
from decimal import Decimal

from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract

from chrima.monitoring import trace_class
from config import KAKFA_PRICE_EVENTS_TOPIC
from infra.kafka import AsyncKafkaConsumer
from ..event import PriceEventDeserialiser, PriceEventType, PriceUpdatedEvent


@trace_class()
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
        self._logger.info("Starting PriceSyncService")

        consumer = AsyncKafkaConsumer.create(
            KAKFA_PRICE_EVENTS_TOPIC,
            group_id="price_sync_group",
            enable_auto_commit=False,
        )

        try:
            self._logger.info(
                "Starting Kafka consumer topic=%s",
                KAKFA_PRICE_EVENTS_TOPIC,
            )

            await consumer.start()

            self._logger.info("Kafka consumer started")

            async for msg in consumer:
                self._logger.debug(
                    "Received Kafka message: %s",
                    msg.value,
                )

                event = self._deserialiser.deserialise_json(msg.value)

                self._logger.info(
                    "Deserialised event type=%s",
                    event.type,
                )

                if event.type == PriceEventType.PRICE_UPDATED:
                    self._logger.info(
                        "Processing PRICE_UPDATED event price_id=%s amount=%s",
                        event.price_id,
                        event.amount,
                    )

                    await self._handle_price_updated(event)

        except Exception:
            self._logger.exception("PriceSyncService failed")
            raise

        finally:
            self._logger.info("Stopping Kafka consumer")
            await consumer.stop()
            self._logger.info("Kafka consumer stopped")

    async def _handle_price_updated(self, event: PriceUpdatedEvent) -> None:
        account = self._w3.eth.account.from_key(self._signer_private_key)

        self._logger.info(
            "Preparing price update transaction wallet=%s price_id=%s",
            account.address,
            event.price_id,
        )

        usd_amount = int(Decimal(str(event.amount)) * 10**6)

        self._logger.debug(
            "Converted price amount raw=%s usd_amount=%s",
            event.amount,
            usd_amount,
        )

        for attempt in range(3):
            try:
                self._logger.info(
                    "Building transaction attempt=%s/3",
                    attempt + 1,
                )

                latest_block = await self._w3.eth.get_block("latest")

                max_fee = int(latest_block["baseFeePerGas"]) * 3
                priority_fee = self._w3.to_wei(2, "gwei")

                nonce = await self._w3.eth.get_transaction_count(
                    account.address,
                    "pending",
                )

                self._logger.debug(
                    "Transaction parameters nonce=%s max_fee=%s priority_fee=%s",
                    nonce,
                    max_fee,
                    priority_fee,
                )

                tx = await self._contract.functions.setPrice(
                    event.price_id.bytes,
                    usd_amount,
                ).build_transaction(
                    {
                        "from": account.address,
                        "nonce": nonce,
                        "maxFeePerGas": max_fee,
                        "maxPriorityFeePerGas": priority_fee,
                    }
                )

                self._logger.info(
                    "Transaction built gas=%s nonce=%s",
                    tx.get("gas"),
                    tx.get("nonce"),
                )

                signed = account.sign_transaction(tx)

                self._logger.debug(
                    "Transaction signed raw_size=%s bytes",
                    len(signed.raw_transaction),
                )

                tx_hash = await self._w3.eth.send_raw_transaction(
                    signed.raw_transaction
                )

                self._logger.info(
                    "Transaction submitted tx_hash=%s",
                    tx_hash.hex(),
                )

                self._logger.info(
                    "Waiting for transaction receipt tx_hash=%s",
                    tx_hash.hex(),
                )

                receipt = await self._w3.eth.wait_for_transaction_receipt(tx_hash)

                self._logger.info(
                    "Transaction confirmed tx_hash=%s price_id=%s amount=%s status=%s block=%s",
                    tx_hash.hex(),
                    event.price_id,
                    event.amount,
                    receipt["status"],
                    receipt["blockNumber"],
                )

                return

            except Exception as e:
                self._logger.exception(
                    "Transaction attempt failed attempt=%s/3 price_id=%s error=%s",
                    attempt + 1,
                    event.price_id,
                    str(e),
                )

                if "nonce too low" in str(e) and attempt < 2:
                    self._logger.warning(
                        "Nonce conflict detected, retrying attempt=%s/3",
                        attempt + 2,
                    )

                    await asyncio.sleep(1)
                    continue

                raise

    def stop(self):
        self._logger.info("Stopping PriceSyncService")

        self._stopped = True
