from uuid import uuid4

import pytest

from chrima.analytics.enums import TimePeriod
from chrima.price.enums import Currency, PriceType
from chrima.product.enums import FulfilmentType
from chrima.subscription.enums import SubscriptionStatus
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.transaction.enums import TransactionStatus
from chrima.workspace.enums import MessagePlatformType
from infra.db import get_db_session
from util import get_datetime


@pytest.fixture
def setup_workspace_with_data(
    user_service,
    workspace_service,
    wallet_service,
    product_service,
    price_service,
    token_service,
    subscription_balance_service,
    faker,
):
    async def _setup(
        product_amount: float = 10.0,
        transaction_count: int = 3,
        transaction_amount: float = 10.0,
        subscription_status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
        transaction_status: TransactionStatus = TransactionStatus.COMPLETE,
        base_timestamp: int | None = None,
    ):
        from chrima.transaction.model import Transaction

        now = (
            base_timestamp
            if base_timestamp is not None
            else int(get_datetime().timestamp())
        )
        async with get_db_session() as db_sess:
            owner = await user_service.create(
                username=faker.user_name(),
                email=faker.email(),
                password=faker.password(),
                db_sess=db_sess,
            )
            workspace = await workspace_service.create(
                user_id=owner.id,
                name=f"{owner.username}-ws",
                platform=MessagePlatformType.DISCORD,
                external_id=f"ext_{uuid4().hex[:8]}",
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
                amount=product_amount,
                db_sess=db_sess,
            )

            for i in range(transaction_count):
                tx = Transaction(
                    product_id=product.id,
                    price_id=price.id,
                    platform_user_id=f"usr_{i}",
                    sender="0xsender",
                    recipient="0xrecipient",
                    address="0xtoken",
                    amount=transaction_amount,
                    status=transaction_status,
                    timestamp=now,
                )
                db_sess.add(tx)

            await subscription_balance_service.create(
                external_id=workspace.external_id,
                platform_user_id="usr_0",
                product_id=product.id,
                credit_amount=50.0,
                status=subscription_status,
                cycle_start=now,
                cycle_end=now + 86400,
                db_sess=db_sess,
            )

            await db_sess.commit()
            return workspace, product, price

    return _setup


@pytest.fixture
def setup_workspace_with_timestamps(
    user_service,
    workspace_service,
    wallet_service,
    product_service,
    price_service,
    token_service,
    subscription_balance_service,
    faker,
):
    async def _setup(timestamps: list[int]):
        from chrima.transaction.model import Transaction

        now = int(get_datetime().timestamp())
        async with get_db_session() as db_sess:
            owner = await user_service.create(
                username=faker.user_name(),
                email=faker.email(),
                password=faker.password(),
                db_sess=db_sess,
            )
            workspace = await workspace_service.create(
                user_id=owner.id,
                name=f"{owner.username}-ws",
                platform=MessagePlatformType.DISCORD,
                external_id=f"ext_{uuid4().hex[:8]}",
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

            for i, ts in enumerate(timestamps):
                tx = Transaction(
                    product_id=product.id,
                    price_id=price.id,
                    platform_user_id=f"usr_{i}",
                    sender="0xsender",
                    recipient="0xrecipient",
                    address="0xtoken",
                    amount=float(i + 1) * 10.0,
                    status=TransactionStatus.COMPLETE,
                    timestamp=ts,
                )
                db_sess.add(tx)

            await subscription_balance_service.create(
                external_id=workspace.external_id,
                platform_user_id="usr_0",
                product_id=product.id,
                credit_amount=50.0,
                status=SubscriptionStatus.ACTIVE,
                cycle_start=now,
                cycle_end=now + 86400,
                db_sess=db_sess,
            )

            await db_sess.commit()
            return workspace, product, price

    return _setup


@pytest.mark.asyncio(loop_scope="session")
class TestGetSummary:
    async def test_returns_summary_with_data(
        self, analytics_service, setup_workspace_with_data, create_drop_tables
    ):
        workspace, _, _ = await setup_workspace_with_data(
            product_amount=10.0,
            transaction_count=3,
            transaction_amount=10.0,
        )
        async with get_db_session() as db_sess:
            summary = await analytics_service.get_summary(workspace.id, db_sess)
        assert summary.total_revenue == 30.0
        assert summary.total_active_customers == 1
        assert summary.total_transactions == 3

    async def test_returns_zero_when_no_data(
        self, analytics_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            summary = await analytics_service.get_summary(uuid4(), db_sess)
        assert summary.total_revenue == 0.0
        assert summary.total_active_customers == 0
        assert summary.total_transactions == 0

    async def test_counts_only_complete_transactions(
        self, analytics_service, setup_workspace_with_data, create_drop_tables
    ):
        workspace, _, _ = await setup_workspace_with_data(
            transaction_count=2,
            transaction_amount=25.0,
            transaction_status=TransactionStatus.FAILED,
        )
        async with get_db_session() as db_sess:
            summary = await analytics_service.get_summary(workspace.id, db_sess)
        assert summary.total_revenue == 0.0
        assert summary.total_transactions == 0

    async def test_counts_only_active_subscriptions(
        self, analytics_service, setup_workspace_with_data, create_drop_tables
    ):
        workspace, _, _ = await setup_workspace_with_data(
            subscription_status=SubscriptionStatus.CANCELLED,
        )
        async with get_db_session() as db_sess:
            summary = await analytics_service.get_summary(workspace.id, db_sess)
        assert summary.total_active_customers == 0


@pytest.mark.asyncio(loop_scope="session")
class TestGetRevenueTimeseries:
    async def test_returns_revenue_for_today(
        self,
        analytics_service,
        setup_workspace_with_timestamps,
        create_drop_tables,
    ):
        now = int(get_datetime().timestamp())
        today_start = now - (now % 86400)
        # Use timestamps earlier than now so the end_ts filter does not exclude them
        timestamps = [
            today_start + 3600,
            today_start + 3600 * 3,
            today_start + 3600 * 5,
        ]
        workspace, _, _ = await setup_workspace_with_timestamps(timestamps)
        async with get_db_session() as db_sess:
            result = await analytics_service.get_revenue_timeseries(
                workspace.id, TimePeriod.TODAY, db_sess
            )
        assert result.period == TimePeriod.TODAY
        assert len(result.points) == 3
        total = sum(p.value for p in result.points)
        assert total == 60.0

    async def test_returns_revenue_for_this_week(
        self,
        analytics_service,
        setup_workspace_with_timestamps,
        create_drop_tables,
    ):
        now = int(get_datetime().timestamp())
        timestamps = [now - 3600 * i for i in range(7)]
        workspace, _, _ = await setup_workspace_with_timestamps(timestamps)
        async with get_db_session() as db_sess:
            result = await analytics_service.get_revenue_timeseries(
                workspace.id, TimePeriod.THIS_WEEK, db_sess
            )
        assert result.period == TimePeriod.THIS_WEEK
        assert len(result.points) == 7
        total = sum(p.value for p in result.points)
        assert total > 0

    async def test_returns_revenue_for_this_month(
        self,
        analytics_service,
        setup_workspace_with_timestamps,
        create_drop_tables,
    ):
        now = int(get_datetime().timestamp())
        timestamps = [now - 3600 * i for i in range(4)]
        workspace, _, _ = await setup_workspace_with_timestamps(timestamps)
        async with get_db_session() as db_sess:
            result = await analytics_service.get_revenue_timeseries(
                workspace.id, TimePeriod.THIS_MONTH, db_sess
            )
        assert result.period == TimePeriod.THIS_MONTH
        assert len(result.points) == 4
        total = sum(p.value for p in result.points)
        assert total > 0, result

    async def test_returns_zeros_when_no_data(
        self, analytics_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await analytics_service.get_revenue_timeseries(
                uuid4(), TimePeriod.TODAY, db_sess
            )
        assert len(result.points) == 3
        assert all(p.value == 0.0 for p in result.points)


@pytest.mark.asyncio(loop_scope="session")
class TestGetActiveCustomersTimeseries:
    async def test_counts_distinct_customers(
        self,
        analytics_service,
        setup_workspace_with_timestamps,
        create_drop_tables,
    ):
        now = int(get_datetime().timestamp())
        today_start = now - (now % 86400)
        timestamps = [today_start + 3600] * 3
        workspace, _, _ = await setup_workspace_with_timestamps(timestamps)
        async with get_db_session() as db_sess:
            result = await analytics_service.get_active_customers_timeseries(
                workspace.id, TimePeriod.TODAY, db_sess
            )
        assert result.period == TimePeriod.TODAY
        assert len(result.points) == 3
        active = sum(1 for p in result.points if p.value > 0)
        assert active == 1

    async def test_returns_zeros_when_no_data(
        self, analytics_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await analytics_service.get_active_customers_timeseries(
                uuid4(), TimePeriod.TODAY, db_sess
            )
        assert len(result.points) == 3
        assert all(p.value == 0.0 for p in result.points)
