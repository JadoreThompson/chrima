import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
import sqlalchemy as sa
from argon2 import PasswordHasher
from asgi_lifespan import LifespanManager
from faker import Faker
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.encryption import EncryptionService
from chrima.jwt import JWTService
from chrima.message_platform import MessagePlatformService
from chrima.message_platform.service.oauth.discord import DiscordOauthService
from chrima.notification import NotificationPublisher
from chrima.price import PriceService
from chrima.product import ProductService
from chrima.subscription import SubscriptionBalanceService
from chrima.subscription.enums import SubscriptionStatus
from chrima.tokens import TokenService
from chrima.transaction import TransactionService
from chrima.user import UserService
from chrima.workspace import WorkspaceService
from chrima.workspace.wallet import WorkspaceWalletService
from core.db import Base
from core.db.session import DB_ENGINE_SYNC
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
def price_service(token_service):
    return PriceService(token_service=token_service)


@pytest.fixture
def product_service(price_service):
    return ProductService(price_service=price_service)


@pytest.fixture
def workspace_service():
    return WorkspaceService()


@pytest.fixture
def workspace_wallet_service():
    return WorkspaceWalletService()


@pytest.fixture
def subscription_balance_service():
    return SubscriptionBalanceService()


@pytest.fixture
def transaction_service():
    return TransactionService()


@pytest.fixture
def notification_publisher():
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
def discord_oauth_service():
    return DiscordOauthService()


@pytest.fixture
def message_platform_service(discord_oauth_service, encryption_service):
    return MessagePlatformService(
        discord_oauth_service=discord_oauth_service,
        encryption_service=encryption_service,
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
