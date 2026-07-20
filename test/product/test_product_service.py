from uuid import uuid4

import pytest
from sqlalchemy import select

from chrima.workspace.enums import MessagePlatformType
from chrima.price.enums import Currency, PriceType
from chrima.price.model import Price
from chrima.product.enums import FulfilmentType
from chrima.product.exception import ProductNotFoundException
from chrima.product.model import Product
from chrima.tokens.enums import TokenChain, TokenStandard
from core.db import get_db_session


@pytest.fixture
def setup_workspace_wallet(
    user_service,
    workspace_service,
    workspace_wallet_service,
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
            await db_sess.commit()
            return workspace, wallet

    return _setup


@pytest.mark.asyncio(loop_scope="session")
class TestCreate:

    async def test_creates_product(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            product = await product_service.create(
                workspace_id=workspace.id,
                name="test-product",
                description="A test product",
                wallet_id=wallet.id,
                external_url="https://example.com",
                roles=["premium"],
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )

            assert product.name == "test-product"
            assert product.description == "A test product"
            assert product.wallet_id == wallet.id
            assert product.external_url == "https://example.com"
            assert product.roles == ["premium"]
            assert product.fulfilment_type == FulfilmentType.ROLE
            assert product.created_at is not None
            assert product.updated_at is not None

            row = await db_sess.get(Product, product.id)
            assert row is not None

    async def test_creates_without_optional_fields(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            product = await product_service.create(
                workspace_id=workspace.id,
                name="minimal-product",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.INVITE,
                db_sess=db_sess,
            )

            assert product.name == "minimal-product"
            assert product.description is None
            assert product.external_url is None
            assert product.roles is None
            assert product.fulfilment_type == FulfilmentType.INVITE

    async def test_nonexistent_workspace_raises(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await product_service.create(
                    workspace_id=uuid4(),
                    name="test",
                    description=None,
                    wallet_id=wallet.id,
                    external_url=None,
                    roles=None,
                    fulfilment_type=FulfilmentType.ROLE,
                    db_sess=db_sess,
                )

    async def test_nonexistent_wallet_raises(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await product_service.create(
                    workspace_id=workspace.id,
                    name="test",
                    description=None,
                    wallet_id=uuid4(),
                    external_url=None,
                    roles=None,
                    fulfilment_type=FulfilmentType.ROLE,
                    db_sess=db_sess,
                )


@pytest.mark.asyncio(loop_scope="session")
class TestGetById:

    async def test_returns_product(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            created = await product_service.create(
                workspace_id=workspace.id,
                name="get-by-id",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )

            fetched = await product_service.get_by_id(created.id, db_sess)
            assert fetched.id == created.id
            assert fetched.name == "get-by-id"

    async def test_raises_when_not_found(self, product_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(ProductNotFoundException):
                await product_service.get_by_id(uuid4(), db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestGetByWorkspace:

    async def test_returns_product(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            created = await product_service.create(
                workspace_id=workspace.id,
                name="ws-product",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )

            fetched = await product_service.get_by_workspace(
                created.id, workspace.id, db_sess
            )
            assert fetched.id == created.id

    async def test_raises_when_not_found(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            with pytest.raises(ProductNotFoundException):
                await product_service.get_by_workspace(uuid4(), workspace.id, db_sess)

    async def test_raises_when_wrong_workspace(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            created = await product_service.create(
                workspace_id=workspace.id,
                name="wrong-ws",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )

            with pytest.raises(ProductNotFoundException):
                await product_service.get_by_workspace(created.id, uuid4(), db_sess)

            row = await db_sess.get(Product, created.id)
            assert row is not None


@pytest.mark.asyncio(loop_scope="session")
class TestListByWorkspace:

    async def test_returns_products(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            p1 = await product_service.create(
                workspace_id=workspace.id,
                name="product-a",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )
            p2 = await product_service.create(
                workspace_id=workspace.id,
                name="product-b",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.INVITE,
                db_sess=db_sess,
            )

            result = await product_service.list_by_workspace(
                workspace.id,
                page=1,
                limit=10,
                db_sess=db_sess,
            )

            assert result.page == 1
            assert result.size == 2
            assert result.has_next is False
            assert {p.id for p in result.data} == {p1.id, p2.id}

    async def test_paginates(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            for _ in range(3):
                await product_service.create(
                    workspace_id=workspace.id,
                    name="paged-product",
                    description=None,
                    wallet_id=wallet.id,
                    external_url=None,
                    roles=None,
                    fulfilment_type=FulfilmentType.ROLE,
                    db_sess=db_sess,
                )

            result = await product_service.list_by_workspace(
                workspace.id,
                page=1,
                limit=2,
                db_sess=db_sess,
            )
            assert result.size == 2
            assert result.has_next is True

    async def test_returns_empty_when_no_products(
        self, product_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await product_service.list_by_workspace(
                uuid4(),
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 0
            assert result.has_next is False


@pytest.mark.asyncio(loop_scope="session")
class TestUpdate:

    async def test_updates_name(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            created = await product_service.create(
                workspace_id=workspace.id,
                name="original",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )

            updated = await product_service.update(
                created.id,
                workspace.id,
                name="updated-name",
                db_sess=db_sess,
            )
            assert updated.name == "updated-name"

            row = await db_sess.get(Product, created.id)
            assert row.name == "updated-name"

    async def test_updates_description(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            created = await product_service.create(
                workspace_id=workspace.id,
                name="desc-test",
                description="old desc",
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )

            updated = await product_service.update(
                created.id,
                workspace.id,
                description="new desc",
                db_sess=db_sess,
            )
            assert updated.description == "new desc"

    async def test_raises_when_not_found(
        self, product_service, setup_workspace_wallet, create_drop_tables
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            with pytest.raises(ProductNotFoundException):
                await product_service.update(
                    uuid4(), workspace.id, name="x", db_sess=db_sess
                )

    async def test_raises_when_wrong_workspace(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            created = await product_service.create(
                workspace_id=workspace.id,
                name="wrong-ws-upd",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )

            with pytest.raises(ProductNotFoundException):
                await product_service.update(
                    created.id, uuid4(), name="x", db_sess=db_sess
                )

            row = await db_sess.get(Product, created.id)
            assert row.name == "wrong-ws-upd"


@pytest.mark.asyncio(loop_scope="session")
class TestDelete:

    async def test_deletes_product(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            created = await product_service.create(
                workspace_id=workspace.id,
                name="to-delete",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )

            await product_service.delete(created.id, workspace.id, db_sess)

        async with get_db_session() as db_sess:
            row = await db_sess.get(Product, created.id)
            assert row is None

    async def test_raises_when_not_found(
        self, product_service, setup_workspace_wallet, create_drop_tables
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            with pytest.raises(ProductNotFoundException):
                await product_service.delete(uuid4(), workspace.id, db_sess)

    async def test_raises_when_wrong_workspace(
        self,
        product_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            created = await product_service.create(
                workspace_id=workspace.id,
                name="wrong-ws-del",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )

            with pytest.raises(ProductNotFoundException):
                await product_service.delete(created.id, uuid4(), db_sess)

            row = await db_sess.get(Product, created.id)
            assert row is not None

    async def test_cascade_deletes_prices(
        self,
        product_service,
        price_service,
        setup_workspace_wallet,
        create_drop_tables,
    ):
        workspace, wallet = await setup_workspace_wallet()
        async with get_db_session() as db_sess:
            created = await product_service.create(
                workspace_id=workspace.id,
                name="cascade-test",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                db_sess=db_sess,
            )
            await price_service.create(
                workspace_id=workspace.id,
                product_id=created.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=10.0,
                db_sess=db_sess,
            )
            price_row = await db_sess.scalar(
                select(Price).where(Price.product_id == created.id)
            )
            assert price_row is not None

            await product_service.delete(created.id, workspace.id, db_sess)

        async with get_db_session() as db_sess:
            price_row = await db_sess.scalar(
                select(Price).where(Price.product_id == created.id)
            )
            assert price_row is None
