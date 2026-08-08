from uuid import uuid4

import pytest

from chrima.workspace.enums import MessagePlatformType
from chrima.price.enums import Currency, PriceType
from chrima.product.enums import FulfilmentType
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.transaction.enums import TransactionStatus
from chrima.transaction.exception import TransactionNotFoundException
from chrima.transaction.model import Transaction
from infra.db import get_db_session
from util import get_datetime


@pytest.fixture
def setup_product_price(
    user_service,
    workspace_service,
    wallet_service,
    product_service,
    price_service,
    token_service,
    faker,
):
    async def _setup():
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
                wallet_address="0xwallet",
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
                amount=10.0,
                db_sess=db_sess,
            )
            await db_sess.commit()
            return workspace, product, price.id

    return _setup


@pytest.fixture
def seed_transactions(setup_product_price):
    async def _seed(count: int = 3, sender: str = "0xsender"):
        workspace, product, price_id = await setup_product_price()
        now = int(get_datetime().timestamp())
        txs = []
        async with get_db_session() as db_sess:
            for i in range(count):
                tx = Transaction(
                    product_id=product.id,
                    price_id=price_id,
                    platform_user_id=f"usr_{i}",
                    sender=sender,
                    recipient="0xrecipient",
                    address="0xtoken",
                    amount=10.0 + i,
                    status=TransactionStatus.COMPLETE,
                    timestamp=now + i,
                )
                db_sess.add(tx)
                await db_sess.flush()
                await db_sess.refresh(tx)
                txs.append(tx)
            await db_sess.commit()
        return txs, product.id, price_id

    return _seed


@pytest.mark.asyncio(loop_scope="session")
class TestGetById:
    async def test_returns_transaction(
        self,
        transaction_service,
        seed_transactions,
        create_drop_tables,
    ):
        txs, _, _ = await seed_transactions(1)
        async with get_db_session() as db_sess:
            fetched = await transaction_service.get_by_id(txs[0].id, db_sess)
            assert fetched.id == txs[0].id
            assert fetched.amount == 10.0

    async def test_raises_when_not_found(self, transaction_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(TransactionNotFoundException):
                await transaction_service.get_by_id(uuid4(), db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestListBySender:
    async def test_returns_matching(
        self, transaction_service, seed_transactions, create_drop_tables
    ):
        txs, _, _ = await seed_transactions(3, sender="0xalice")
        await seed_transactions(2, sender="0xbob")

        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_sender(
                "0xalice",
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 3

    async def test_returns_empty_when_none(
        self, transaction_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_sender(
                "0xnobody",
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 0

    async def test_orders_by_timestamp_desc(
        self, transaction_service, seed_transactions, create_drop_tables
    ):
        txs, _, _ = await seed_transactions(3)

        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_sender(
                "0xsender",
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            timestamps = [t.timestamp for t in result.data]
            assert timestamps == sorted(timestamps, reverse=True)

    async def test_paginates(
        self, transaction_service, seed_transactions, create_drop_tables
    ):
        txs, _, _ = await seed_transactions(3)

        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_sender(
                "0xsender",
                page=1,
                limit=2,
                db_sess=db_sess,
            )
            assert result.size == 2
            assert result.has_next is True

            result2 = await transaction_service.list_by_sender(
                "0xsender",
                page=2,
                limit=2,
                db_sess=db_sess,
            )
            assert result2.size == 1
            assert result2.has_next is False


@pytest.mark.asyncio(loop_scope="session")
class TestListByProduct:
    async def test_returns_matching(
        self, transaction_service, seed_transactions, create_drop_tables
    ):
        txs, product_id, _ = await seed_transactions(2)

        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_product(
                product_id,
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 2

    async def test_returns_empty_when_none(
        self, transaction_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_product(
                uuid4(),
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 0

    async def test_paginates(
        self, transaction_service, seed_transactions, create_drop_tables
    ):
        txs, product_id, _ = await seed_transactions(3)

        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_product(
                product_id,
                page=1,
                limit=2,
                db_sess=db_sess,
            )
            assert result.size == 2
            assert result.has_next is True

    async def test_orders_by_timestamp_desc(
        self, transaction_service, seed_transactions, create_drop_tables
    ):
        txs, product_id, _ = await seed_transactions(3)

        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_product(
                product_id,
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            timestamps = [t.timestamp for t in result.data]
            assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.asyncio(loop_scope="session")
class TestListByPrice:
    async def test_returns_matching(
        self, transaction_service, seed_transactions, create_drop_tables
    ):
        txs, _, price_id = await seed_transactions(2)

        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_price(
                price_id,
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 2

    async def test_returns_empty_when_none(
        self, transaction_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_price(
                uuid4(),
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 0

    async def test_paginates(
        self, transaction_service, seed_transactions, create_drop_tables
    ):
        txs, _, price_id = await seed_transactions(3)

        async with get_db_session() as db_sess:
            result = await transaction_service.list_by_price(
                price_id,
                page=1,
                limit=2,
                db_sess=db_sess,
            )
            assert result.size == 2
            assert result.has_next is True
