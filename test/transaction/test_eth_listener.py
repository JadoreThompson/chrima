import asyncio
import json
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from web3 import AsyncWeb3

from chrima.event_bus.model import EventOutbox
from chrima.event_bus.service.outbox import OutboxPoller
from chrima.price.enums import Currency, PriceType
from chrima.price.event.deserialiser import PriceEventDeserialiser
from chrima.price.service.sync import PriceSyncService
from chrima.product.enums import FulfilmentType
from chrima.product.event.deserialiser import ProductEventDeserialiser
from chrima.product.service.sync import ProductSyncService
from chrima.transaction.enums import TransactionStatus
from chrima.transaction.event import TransactionEventDeserialiser
from chrima.transaction.event.enums import TransactionEventType
from chrima.transaction.model import EthBlocks, Transaction
from chrima.transaction.service.listener import EthListener
from chrima.workspace.enums import MessagePlatformType
from config import (
    CHRIMA_PAYMENT_CONTRACT_ABI,
    CHRIMA_PAYMENT_CONTRACT_ADDRESS,
    RPC_URL,
    SIGNER_PRIVATE_KEY,
    SRC_PATH,
)
from infra.db.session import get_db_session
from infra.kafka import AsyncKafkaProducer


@pytest.fixture
def usdt_contract_address():
    return os.environ["USDT_ADDRESS"]


@pytest.fixture
def usdt_contract_abi() -> list[dict]:
    fpath = os.path.join(SRC_PATH, "resources", "contract", "TestUSDT.json")
    if not os.path.exists(fpath):
        raise FileNotFoundError(f"ABI not found at {fpath}")

    with open(fpath, "r") as f:
        return json.load(f)


@pytest.fixture
def wallet_address():
    return os.environ["WALLET_ADDRESS"]


@pytest.fixture
def eth_listener(event_publisher, product_service, price_service):
    return EthListener(
        event_publisher=event_publisher,
        product_service=product_service,
        price_service=price_service,
    )


@pytest_asyncio.fixture(loop_scope="session")
async def w3():
    return AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URL))


@pytest_asyncio.fixture(loop_scope="session")
async def chrima_payment_contract(w3):
    return w3.eth.contract(
        address=AsyncWeb3.to_checksum_address(CHRIMA_PAYMENT_CONTRACT_ADDRESS),
        abi=CHRIMA_PAYMENT_CONTRACT_ABI,
    )


@pytest_asyncio.fixture(loop_scope="session")
async def usdt_contract(w3, usdt_contract_address, usdt_contract_abi):
    return w3.eth.contract(
        address=AsyncWeb3.to_checksum_address(usdt_contract_address),
        abi=usdt_contract_abi,
    )


@pytest_asyncio.fixture(loop_scope="session")
async def kafka_producer():
    producer = AsyncKafkaProducer.create()

    try:
        await producer.start()
        yield producer
    finally:
        await producer.stop()


@pytest.fixture
def product_sync_service(w3, chrima_payment_contract, wallet_service):
    return ProductSyncService(
        w3=w3,
        contract=chrima_payment_contract,
        signer_private_key=SIGNER_PRIVATE_KEY,
        deserialiser=ProductEventDeserialiser(),
        wallet_service=wallet_service,
    )


@pytest.fixture
def price_sync_service(w3, chrima_payment_contract):
    return PriceSyncService(
        w3=w3,
        contract=chrima_payment_contract,
        signer_private_key=SIGNER_PRIVATE_KEY,
        deserialiser=PriceEventDeserialiser(),
    )


@pytest.fixture
def outbox_event_poller(kafka_producer):
    deserialisers = {
        "price": PriceEventDeserialiser(),
        "product": ProductEventDeserialiser(),
        "transaction": TransactionEventDeserialiser(),
    }
    return OutboxPoller(
        kafka_producer=kafka_producer,
        deserialisers=deserialisers,
        interval=1,
        batch_size=10,
    )


@pytest.fixture
def signer_account(w3):
    return w3.eth.account.from_key(SIGNER_PRIVATE_KEY)


@asynccontextmanager
async def _run(coro):
    task = asyncio.create_task(coro)
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio(loop_scope="session")
async def test_stores_transaction_emits_event(
    eth_listener: EthListener,
    user_service,
    workspace_service,
    wallet_service,
    product_service,
    price_service,
    faker,
    product_sync_service,
    price_sync_service,
    outbox_event_poller,
    w3,
    chrima_payment_contract,
    usdt_contract,
    signer_account,
    wallet_address,
    create_drop_tables,
):
    """Syncs the created product and price to the contract, triggers
    processTransaction on-chain, then verifies that the EthListener picks up
    the TransactionComplete event and persists a Transaction record, an
    EthBlocks checkpoint, and emits a TransactionCompletedEvent to the outbox."""

    platform_user_id = str(uuid4().int)[:18]
    # wallet_address = "0x0000000000000000000000000000000000000001"

    async with _run(outbox_event_poller.run()):
        async with _run(price_sync_service.run()):
            async with _run(product_sync_service.run()):
                async with _run(eth_listener.listen(1)):
                    async with get_db_session() as db_sess:
                        owner = await user_service.create(
                            username=faker.user_name(),
                            email=faker.email(),
                            password=faker.password(),
                            db_sess=db_sess,
                        )
                        workspace = await workspace_service.create(
                            user_id=owner.id,
                            name=faker.user_name() + "-ws",
                            platform=MessagePlatformType.DISCORD,
                            external_id=str(uuid4().int)[:18],
                            notification_channel_id="ch_test",
                            db_sess=db_sess,
                        )
                        wallet = await wallet_service.create(
                            workspace_id=workspace.id,
                            name="main",
                            wallet_address=wallet_address,
                            db_sess=db_sess,
                        )
                        product = await product_service.create(
                            workspace_id=workspace.id,
                            name="test-product",
                            description=None,
                            wallet_id=wallet.id,
                            external_url=None,
                            roles=["premium"],
                            fulfilment_type=FulfilmentType.ROLE,
                            db_sess=db_sess,
                        )
                        price = await price_service.create(
                            workspace_id=workspace.id,
                            product_id=product.id,
                            type=PriceType.ONE_TIME,
                            currency=Currency.USD,
                            amount=1.0,
                            db_sess=db_sess,
                        )
                        await db_sess.commit()
                        price_id = price.id
                        usdt_amount = int(Decimal(str(price.amount)) * 10**6)

                    # # Allow the outbox poller and sync services to set the
                    # # on-chain recipient and price before triggering the payment
                    await asyncio.sleep(10)

                    latest_block = await w3.eth.get_block("latest")
                    max_fee = int(latest_block["baseFeePerGas"]) * 3
                    priority_fee = w3.to_wei(2, "gwei")

                    # Mint USDT to the signer so it can pay for the product
                    mint_tx = await usdt_contract.functions.mint(
                        signer_account.address, usdt_amount
                    ).build_transaction(
                        {
                            "from": signer_account.address,
                            "nonce": await w3.eth.get_transaction_count(
                                signer_account.address, "pending"
                            ),
                            "maxFeePerGas": max_fee,
                            "maxPriorityFeePerGas": priority_fee,
                        }
                    )
                    signed_mint = signer_account.sign_transaction(mint_tx)
                    mint_hash = await w3.eth.send_raw_transaction(
                        signed_mint.raw_transaction
                    )
                    mint_receipt = await w3.eth.wait_for_transaction_receipt(mint_hash)
                    assert mint_receipt["status"] == 1, "USDT mint failed"

                    # Approve the ChrimaPayment contract to spend USDT
                    approve_tx = await usdt_contract.functions.approve(
                        chrima_payment_contract.address,
                        usdt_amount,
                    ).build_transaction(
                        {
                            "from": signer_account.address,
                            "nonce": await w3.eth.get_transaction_count(
                                signer_account.address, "pending"
                            ),
                            "maxFeePerGas": max_fee,
                            "maxPriorityFeePerGas": priority_fee,
                        }
                    )
                    signed_approve = signer_account.sign_transaction(approve_tx)
                    approve_hash = await w3.eth.send_raw_transaction(
                        signed_approve.raw_transaction
                    )
                    approve_receipt = await w3.eth.wait_for_transaction_receipt(
                        approve_hash
                    )
                    assert approve_receipt["status"] == 1, "USDT approve failed"

                    await asyncio.sleep(2)

                    # Trigger the on-chain payment; emits TransactionComplete
                    tx = await chrima_payment_contract.functions.processTransaction(
                        product.id.bytes,
                        price_id.bytes,
                        platform_user_id,
                    ).build_transaction(
                        {
                            "from": signer_account.address,
                            "nonce": await w3.eth.get_transaction_count(
                                signer_account.address, "pending"
                            ),
                            "maxFeePerGas": max_fee,
                            # "maxPriorityFeePerGas": priority_fee,
                            "maxPriorityFeePerGas": w3.to_wei(2, "gwei"),
                        }
                    )
                    signed = signer_account.sign_transaction(tx)
                    tx_hash = await w3.eth.send_raw_transaction(signed.raw_transaction)
                    receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
                    assert receipt["status"] == 1, "processTransaction failed"

                    # Allow the eth listener to pick up the event and persist it
                    await asyncio.sleep(15)

    # The eth listener should have persisted a transaction record
    async with get_db_session() as db_sess:
        result = await db_sess.scalars(
            select(Transaction).order_by(Transaction.timestamp.desc())
        )
        txs = result.all()
        assert len(txs) == 1
        tx = txs[0]
        assert tx.product_id == product.id
        assert tx.price_id == price_id
        assert tx.platform_user_id == platform_user_id
        assert tx.sender == signer_account.address
        assert tx.recipient == wallet_address
        assert tx.amount == float(usdt_amount)
        assert tx.status == TransactionStatus.COMPLETE

        # The eth listener should have created (and completed) EthBlocks checkpoints
        blocks = (await db_sess.scalars(select(EthBlocks))).all()
        assert len(blocks) >= 1
        assert sum(b.completed for b in blocks) >= len(blocks) - 1

        # The eth listener should have emitted a transaction completed event
        events = (
            await db_sess.scalars(
                select(EventOutbox).where(
                    EventOutbox.type == TransactionEventType.COMPLETED.value
                )
            )
        ).all()
        assert len(events) == 1
        
        payload = events[0].payload
        assert payload["transaction_id"] == str(tx.id)
        assert payload["product_id"] == str(product.id)
        assert payload["price_id"] == str(price_id)
        assert payload["platform_user_id"] == platform_user_id
        assert payload["amount"] == price.amount
