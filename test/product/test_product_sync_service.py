import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from web3 import AsyncWeb3

from chrima.workspace.enums import MessagePlatformType
from chrima.price.enums import Currency, PriceType
from chrima.product.enums import FulfilmentType
from chrima.product.event import ProductEventDeserialiser, ProductWalletUpdatedEvent
from chrima.product.schema import CreatePriceRequest, ProductResponse
from chrima.product.service.sync import ProductSyncService
from chrima.tokens.enums import TokenChain, TokenStandard
from core.db import get_db_session


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
    contract.functions.setProductRecipient.return_value.build_transaction = AsyncMock()
    return contract


@pytest.fixture
def mock_deserialiser():
    return MagicMock()


@pytest.fixture
def mock_wallet():
    wallet = MagicMock()
    wallet.wallet_address = "0xAbCdEf0000000000000000000000000000000001"
    return wallet


@pytest.fixture
def product_sync_service(mock_w3, mock_contract, mock_deserialiser):
    return ProductSyncService(
        w3=mock_w3,
        contract=mock_contract,
        signer_private_key="0xabc123",
        deserialiser=mock_deserialiser,
    )


@pytest.fixture
def wallet_updated_event():
    return ProductWalletUpdatedEvent(
        product_id=uuid4(),
        wallet_id=uuid4(),
    )


@pytest.fixture
def mock_db_sess(mock_wallet):
    sess = AsyncMock()
    sess.get = AsyncMock(return_value=mock_wallet)
    return sess


@pytest.fixture
def create_wallet(
    user_service, workspace_service, workspace_wallet_service, token_service, faker
):
    async def _setup(
        wallet_address: str = "0xAbCdEf0000000000000000000000000000000001",
    ):
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
            token = await token_service.create(
                name="TST",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xtoken",
                db_sess=db_sess,
            )
            wallet = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="main",
                wallet_address=wallet_address,
                token_ids=[token.id],
                db_sess=db_sess,
            )
            await db_sess.commit()
            return wallet

    return _setup


@patch("chrima.product.service.sync.get_db_session")
@pytest.mark.asyncio(loop_scope="session")
class TestHandleWalletUpdated:

    async def test_calls_set_product_recipient(
        self,
        mock_get_db,
        product_sync_service,
        mock_w3,
        mock_contract,
        mock_db_sess,
        mock_wallet,
        wallet_updated_event,
        create_drop_tables,
    ):
        mock_get_db.return_value.__aenter__.return_value = mock_db_sess

        mock_w3.eth.get_block.return_value = {"baseFeePerGas": 1_000_000_000}
        mock_w3.eth.get_transaction_count.return_value = 5
        mock_w3.eth.send_raw_transaction.return_value = b"\x01" * 32
        mock_w3.eth.wait_for_transaction_receipt.return_value = {"status": 1}

        mock_account = MagicMock()
        mock_account.address = "0xSignerAddress"
        mock_account.sign_transaction.return_value = MagicMock(
            raw_transaction=b"\x02" * 64
        )
        mock_w3.eth.account.from_key.return_value = mock_account

        await product_sync_service.handle_wallet_updated(wallet_updated_event)

        mock_contract.functions.setProductRecipient.assert_called_once_with(
            str(wallet_updated_event.product_id),
            AsyncWeb3.to_checksum_address(mock_wallet.wallet_address),
        )
        mock_contract.functions.setProductRecipient.return_value.build_transaction.assert_called_once()
        mock_w3.eth.send_raw_transaction.assert_called_once()
        mock_w3.eth.wait_for_transaction_receipt.assert_called_once()
        mock_db_sess.get.assert_called_once()

    async def test_retries_on_nonce_conflict(
        self,
        mock_get_db,
        product_sync_service,
        mock_contract,
        mock_db_sess,
        wallet_updated_event,
        create_drop_tables,
    ):
        mock_get_db.return_value.__aenter__.return_value = mock_db_sess

        build_tx = (
            mock_contract.functions.setProductRecipient.return_value.build_transaction
        )
        build_tx.side_effect = [
            Exception("nonce too low"),
            {"data": "0x", "from": "0xSigner"},
        ]

        mock_w3 = product_sync_service._w3
        mock_w3.eth.get_block.return_value = {"baseFeePerGas": 1_000_000_000}
        mock_w3.eth.get_transaction_count.return_value = 5
        mock_w3.eth.send_raw_transaction.return_value = b"\x01" * 32
        mock_w3.eth.wait_for_transaction_receipt.return_value = {"status": 1}

        mock_account = MagicMock()
        mock_account.address = "0xSignerAddress"
        mock_account.sign_transaction.return_value = MagicMock(
            raw_transaction=b"\x02" * 64
        )
        mock_w3.eth.account.from_key.return_value = mock_account

        await product_sync_service.handle_wallet_updated(wallet_updated_event)

        assert build_tx.call_count == 2

    async def test_raises_after_max_retries(
        self,
        mock_get_db,
        product_sync_service,
        mock_contract,
        mock_db_sess,
        wallet_updated_event,
        create_drop_tables,
    ):
        mock_get_db.return_value.__aenter__.return_value = mock_db_sess

        build_tx = (
            mock_contract.functions.setProductRecipient.return_value.build_transaction
        )
        build_tx.side_effect = Exception("nonce too low")

        mock_w3 = product_sync_service._w3
        mock_w3.eth.get_block.return_value = {"baseFeePerGas": 1_000_000_000}
        mock_w3.eth.get_transaction_count.return_value = 5

        mock_account = MagicMock()
        mock_account.address = "0xSignerAddress"
        mock_w3.eth.account.from_key.return_value = mock_account

        with pytest.raises(Exception, match="nonce too low"):
            await product_sync_service.handle_wallet_updated(wallet_updated_event)

        assert build_tx.call_count == 3

    async def test_raises_on_unrecoverable_error(
        self,
        mock_get_db,
        product_sync_service,
        mock_contract,
        mock_db_sess,
        wallet_updated_event,
        create_drop_tables,
    ):
        mock_get_db.return_value.__aenter__.return_value = mock_db_sess

        build_tx = (
            mock_contract.functions.setProductRecipient.return_value.build_transaction
        )
        build_tx.side_effect = Exception("execution reverted")

        mock_w3 = product_sync_service._w3
        mock_w3.eth.get_block.return_value = {"baseFeePerGas": 1_000_000_000}
        mock_w3.eth.get_transaction_count.return_value = 5

        mock_account = MagicMock()
        mock_account.address = "0xSignerAddress"
        mock_w3.eth.account.from_key.return_value = mock_account

        with pytest.raises(Exception, match="execution reverted"):
            await product_sync_service.handle_wallet_updated(wallet_updated_event)

        assert build_tx.call_count == 1


@patch("chrima.product.service.sync.AsyncKafkaConsumer")
@pytest.mark.asyncio(loop_scope="session")
class TestRun:

    @pytest_asyncio.fixture(loop_scope="session")
    async def create_product(
        self,
        user_service,
        workspace_service,
        workspace_wallet_service,
        token_service,
        product_service,
        faker,
    ):
        async def _func() -> ProductResponse:
            async with get_db_session() as db_sess:
                user = await user_service.create(
                    username=faker.user_name(),
                    email=faker.email(),
                    password=faker.password(),
                    db_sess=db_sess,
                )
                wspace = await workspace_service.create(
                    user_id=user.id,
                    name="test-workspace",
                    platform=MessagePlatformType.DISCORD,
                    external_id="123456789",
                    notification_channel_id="111111111",
                    db_sess=db_sess,
                )
                token = await token_service.create(
                    name="TST",
                    standard=TokenStandard.ERC_20,
                    chain=TokenChain.ETH,
                    address="0xtoken",
                    db_sess=db_sess,
                )
                wallet = await workspace_wallet_service.create(
                    workspace_id=wspace.id,
                    name="test-wallet",
                    wallet_address="0xAbCdEf0000000000000000000000000000000001",
                    token_ids=[token.id],
                    db_sess=db_sess,
                )
                product = await product_service.create(
                    workspace_id=wspace.id,
                    name="test-product",
                    description=None,
                    wallet_id=wallet.id,
                    external_url=None,
                    roles=["111111111111111111"],
                    fulfilment_type=FulfilmentType.ROLE,
                    price_data=CreatePriceRequest(
                        type=PriceType.ONE_TIME,
                        currency=Currency.USD,
                        amount=10.0,
                    ),
                    db_sess=db_sess,
                )
                await db_sess.commit()
                return product

        return _func

    async def test_onchain_sets_product_recipient(
        self,
        MockAsyncKafkaConsumerCls,
        create_product,
        mock_w3,
        mock_contract,
        create_drop_tables,
    ):
        product = await create_product()

        event = ProductWalletUpdatedEvent(
            product_id=product.id, wallet_id=product.wallet_id
        )
        mock_consumer = AsyncMock()
        MockAsyncKafkaConsumerCls.create.return_value = mock_consumer
        mock_record = MagicMock(value=event.model_dump_json().encode())
        mock_consumer.__aiter__.return_value = [mock_record]

        product_sync_service = ProductSyncService(
            w3=mock_w3,
            contract=mock_contract,
            signer_private_key="private-key",
            deserialiser=ProductEventDeserialiser(),
        )

        try:
            await asyncio.wait_for(product_sync_service.run(), timeout=5.0)
        except asyncio.CancelledError:
            pass

        mock_contract.functions.setProductRecipient.assert_called_once()
        mock_w3.eth.send_raw_transaction.assert_called_once()
