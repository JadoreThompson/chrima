from uuid import uuid4

import pytest

from chrima.price.enums import Currency, PriceType
from chrima.price.schema import CreatePriceRequest
from chrima.product.enums import FulfilmentType
from chrima.subscription.enums import SubscriptionStatus
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.transaction.enums import TransactionStatus
from chrima.workspace.enums import MessagePlatformType
from core.db import get_db_session
from util import get_datetime


async def _setup(
    client,
    user_service,
    pw_hasher,
    workspace_service,
    workspace_wallet_service,
    product_service,
    price_service,
    token_service,
    subscription_balance_service,
    faker,
    transaction_count=3,
    transaction_amount=10.0,
    subscription_status=SubscriptionStatus.ACTIVE,
    cycle_end_offset=86400,
):
    from chrima.transaction.model import Transaction

    username = faker.user_name()
    email = faker.email()
    password = "test_pass_123"
    now = int(get_datetime().timestamp())
    today_start = now - (now % 86400)

    async with get_db_session() as db_sess:
        owner = await user_service.create(
            username=username,
            email=email,
            password=pw_hasher.hash(password),
            db_sess=db_sess,
        )
        workspace = await workspace_service.create(
            user_id=owner.id,
            name="analytics-ws",
            platform=MessagePlatformType.DISCORD,
            external_id="ext_analytics",
            notification_channel_id="ch_analytics",
            db_sess=db_sess,
        )
        token = await token_service.create(
            name="ANT",
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
        prices = await price_service.list_by_product(
            product.id, page=1, limit=1, db_sess=db_sess
        )
        price = prices.data[0]

        for i in range(transaction_count):
            tx = Transaction(
                product_id=product.id,
                price_id=price.id,
                platform_user_id=f"usr_{i}",
                sender="0xsender",
                recipient="0xrecipient",
                address="0xtoken",
                amount=transaction_amount,
                status=TransactionStatus.COMPLETE,
                timestamp=today_start + 3600,
            )
            db_sess.add(tx)

        if transaction_count > 0:
            await subscription_balance_service.create(
                external_id=workspace.external_id,
                platform_user_id="usr_0",
                product_id=product.id,
                credit_amount=50.0,
                status=subscription_status,
                cycle_start=now,
                cycle_end=now + cycle_end_offset,
                db_sess=db_sess,
            )

        await db_sess.commit()

    await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    await client.post(
        "/auth/select-workspace", json={"workspace_id": str(workspace.id)}
    )

    return workspace, product, price.id


@pytest.mark.asyncio(loop_scope="session")
class TestGetSummary:
    async def test_200_returns_summary(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        product_service,
        price_service,
        token_service,
        subscription_balance_service,
        faker,
        create_drop_tables,
    ):
        workspace, _, _ = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            product_service,
            price_service,
            token_service,
            subscription_balance_service,
            faker,
        )
        rsp = await client.get(
            "/analytics/summary",
            params={"workspace_id": str(workspace.id)},
        )
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["total_revenue"] == 30.0
        assert data["total_active_customers"] == 1
        assert data["total_transactions"] == 3

    async def test_200_returns_zeros_when_no_data(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        product_service,
        price_service,
        token_service,
        subscription_balance_service,
        faker,
        create_drop_tables,
    ):
        workspace, _, _ = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            product_service,
            price_service,
            token_service,
            subscription_balance_service,
            faker,
            transaction_count=0,
        )
        rsp = await client.get(
            "/analytics/summary",
            params={"workspace_id": str(workspace.id)},
        )
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["total_revenue"] == 0.0
        assert data["total_active_customers"] == 0
        assert data["total_transactions"] == 0

    async def test_401_without_auth(
        self,
        client,
        create_drop_tables,
    ):
        rsp = await client.get(
            "/analytics/summary",
            params={"workspace_id": str(uuid4())},
        )
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestGetRevenue:
    async def test_200_returns_timeseries(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        product_service,
        price_service,
        token_service,
        subscription_balance_service,
        faker,
        create_drop_tables,
    ):
        workspace, _, _ = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            product_service,
            price_service,
            token_service,
            subscription_balance_service,
            faker,
        )
        rsp = await client.get(
            "/analytics/revenue",
            params={"workspace_id": str(workspace.id), "period": "today"},
        )
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["period"] == "today"
        assert len(data["points"]) == 3

    async def test_401_without_auth(
        self,
        client,
        create_drop_tables,
    ):
        rsp = await client.get(
            "/analytics/revenue",
            params={"workspace_id": str(uuid4()), "period": "today"},
        )
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestGetActiveCustomers:
    async def test_200_returns_timeseries(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        product_service,
        price_service,
        token_service,
        subscription_balance_service,
        faker,
        create_drop_tables,
    ):
        workspace, _, _ = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            product_service,
            price_service,
            token_service,
            subscription_balance_service,
            faker,
        )
        rsp = await client.get(
            "/analytics/active-customers",
            params={"workspace_id": str(workspace.id), "period": "today"},
        )
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["period"] == "today"
        assert len(data["points"]) == 3

    async def test_401_without_auth(
        self,
        client,
        create_drop_tables,
    ):
        rsp = await client.get(
            "/analytics/active-customers",
            params={"workspace_id": str(uuid4()), "period": "today"},
        )
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestGetSubscriptionAnalytics:
    async def test_200_returns_active_count(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        product_service,
        price_service,
        token_service,
        subscription_balance_service,
        faker,
        create_drop_tables,
    ):
        workspace, _, _ = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            product_service,
            price_service,
            token_service,
            subscription_balance_service,
            faker,
        )
        rsp = await client.get(
            "/analytics/subscriptions",
            params={"workspace_id": str(workspace.id)},
        )
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["active"] == 1
        assert data["expired"] == 0
        assert data["cancelled"] == 0

    async def test_200_counts_expired_and_cancelled(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        product_service,
        price_service,
        token_service,
        subscription_balance_service,
        faker,
        create_drop_tables,
    ):
        workspace, _, _ = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            product_service,
            price_service,
            token_service,
            subscription_balance_service,
            faker,
            subscription_status=SubscriptionStatus.CANCELLED,
        )
        rsp = await client.get(
            "/analytics/subscriptions",
            params={"workspace_id": str(workspace.id)},
        )
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["active"] == 0
        assert data["cancelled"] == 1

    async def test_200_returns_zeros_when_no_data(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        product_service,
        price_service,
        token_service,
        subscription_balance_service,
        faker,
        create_drop_tables,
    ):
        workspace, _, _ = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            product_service,
            price_service,
            token_service,
            subscription_balance_service,
            faker,
            transaction_count=0,
        )
        rsp = await client.get(
            "/analytics/subscriptions",
            params={"workspace_id": str(workspace.id)},
        )
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["active"] == 0
        assert data["expired"] == 0
        assert data["cancelled"] == 0
        assert data["expiring"] == 0

    async def test_401_without_auth(
        self,
        client,
        create_drop_tables,
    ):
        rsp = await client.get(
            "/analytics/subscriptions",
            params={"workspace_id": str(uuid4())},
        )
        assert rsp.status_code == 401
