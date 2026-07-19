from uuid import uuid4

import pytest
from sqlalchemy import select

from chrima.workspace.enums import MessagePlatformType
from chrima.price.enums import Currency, PriceType, RecurringInterval
from chrima.price.exception import PriceNotFoundException
from chrima.price.model import Price, PriceToken
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.product.enums import FulfilmentType
from chrima.price.schema import CreatePriceRequest
from core.db import get_db_session


@pytest.fixture
def setup_workspace_product(
    user_service,
    workspace_service,
    workspace_wallet_service,
    product_service,
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
            product = await product_service.create(
                workspace_id=workspace.id,
                name="test-product",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=["premium"],
                fulfilment_type=FulfilmentType.ROLE,
                price_data=CreatePriceRequest(
                    workspace_id=workspace.id,
                    product_id=uuid4(),
                    type=PriceType.ONE_TIME,
                    currency=Currency.USD,
                    amount=10.0,
                ),
                db_sess=db_sess,
            )
            await db_sess.commit()
            return workspace, product, token

    return _setup


@pytest.mark.asyncio(loop_scope="session")
class TestCreate:

    async def test_creates_price(
        self, price_service, token_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            price = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=19.99,
                active=True,
                db_sess=db_sess,
            )

            assert price.workspace_id == workspace.id
            assert price.product_id == product.id
            assert price.type == PriceType.ONE_TIME
            assert price.currency == Currency.USD
            assert price.amount == 19.99
            assert price.active is True
            assert price.recurring_interval is None
            assert price.recurring_interval_count is None
            assert price.trial_period_days is None
            assert price.created_at is not None
            assert price.updated_at is not None

            row = await db_sess.get(Price, price.id)
            assert row is not None

    async def test_creates_with_recurring(
        self, price_service, token_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            price = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.RECURRING,
                currency=Currency.USD,
                amount=5.0,
                active=True,
                recurring_interval=RecurringInterval.MONTH,
                recurring_interval_count=1,
                trial_period_days=7,
                db_sess=db_sess,
            )

            assert price.type == PriceType.RECURRING
            assert price.recurring_interval == RecurringInterval.MONTH
            assert price.recurring_interval_count == 1
            assert price.trial_period_days == 7

    async def test_creates_with_tokens(
        self, price_service, token_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            price = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=1.0,
                active=True,
                token_ids=[token.id],
                db_sess=db_sess,
            )

            assert len(price.tokens) == 1
            assert price.tokens[0].id == token.id
            assert price.tokens[0].name == "TST"

            pt = await db_sess.scalar(
                select(PriceToken).where(
                    PriceToken.price_id == price.id,
                    PriceToken.token_id == token.id,
                )
            )
            assert pt is not None

    async def test_zero_amount_raises(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await price_service.create(
                    workspace_id=workspace.id,
                    product_id=product.id,
                    type=PriceType.ONE_TIME,
                    currency=Currency.USD,
                    amount=0,
                    active=True,
                    db_sess=db_sess,
                )
            all_prices = (await db_sess.execute(select(Price))).scalars().all()
            assert len(all_prices) == 1  # only the one from product creation

    async def test_negative_amount_raises(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await price_service.create(
                    workspace_id=workspace.id,
                    product_id=product.id,
                    type=PriceType.ONE_TIME,
                    currency=Currency.USD,
                    amount=-5.0,
                    active=True,
                    db_sess=db_sess,
                )
            all_prices = (await db_sess.execute(select(Price))).scalars().all()
            assert len(all_prices) == 1

    async def test_nonexistent_workspace_raises(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await price_service.create(
                    workspace_id=uuid4(),
                    product_id=product.id,
                    type=PriceType.ONE_TIME,
                    currency=Currency.USD,
                    amount=5.0,
                    active=True,
                    db_sess=db_sess,
                )

    async def test_nonexistent_product_raises(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await price_service.create(
                    workspace_id=workspace.id,
                    product_id=uuid4(),
                    type=PriceType.ONE_TIME,
                    currency=Currency.USD,
                    amount=5.0,
                    active=True,
                    db_sess=db_sess,
                )

    async def test_nonexistent_token_raises(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await price_service.create(
                    workspace_id=workspace.id,
                    product_id=product.id,
                    type=PriceType.ONE_TIME,
                    currency=Currency.USD,
                    amount=5.0,
                    active=True,
                    token_ids=[uuid4()],
                    db_sess=db_sess,
                )


@pytest.mark.asyncio(loop_scope="session")
class TestGet:
    async def test_returns_price(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            created = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=15.0,
                active=True,
                db_sess=db_sess,
            )

            fetched = await price_service.get_by_id(created.id, db_sess)

            assert fetched.id == created.id
            assert fetched.amount == 15.0

    async def test_raises_when_not_found(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            with pytest.raises(PriceNotFoundException):
                await price_service.get_by_id(uuid4(), db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestGetById:
    async def test_returns_price(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            created = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=25.0,
                active=True,
                db_sess=db_sess,
            )

            fetched = await price_service.get_by_id(created.id, db_sess)
            assert fetched.id == created.id
            assert fetched.amount == 25.0

    async def test_raises_when_not_found(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            with pytest.raises(PriceNotFoundException):
                await price_service.get_by_id(uuid4(), db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestListByProduct:
    async def test_returns_prices_for_product(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            p1 = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=10.0,
                active=True,
                db_sess=db_sess,
            )
            p2 = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.RECURRING,
                currency=Currency.USD,
                amount=5.0,
                active=True,
                recurring_interval=RecurringInterval.MONTH,
                recurring_interval_count=1,
                db_sess=db_sess,
            )

            result = await price_service.list_by_product(
                product.id,
                page=1,
                limit=10,
                db_sess=db_sess,
            )

            assert result.page == 1
            assert result.size >= 2
            assert {p.id for p in result.data}.issuperset({p1.id, p2.id})

    async def test_paginates(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            for _ in range(3):
                await price_service.create(
                    workspace_id=workspace.id,
                    product_id=product.id,
                    type=PriceType.ONE_TIME,
                    currency=Currency.USD,
                    amount=10.0,
                    active=True,
                    db_sess=db_sess,
                )

            result = await price_service.list_by_product(
                product.id,
                page=1,
                limit=2,
                db_sess=db_sess,
            )
            assert result.size == 2
            assert result.has_next is True

    async def test_returns_empty_when_no_prices(
        self, price_service, token_service, faker, create_drop_tables
    ):
        # query with a random product_id that has no prices
        async with get_db_session() as db_sess:
            result = await price_service.list_by_product(
                uuid4(),
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 0
            assert result.has_next is False


@pytest.mark.asyncio(loop_scope="session")
class TestUpdate:
    async def test_updates_amount(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            created = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=10.0,
                active=True,
                db_sess=db_sess,
            )

            updated = await price_service.update(
                created.id,
                workspace.id,
                amount=20.0,
                db_sess=db_sess,
            )
            assert updated.amount == 20.0

            row = await db_sess.get(Price, created.id)
            assert row.amount == 20.0

    async def test_updates_multiple_fields(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            created = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.RECURRING,
                currency=Currency.USD,
                amount=5.0,
                active=True,
                recurring_interval=RecurringInterval.MONTH,
                recurring_interval_count=1,
                db_sess=db_sess,
            )

            updated = await price_service.update(
                created.id,
                workspace.id,
                currency=Currency.USD,
                amount=7.5,
                active=False,
                db_sess=db_sess,
            )
            assert updated.amount == 7.5
            assert updated.active is False

    async def test_raises_when_not_found(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            with pytest.raises(PriceNotFoundException):
                await price_service.update(
                    uuid4(), workspace.id, amount=5.0, db_sess=db_sess
                )

    async def test_update_zero_amount(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            created = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=10.0,
                active=True,
                db_sess=db_sess,
            )

            with pytest.raises(Exception):
                await price_service.update(
                    created.id, workspace.id, amount=0, db_sess=db_sess
                )

            row = await db_sess.get(Price, created.id)
            assert row.amount == 10.0

    async def test_update_negative_amount(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            created = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=10.0,
                active=True,
                db_sess=db_sess,
            )

            with pytest.raises(Exception):
                await price_service.update(
                    created.id, workspace.id, amount=-1.0, db_sess=db_sess
                )

            row = await db_sess.get(Price, created.id)
            assert row.amount == 10.0

    async def test_raises_when_wrong_workspace(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            created = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=10.0,
                active=True,
                db_sess=db_sess,
            )

            with pytest.raises(PriceNotFoundException):
                await price_service.update(
                    created.id, uuid4(), amount=5.0, db_sess=db_sess
                )

            row = await db_sess.get(Price, created.id)
            assert row.amount == 10.0


@pytest.mark.asyncio(loop_scope="session")
class TestListByProduct:
    async def test_returns_empty_for_nonexistent_product(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            result = await price_service.list_by_product(
                uuid4(),
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 0
            assert result.has_next is False


@pytest.mark.asyncio(loop_scope="session")
class TestDelete:
    async def test_deletes_price(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            created = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=10.0,
                active=True,
                db_sess=db_sess,
            )

            await price_service.delete(created.id, workspace.id, db_sess=db_sess)

        async with get_db_session() as db_sess:
            row = await db_sess.get(Price, created.id)
            assert row is None

    async def test_raises_when_not_found(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            with pytest.raises(PriceNotFoundException):
                await price_service.delete(uuid4(), workspace.id, db_sess=db_sess)

    async def test_raises_when_wrong_workspace(
        self, price_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            created = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=10.0,
                active=True,
                db_sess=db_sess,
            )

            with pytest.raises(PriceNotFoundException):
                await price_service.delete(created.id, uuid4(), db_sess=db_sess)

            row = await db_sess.get(Price, created.id)
            assert row is not None

    async def test_cascade_deletes_price_tokens(
        self, price_service, token_service, setup_workspace_product, create_drop_tables
    ):
        workspace, product, token = await setup_workspace_product()
        async with get_db_session() as db_sess:
            created = await price_service.create(
                workspace_id=workspace.id,
                product_id=product.id,
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=10.0,
                active=True,
                token_ids=[token.id],
                db_sess=db_sess,
            )

            await price_service.delete(created.id, workspace.id, db_sess=db_sess)

            pt = await db_sess.scalar(
                select(PriceToken).where(PriceToken.price_id == created.id)
            )
            assert pt is None
