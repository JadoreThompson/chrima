import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from web3 import AsyncWeb3

from chrima.price.event import PriceEventDeserialiser, PriceUpdatedEvent
from chrima.price.service.sync import PriceSyncService


@pytest.fixture
def mock_w3():
    w3 = MagicMock(spec=AsyncWeb3)
    w3.eth = MagicMock()
    w3.eth.account = MagicMock()
    w3.eth.get_block = AsyncMock()
    w3.eth.get_transaction_count = AsyncMock()
    w3.eth.send_raw_transaction = AsyncMock()
    w3.eth.wait_for_transaction_receipt = AsyncMock()
    w3.to_wei.return_value = 2_000_000_000
    return w3


@pytest.fixture
def mock_contract():
    contract = MagicMock()
    contract.functions.setPrice.return_value.build_transaction = AsyncMock()
    return contract


@patch("chrima.price.service.sync.AsyncKafkaConsumer")
@pytest.mark.asyncio(loop_scope="session")
async def test_onchain_sets_price(
    MockAsyncKafkaConsumerCls,
    mock_w3,
    mock_contract,
    create_drop_tables,
):
    event = PriceUpdatedEvent(price_id=uuid4(), amount=10.0)
    mock_consumer = AsyncMock()
    MockAsyncKafkaConsumerCls.create.return_value = mock_consumer
    mock_record = MagicMock(value=event.model_dump_json().encode())
    mock_consumer.__aiter__.return_value = [mock_record]

    mock_w3.eth.get_block.return_value = {"baseFeePerGas": 1_000_000_000}
    mock_w3.eth.get_transaction_count.return_value = 5
    mock_w3.eth.send_raw_transaction.return_value = b"\x01" * 32
    mock_w3.eth.wait_for_transaction_receipt.return_value = {"status": 1}
    mock_account = MagicMock()
    mock_account.address = "0xSignerAddress"
    mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"\x02" * 64)
    mock_w3.eth.account.from_key.return_value = mock_account

    price_sync_service = PriceSyncService(
        w3=mock_w3,
        contract=mock_contract,
        signer_private_key="private-key",
        deserialiser=PriceEventDeserialiser(),
    )

    try:
        await asyncio.wait_for(price_sync_service.run(), timeout=5.0)
    except asyncio.CancelledError:
        pass

    mock_contract.functions.setPrice.assert_called_once()
    mock_w3.eth.send_raw_transaction.assert_called_once()
