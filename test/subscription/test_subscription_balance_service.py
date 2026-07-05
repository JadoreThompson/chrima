from uuid import uuid4

import pytest

from chrima.message_platform.enums import MessagePlatformType
from sqlalchemy import select

from chrima.price.enums import Currency, PriceType, RecurringInterval
from chrima.price.model import Price
from chrima.price.schema import CreatePriceRequest
from chrima.product.enums import FulfilmentType
from chrima.subscription.enums import SubscriptionStatus
from chrima.subscription.exception import SubscriptionBalanceNotFoundException
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.transaction.enums import TransactionStatus
from chrima.transaction.model import Transaction
from core.db import get_db_session
from util import get_datetime


@pytest.fixture
def external_id():
    return f"ext_{uuid4().hex[:8]}"


@pytest.fixture
def platform_user_id():
    return f"usr_{uuid4().hex[:8]}"


@pytest.fixture
def now():
    return int(get_datetime().timestamp())


@pytest.fixture
def create_product(
    user_service,
    workspace_service,
    workspace_wallet_service,
    product_service,
    token_service,
    faker,
):
    async def _create():
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username=faker.user_name(),
                email=faker.email(),
                password=faker.password(),
                db_sess=db_sess,
            )
            workspace = await workspace_service.create(
                user_id=user.id,
                name=f"{user.username}-ws",
                platform=MessagePlatformType.DISCORD,
                external_id=f"ext_{uuid4().hex[:8]}",
                notification_channel_id="ch_1",
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
                    product_id=uuid4(),
                    type=PriceType.ONE_TIME,
                    currency=Currency.USD,
                    amount=10.0,
                ),
                db_sess=db_sess,
            )
            price_row = await db_sess.scalar(
                select(Price).where(Price.product_id == product.id)
            )
            tx = Transaction(
                product_id=product.id,
                price_id=price_row.id,
                platform_user_id="usr_test",
                sender="0xsender",
                recipient="0xrecipient",
                address="0xtoken",
                amount=10.0,
                status=TransactionStatus.COMPLETE,
                timestamp=int(get_datetime().timestamp()),
            )
            db_sess.add(tx)
            await db_sess.commit()
            return product, tx

    return _create


@pytest.fixture
def create_balance(subscription_balance_service):
    async def _create(external_id, platform_user_id, product_id, **kw):
        async with get_db_session() as db_sess:
            params = {
                "external_id": external_id,
                "platform_user_id": platform_user_id,
                "product_id": product_id,
                "credit_amount": 0.0,
                "status": SubscriptionStatus.ACTIVE,
                "db_sess": db_sess,
            }
            params.update(kw)
            return await subscription_balance_service.create(**params)

    return _create


@pytest.mark.asyncio(loop_scope="session")
class TestCreate:
    async def test_creates_subscription_balance(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        now,
        create_product,
        create_drop_tables,
    ):
        product, _ = await create_product()
        async with get_db_session() as db_sess:
            result = await subscription_balance_service.create(
                external_id=external_id,
                platform_user_id=platform_user_id,
                product_id=product.id,
                credit_amount=100.0,
                status=SubscriptionStatus.ACTIVE,
                cycle_start=now,
                cycle_end=now + 3600,
                db_sess=db_sess,
            )
        assert result.credit_amount == 100.0
        assert result.status == SubscriptionStatus.ACTIVE
        assert result.cycle_start == now
        assert result.attempt_count == 0

    async def test_creates_without_optional_fields(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        create_product,
        create_drop_tables,
    ):
        product, _ = await create_product()
        async with get_db_session() as db_sess:
            result = await subscription_balance_service.create(
                external_id=external_id,
                platform_user_id=platform_user_id,
                product_id=product.id,
                credit_amount=0.0,
                status=SubscriptionStatus.INCOMPLETE,
                db_sess=db_sess,
            )
        assert result.cycle_start is None
        assert result.cycle_end is None
        assert result.last_processed_tx is None


@pytest.mark.asyncio(loop_scope="session")
class TestGet:
    async def test_returns_balance_by_composite_key(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        now,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, _ = await create_product()
        await create_balance(
            external_id,
            platform_user_id,
            product.id,
            credit_amount=50.0,
            cycle_start=now,
            cycle_end=now + 3600,
        )
        async with get_db_session() as db_sess:
            result = await subscription_balance_service.get(
                external_id, platform_user_id, product.id, db_sess=db_sess
            )
        assert result.credit_amount == 50.0

    async def test_raises_when_not_found(
        self, subscription_balance_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            with pytest.raises(SubscriptionBalanceNotFoundException):
                await subscription_balance_service.get(
                    "nonexistent", "nonexistent", uuid4(), db_sess=db_sess
                )


@pytest.mark.asyncio(loop_scope="session")
class TestGetById:
    async def test_returns_balance_by_id(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        now,
        create_product,
        create_drop_tables,
    ):
        product, _ = await create_product()
        async with get_db_session() as db_sess:
            created = await subscription_balance_service.create(
                external_id=external_id,
                platform_user_id=platform_user_id,
                product_id=product.id,
                credit_amount=25.0,
                status=SubscriptionStatus.ACTIVE,
                cycle_start=now,
                cycle_end=now + 3600,
                db_sess=db_sess,
            )
        async with get_db_session() as db_sess:
            result = await subscription_balance_service.get_by_id(created.id, db_sess)
        assert result.credit_amount == 25.0

    async def test_returns_none_when_not_found(
        self, subscription_balance_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await subscription_balance_service.get_by_id(uuid4(), db_sess)
        assert result is None


@pytest.mark.asyncio(loop_scope="session")
class TestIncreaseBalance:
    async def test_increases_balance(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        now,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, tx = await create_product()
        await create_balance(
            external_id,
            platform_user_id,
            product.id,
            credit_amount=10.0,
            cycle_start=now,
            cycle_end=now + 3600,
        )
        async with get_db_session() as db_sess:
            result = await subscription_balance_service.increase_balance(
                external_id=external_id,
                platform_user_id=platform_user_id,
                product_id=product.id,
                amount=25.0,
                transaction_id=tx.id,
                db_sess=db_sess,
            )
        assert result.credit_amount == 35.0
        assert result.last_processed_tx == tx.id

    async def test_increases_twice(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        now,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, tx = await create_product()
        await create_balance(
            external_id,
            platform_user_id,
            product.id,
            credit_amount=5.0,
            cycle_start=now,
            cycle_end=now + 3600,
        )
        async with get_db_session() as db_sess:
            await subscription_balance_service.increase_balance(
                external_id=external_id,
                platform_user_id=platform_user_id,
                product_id=product.id,
                amount=10.0,
                transaction_id=tx.id,
                db_sess=db_sess,
            )
        async with get_db_session() as db_sess:
            result = await subscription_balance_service.increase_balance(
                external_id=external_id,
                platform_user_id=platform_user_id,
                product_id=product.id,
                amount=15.0,
                transaction_id=tx.id,
                db_sess=db_sess,
            )
        assert result.credit_amount == 30.0

    async def test_raises_on_zero_amount(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, tx = await create_product()
        await create_balance(
            external_id, platform_user_id, product.id, credit_amount=10.0
        )
        async with get_db_session() as db_sess:
            with pytest.raises(ValueError, match="Amount must be greater than zero"):
                await subscription_balance_service.increase_balance(
                    external_id, platform_user_id, product.id, 0, tx.id, db_sess=db_sess
                )

    async def test_raises_on_negative_amount(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, tx = await create_product()
        await create_balance(
            external_id, platform_user_id, product.id, credit_amount=10.0
        )
        async with get_db_session() as db_sess:
            with pytest.raises(ValueError, match="Amount must be greater than zero"):
                await subscription_balance_service.increase_balance(
                    external_id,
                    platform_user_id,
                    product.id,
                    -5.0,
                    tx.id,
                    db_sess=db_sess,
                )

    async def test_raises_on_none_transaction_id(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, _ = await create_product()
        await create_balance(
            external_id, platform_user_id, product.id, credit_amount=10.0
        )
        async with get_db_session() as db_sess:
            with pytest.raises(ValueError, match="Transaction ID must be provided"):
                await subscription_balance_service.increase_balance(
                    external_id,
                    platform_user_id,
                    product.id,
                    10.0,
                    None,
                    db_sess=db_sess,
                )

    async def test_raises_when_not_found(
        self, subscription_balance_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            with pytest.raises(SubscriptionBalanceNotFoundException):
                await subscription_balance_service.increase_balance(
                    "nonexistent",
                    "nonexistent",
                    uuid4(),
                    10.0,
                    uuid4(),
                    db_sess=db_sess,
                )


@pytest.mark.asyncio(loop_scope="session")
class TestProcessCycle:
    async def test_deducts_and_updates_cycle(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        now,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, tx = await create_product()
        await create_balance(
            external_id,
            platform_user_id,
            product.id,
            credit_amount=100.0,
            cycle_start=now,
            cycle_end=now + 3600,
        )
        async with get_db_session() as db_sess:
            result = await subscription_balance_service.process_cycle(
                external_id=external_id,
                platform_user_id=platform_user_id,
                product_id=product.id,
                amount=30.0,
                recurring_interval=RecurringInterval.DAY,
                recurring_interval_count=30,
                transaction_id=tx.id,
                db_sess=db_sess,
            )
        assert result.credit_amount == 70.0
        assert result.last_processed_tx == tx.id
        assert result.cycle_end == result.cycle_start + 86400 * 30

    async def test_month_interval(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, tx = await create_product()
        await create_balance(
            external_id, platform_user_id, product.id, credit_amount=100.0
        )
        async with get_db_session() as db_sess:
            result = await subscription_balance_service.process_cycle(
                external_id=external_id,
                platform_user_id=platform_user_id,
                product_id=product.id,
                amount=10.0,
                recurring_interval=RecurringInterval.MONTH,
                recurring_interval_count=1,
                transaction_id=tx.id,
                db_sess=db_sess,
            )
        assert result.cycle_end == result.cycle_start + 2592000

    async def test_raises_on_zero_amount(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, tx = await create_product()
        await create_balance(
            external_id, platform_user_id, product.id, credit_amount=50.0
        )
        async with get_db_session() as db_sess:
            with pytest.raises(ValueError, match="Amount must be greater than zero"):
                await subscription_balance_service.process_cycle(
                    external_id,
                    platform_user_id,
                    product.id,
                    0,
                    RecurringInterval.DAY,
                    1,
                    tx.id,
                    db_sess=db_sess,
                )

    async def test_raises_on_negative_amount(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, tx = await create_product()
        await create_balance(
            external_id, platform_user_id, product.id, credit_amount=50.0
        )
        async with get_db_session() as db_sess:
            with pytest.raises(ValueError, match="Amount must be greater than zero"):
                await subscription_balance_service.process_cycle(
                    external_id,
                    platform_user_id,
                    product.id,
                    -10.0,
                    RecurringInterval.DAY,
                    1,
                    tx.id,
                    db_sess=db_sess,
                )

    async def test_raises_on_none_transaction_id(
        self,
        subscription_balance_service,
        external_id,
        platform_user_id,
        create_product,
        create_balance,
        create_drop_tables,
    ):
        product, _ = await create_product()
        await create_balance(
            external_id, platform_user_id, product.id, credit_amount=50.0
        )
        async with get_db_session() as db_sess:
            with pytest.raises(ValueError, match="Transaction ID must be provided"):
                await subscription_balance_service.process_cycle(
                    external_id,
                    platform_user_id,
                    product.id,
                    10.0,
                    RecurringInterval.DAY,
                    1,
                    None,
                    db_sess=db_sess,
                )

    async def test_raises_when_not_found(
        self, subscription_balance_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            with pytest.raises(SubscriptionBalanceNotFoundException):
                await subscription_balance_service.process_cycle(
                    "nonexistent",
                    "nonexistent",
                    uuid4(),
                    10.0,
                    RecurringInterval.DAY,
                    1,
                    uuid4(),
                    db_sess=db_sess,
                )
