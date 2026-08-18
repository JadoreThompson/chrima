import asyncio
import json
import os
import uuid
from collections import defaultdict
from time import perf_counter
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
import sqlalchemy as sa
from argon2 import PasswordHasher
from asgi_lifespan import LifespanManager
from faker import Faker
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.community.postgres import PostgresContainer

from chrima.discord import DiscordMembershipService, DiscordService, DiscordClient
from chrima.encryption import EncryptionService
from chrima.event_bus.publisher import OutboxEventPublisher
from chrima.jwt import JWTService
from chrima.notification import NotificationPublisher
from chrima.price import PriceService
from chrima.product import ProductService
from chrima.analytics import AnalyticsService
from chrima.subscription import SubscriptionBalanceService
from chrima.subscription.enums import SubscriptionStatus
from chrima.tokens import TokenService
from chrima.transaction import TransactionService
from chrima.transaction.event import TransactionEventDeserialiser
from chrima.transaction.service import TransactionOrchestrator
from chrima.user import UserService
from chrima.wallet import WalletService
from chrima.workspace import WorkspaceService
from config import (
    DISCORD_BOT_TOKEN,
    KAFKA_PORT,
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USERNAME,
    SRC_PATH,
)
from testcontainers.community.kafka import KafkaContainer
from infra.db import Base
from infra.db.session import DB_ENGINE_SYNC
from util import get_datetime, import_modules


@pytest.fixture
def token_service():
    return TokenService()


@pytest.fixture
def pw_hasher():
    return PasswordHasher()


@pytest.fixture
def user_service(pw_hasher):
    return UserService(pw_hasher=pw_hasher)


@pytest.fixture
def event_publisher():
    return OutboxEventPublisher()


@pytest.fixture
def price_service(event_publisher):
    return PriceService(event_publisher=event_publisher)


@pytest.fixture
def wallet_service():
    return WalletService()


@pytest.fixture
def product_service(event_publisher, wallet_service):
    return ProductService(
        event_publisher=event_publisher, wallet_service=wallet_service
    )


@pytest.fixture
def workspace_service():
    return WorkspaceService()


@pytest.fixture
def subscription_balance_service(event_publisher):
    return SubscriptionBalanceService(event_publisher=event_publisher)


@pytest.fixture
def transaction_service():
    return TransactionService()


@pytest.fixture
def analytics_service():
    return AnalyticsService()


@pytest.fixture
def notification_publisher():
    return NotificationPublisher()


@pytest.fixture
def mock_notification_publisher():
    publisher = MagicMock(spec=NotificationPublisher)
    publisher.send = AsyncMock()
    return publisher


@pytest.fixture
def jwt_service(user_service):
    return JWTService(user_service=user_service)


@pytest.fixture
def encryption_service():
    return EncryptionService()


@pytest.fixture
def discord_service(encryption_service):
    return DiscordService(encryption_service=encryption_service)


@pytest.fixture
def outbox_event_publisher():
    return OutboxEventPublisher()


@pytest.fixture
def transaction_event_deserialiser():
    return TransactionEventDeserialiser()


@pytest_asyncio.fixture(loop_scope="session")
async def discord_client():
    client = DiscordClient()

    task = asyncio.create_task(client.start(DISCORD_BOT_TOKEN))
    await asyncio.sleep(1)
    await client.wait_until_ready()

    yield client

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.fixture
def discord_membership_service(discord_client, discord_service):
    return DiscordMembershipService(
        discord_client=discord_client, discord_service=discord_service
    )


@pytest.fixture
def transaction_orchestrator(
    discord_service,
    discord_membership_service,
    notification_publisher,
    product_service,
    price_service,
    workspace_service,
    transaction_event_deserialiser,
):
    return TransactionOrchestrator(
        discord_service=discord_service,
        discord_membership_service=discord_membership_service,
        product_service=product_service,
        price_service=price_service,
        workspace_service=workspace_service,
        deserialiser=transaction_event_deserialiser,
        notification_publisher=notification_publisher,
    )


@pytest.fixture
def create_subscription_balance(subscription_balance_service):
    async def _func(key: str, db_sess: AsyncSession, **kw):
        """
        Creates a subscription balance through the subscription balance service

        Args:
            key (str): A unique key
            db_sess (AsyncSession): An async database session
            kw (dict): Parameters to pass to the create method

        Returns:
            A subscription balance object
        """
        now = int(get_datetime().timestamp())

        params = {
            "external_id": f"ext_{key}",
            "platform_user_id": f"usr_{key}",
            "product_id": uuid.uuid4(),
            "credit_amount": 0.0,
            "status": SubscriptionStatus.ACTIVE,
            "cycle_start": now - 6000,
            "cycle_end": now + 6000,
            "last_processed_tx": None,
            "db_sess": db_sess,
        }

        params.update(kw)

        return await subscription_balance_service.create(**params)

    return _func


@pytest.fixture(scope="session", autouse=True)
def postgres_container():
    with PostgresContainer(
        "postgres:18",
        username=POSTGRES_USERNAME,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB,
    ).with_bind_ports(5432, POSTGRES_PORT) as postgres:
        yield postgres


@pytest.fixture(scope="session", autouse=True)
def kafka_container():
    with KafkaContainer().with_kraft().with_bind_ports(9093, KAFKA_PORT) as kafka:
        yield kafka


@pytest.fixture
def create_drop_tables():
    import chrima

    import_modules(chrima)

    def _helper(create_tables: bool):
        with DB_ENGINE_SYNC.begin() as conn:
            conn.execute(sa.text("DROP SCHEMA IF EXISTS public CASCADE"))
            conn.execute(sa.text("CREATE SCHEMA public"))

            if create_tables:
                Base.metadata.create_all(bind=conn)

    _helper(True)

    yield

    _helper(False)


@pytest.fixture
def faker():
    return Faker()


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    from chrima.api.app import app

    async with LifespanManager(app=app) as lifespan:
        async with AsyncClient(
            base_url="http://test", transport=ASGITransport(app=app)
        ) as client:
            yield client


@pytest.fixture
def discord_user_id() -> int:
    return int(os.environ["DISCORD_USER_ID"])


@pytest.fixture
def discord_guild_id() -> int:
    return int(os.environ["DISCORD_GUILD_ID"])


@pytest.fixture
def discord_role_id() -> int:
    return int(os.environ["DISCORD_ROLE_1_ID"])


@pytest.fixture
def discord_oauth_payload():
    fpath = os.path.join(SRC_PATH, "resources", "discord-oauth-payload.json")
    if not os.path.exists(fpath):
        raise FileNotFoundError(f"Discord oauth payload not found at {fpath}")

    with open(fpath, "r") as f:
        return json.load(f)


@pytest.fixture
def discord_access_token(discord_oauth_payload) -> str:
    return discord_oauth_payload["access_token"]


@pytest.fixture
def discord_refresh_token(discord_oauth_payload):
    return discord_oauth_payload["refresh_token"]


_durations: dict[str, float] = defaultdict(float)
_counts: dict[str, int] = defaultdict(int)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    start = perf_counter()

    yield

    duration = perf_counter() - start

    module = item.fspath.basename

    _durations[module] += duration
    _counts[module] += 1


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _durations:
        return

    terminalreporter.write_sep("=", "test function timings")

    terminalreporter.write_line(f"{'Module':<45} {'Tests':>6} {'Time':>10}")
    terminalreporter.write_line("-" * 65)

    total_duration = 0.0
    total_tests = 0

    for module, duration in sorted(
        _durations.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        tests = _counts[module]

        terminalreporter.write_line(f"{module:<45} {tests:>6} {duration:>9.3f}s")

        total_duration += duration
        total_tests += tests

    terminalreporter.write_line("-" * 65)
    terminalreporter.write_line(
        f"{'TOTAL':<45} {total_tests:>6} {total_duration:>9.3f}s"
    )
