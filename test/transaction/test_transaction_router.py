from uuid import uuid4

import pytest

from chrima.message_platform.enums import MessagePlatformType
from chrima.price.enums import Currency, PriceType
from chrima.price.schema import CreatePriceRequest
from chrima.product.enums import FulfilmentType
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.transaction.enums import TransactionStatus
from chrima.transaction.model import Transaction
from core.db import get_db_session
from util import get_datetime


@pytest.fixture
def seed_data(
    user_service,
    workspace_service,
    workspace_wallet_service,
    product_service,
    price_service,
    token_service,
    faker,
):
    async def _seed(count: int = 1, sender: str = "0xsender"):
        async with get_db_session() as db_sess:
            owner = await user_service.create(
                username=faker.user_name(),
                email=faker.email(),
                password=faker.password(),
                db_sess=db_sess,
            )
            workspace = await workspace_service.create(
                user_id=owner.id,
                name="tx-ws",
                platform=MessagePlatformType.DISCORD,
                external_id="ext_tx",
                notification_channel_id="ch_tx",
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
                wallet_address="0xwallet",
                token_ids=[token.id],
                db_sess=db_sess,
            )
            product = await product_service.create(
                workspace_id=workspace.id,
                name="tx-product",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                price_data=CreatePriceRequest(
                    product_id=uuid4(),
                    type=PriceType.ONE_TIME,
                    currency=Currency.USD,
                    amount=10.0,
                ),
                db_sess=db_sess,
            )

            data = await price_service.list_by_product(
                product.id, workspace.id, 1, 1, db_sess
            )
            price = data.data[0]
            now = int(get_datetime().timestamp())
            txs = []
            for i in range(count):
                tx = Transaction(
                    id=uuid4(),
                    product_id=product.id,
                    price_id=price.id,
                    platform_user_id=f"usr_{i}",
                    sender=sender,
                    recipient="0xrecipient",
                    address="0xtoken",
                    amount=10.0 + i,
                    status=TransactionStatus.COMPLETE,
                    timestamp=now + i,
                )
                db_sess.add(tx)
                txs.append(tx)
            await db_sess.commit()
        return txs, product.id, price.id

    return _seed


@pytest.mark.asyncio(loop_scope="session")
class TestGetTransaction:

    async def test_200_returns_transaction(self, client, seed_data, create_drop_tables):
        txs, _, _ = await seed_data(1)

        rsp = await client.get(f"/transactions/{txs[0].id}")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["id"] == str(txs[0].id)
        assert data["amount"] == 10.0

    async def test_404_on_nonexistent(self, client, create_drop_tables):
        rsp = await client.get(f"/transactions/{uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(self, client, create_drop_tables):
        rsp = await client.get("/transactions/not-a-uuid")
        assert rsp.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
class TestListTransactions:

    async def test_200_returns_by_sender(self, client, seed_data, create_drop_tables):
        await seed_data(3, sender="0xsender")

        rsp = await client.get("/transactions/?sender=0xsender&limit=10")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["size"] == 3

    async def test_200_filters_by_sender(self, client, seed_data, create_drop_tables):
        await seed_data(2, sender="0xalice")
        await seed_data(1, sender="0xbob")

        rsp = await client.get("/transactions/?sender=0xalice&limit=10")
        assert rsp.status_code == 200
        assert rsp.json()["size"] == 2

    async def test_200_filters_by_product(self, client, seed_data, create_drop_tables):
        txs, product_id, _ = await seed_data(2)

        rsp = await client.get(f"/transactions/?product_id={product_id}&limit=10")
        assert rsp.status_code == 200
        assert rsp.json()["size"] == 2

    async def test_200_filters_by_price(self, client, seed_data, create_drop_tables):
        txs, _, price_id = await seed_data(2)

        rsp = await client.get(f"/transactions/?price_id={price_id}&limit=10")
        assert rsp.status_code == 200
        assert rsp.json()["size"] == 2

    async def test_200_empty_when_no_match(self, client, create_drop_tables):
        rsp = await client.get("/transactions/?sender=0xnobody&limit=10")
        assert rsp.status_code == 200
        assert rsp.json()["size"] == 0

    async def test_422_on_invalid_page(self, client, create_drop_tables):
        rsp = await client.get("/transactions/?page=0")
        assert rsp.status_code == 422

    async def test_422_on_excessive_limit(self, client, create_drop_tables):
        rsp = await client.get("/transactions/?limit=200")
        assert rsp.status_code == 422
