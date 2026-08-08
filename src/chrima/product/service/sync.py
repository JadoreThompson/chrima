import asyncio
import logging

from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract

from chrima.monitoring import trace_class
from chrima.wallet import WalletService
from chrima.wallet.exception import WalletNotFoundException
from config import KAKFA_PRODUCT_EVENTS_TOPIC
from infra.db import get_db_session
from infra.kafka import AsyncKafkaConsumer
from ..event import (
    ProductEventDeserialiser,
    ProductEventType,
    ProductWalletUpdatedEvent,
)


@trace_class()
class ProductSyncService:
    def __init__(
        self,
        w3: AsyncWeb3,
        contract: AsyncContract,
        signer_private_key: str,
        deserialiser: ProductEventDeserialiser,
        wallet_service: WalletService,
    ):
        self._w3 = w3
        self._contract = contract
        self._signer_private_key = signer_private_key
        self._deserialiser = deserialiser
        self._wallet_service = wallet_service
        self._stopped = False
        self._logger = logging.getLogger("product_sync_service")

    async def run(self):
        self._logger.info("Init")
        consumer = AsyncKafkaConsumer.create(
            KAKFA_PRODUCT_EVENTS_TOPIC,
            group_id="product_sync_group",
            enable_auto_commit=False,
        )

        try:
            await consumer.start()            
            
            async for msg in consumer:
                event = self._deserialiser.deserialise_json(msg.value)
                if event.type == ProductEventType.WALLET_UPDATED:
                    await self.handle_wallet_updated(event)
                await consumer.commit()
        finally:
            await consumer.stop()

    async def handle_wallet_updated(self, event: ProductWalletUpdatedEvent) -> None:
        async with get_db_session() as db_sess:
            try:
                wallet = await self._wallet_service.get_by_id(event.wallet_id, db_sess)
            except WalletNotFoundException:
                self._logger.info(f"Wallet '%s' not found", event.wallet_id)
                return

            account = self._w3.eth.account.from_key(self._signer_private_key)

            for attempt in range(3):
                try:
                    latest_block = await self._w3.eth.get_block("latest")
                    max_fee = int(latest_block["baseFeePerGas"]) * 3

                    tx = await self._contract.functions.setProductRecipient(
                        event.product_id.bytes,
                        AsyncWeb3.to_checksum_address(wallet.wallet_address),
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
                        "setProductRecipient tx hash=%s product_id=%s wallet=%s status=%s",
                        tx_hash.hex(),
                        event.product_id,
                        wallet.wallet_address,
                        receipt["status"],
                    )
                    return
                except Exception as e:
                    if "nonce too low" in str(e) and attempt < 2:
                        self._logger.warning(
                            "Nonce conflict, retrying (%s/3)", attempt + 1
                        )
                        await asyncio.sleep(1)
                        continue
                    raise

    def stop(self):
        self._stopped = True
