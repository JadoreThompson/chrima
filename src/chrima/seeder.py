from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import IS_PRODUCTION
from chrima.encryption import EncryptionService
from chrima.event_bus.publisher import OutboxEventPublisher
from chrima.message_platform.enums import MessagePlatformType
from chrima.message_platform.service.oauth.discord import DiscordOauthService
from chrima.message_platform.service.service import MessagePlatformService
from chrima.price import PriceService
from chrima.price.enums import Currency, PriceType
from chrima.price.model import Price
from chrima.product import ProductService
from chrima.product.enums import FulfilmentType as ProductFulfilmentType
from chrima.product.schema import CreatePriceRequest, ProductResponse
from chrima.subscription.enums import SubscriptionStatus
from chrima.subscription.service.service import SubscriptionBalanceService
from chrima.tokens import TokenService
from chrima.tokens.service import TokenSeeder
from chrima.transaction.enums import TransactionStatus
from chrima.transaction.model import Transaction
from chrima.user import UserService
from chrima.user.schema import UserDto
from chrima.wallet import WalletService
from chrima.wallet.schema import WalletResponse
from chrima.workspace import WorkspaceService
from chrima.workspace.schema import WorkspaceResponse
from core.db import get_db_session
from util import get_datetime


class DbSeeder:

    def __init__(self) -> None:
        pw_hasher = PasswordHasher()
        self._user_service = UserService(pw_hasher=pw_hasher)
        self._token_service = TokenService()
        self._token_seeder = TokenSeeder(mainnet=IS_PRODUCTION)
        self._workspace_service = WorkspaceService()
        self._wallet_service = WalletService()
        event_publisher = OutboxEventPublisher()
        self._price_service = PriceService(
            token_service=self._token_service,
            event_publisher=event_publisher,
        )
        self._product_service = ProductService(
            price_service=self._price_service,
            event_publisher=event_publisher,
        )
        self._subscription_balance_service = SubscriptionBalanceService()
        self._encryption_service = EncryptionService()
        self._discord_oauth_service = DiscordOauthService()
        self._message_platform_service = MessagePlatformService(
            discord_oauth_service=self._discord_oauth_service,
            encryption_service=self._encryption_service,
        )

    async def run(self) -> None:
        async with get_db_session() as db_sess:
            user = await self._seed_user(db_sess)
            tokens = await self._seed_tokens(db_sess)
            workspace = await self._seed_workspace(user, db_sess)
            await self._seed_oauth(workspace, db_sess)
            wallet = await self._seed_wallet(workspace, tokens, db_sess)
            product = await self._seed_product(workspace, wallet, db_sess)
            price = await self._get_product_price(product, db_sess)
            await self._seed_transactions(workspace, product, price, db_sess)
            await self._seed_subscription_balance(workspace, product, db_sess)

    async def _seed_user(self, db_sess: AsyncSession) -> UserDto:
        print("Seeding user ...")
        return await self._user_service.create(
            username="testuser",
            email="test@example.com",
            password="password123",
            db_sess=db_sess,
        )

    async def _seed_tokens(self, db_sess: AsyncSession) -> list:
        print("Seeding tokens ...")
        return await self._token_seeder.run(db_sess)

    async def _seed_workspace(
        self, user: UserDto, db_sess: AsyncSession
    ) -> WorkspaceResponse:
        print("Seeding workspace ...")
        return await self._workspace_service.create(
            user_id=user.id,
            name="Test Workspace",
            platform=MessagePlatformType.DISCORD,
            external_id="1495532119961637047",
            notification_channel_id="1495532119961637047",
            db_sess=db_sess,
        )

    async def _seed_oauth(
        self,
        workspace: WorkspaceResponse,
        db_sess: AsyncSession,
    ) -> None:
        print("Seeding Discord OAuth payload ...")
        await self._message_platform_service.store_oauth_payload(
            message_platform_type=MessagePlatformType.DISCORD,
            user_id=int(workspace.external_id),
            oauth_payload={
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_at": 9999999999,
            },
            db_sess=db_sess,
        )

    async def _seed_wallet(
        self,
        workspace: WorkspaceResponse,
        tokens: list,
        db_sess: AsyncSession,
    ) -> WalletResponse:
        print("Seeding wallet ...")
        return await self._wallet_service.create(
            workspace_id=workspace.id,
            name="Test Wallet",
            wallet_address="0xabcdef1234567890abcdef1234567890abcdef12",
            token_ids=[t.id for t in tokens],
            db_sess=db_sess,
        )

    async def _seed_product(
        self,
        workspace: WorkspaceResponse,
        wallet: WalletResponse,
        db_sess: AsyncSession,
    ) -> ProductResponse:
        print("Seeding product ...")
        return await self._product_service.create(
            workspace_id=workspace.id,
            name="Test Product",
            description="A test product for development",
            wallet_id=wallet.id,
            external_url="https://discord.gg/test",
            roles=["1520062782840508496"],
            fulfilment_type=ProductFulfilmentType.ROLE,
            price_data=CreatePriceRequest(
                type=PriceType.ONE_TIME,
                currency=Currency.USD,
                amount=10.0,
                active=True,
                recurring_interval=None,
                recurring_interval_count=None,
                trial_period_days=None,
            ),
            db_sess=db_sess,
        )

    async def _seed_subscription_balance(
        self,
        workspace: WorkspaceResponse,
        product: ProductResponse,
        db_sess: AsyncSession,
    ) -> None:
        print("Seeding subscription balance ...")
        await self._subscription_balance_service.create(
            external_id=workspace.external_id,
            platform_user_id=workspace.external_id,
            product_id=product.id,
            credit_amount=0.0,
            status=SubscriptionStatus.ACTIVE,
            db_sess=db_sess,
        )

    async def _get_product_price(
        self, product: ProductResponse, db_sess: AsyncSession
    ) -> Price:
        row = await db_sess.scalar(select(Price).where(Price.product_id == product.id))
        return row

    async def _seed_transactions(
        self,
        workspace: WorkspaceResponse,
        product: ProductResponse,
        price: Price,
        db_sess: AsyncSession,
    ) -> None:
        print("Seeding transactions ...")
        now = int(get_datetime().timestamp())

        tx1 = Transaction(
            product_id=product.id,
            price_id=price.id,
            platform_user_id=workspace.external_id,
            sender="0xf2dd8a2D48301B0b072786bd55B9F892F64A77D5",
            recipient="0x0000000000000000000000000000000000000001",
            address="0x0000000000000000000000000000000000000001",
            amount=price.amount,
            status=TransactionStatus.COMPLETE,
            timestamp=now - 86400,
        )
        tx2 = Transaction(
            product_id=product.id,
            price_id=price.id,
            platform_user_id=workspace.external_id,
            sender="0xf2dd8a2D48301B0b072786bd55B9F892F64A77D5",
            recipient="0x0000000000000000000000000000000000000001",
            address="0x0000000000000000000000000000000000000001",
            amount=price.amount,
            status=TransactionStatus.COMPLETE,
            timestamp=now - 43200,
        )
        tx3 = Transaction(
            product_id=product.id,
            price_id=price.id,
            platform_user_id=workspace.external_id,
            sender="0xf2dd8a2D48301B0b072786bd55B9F892F64A77D5",
            recipient="0x0000000000000000000000000000000000000001",
            address="0x0000000000000000000000000000000000000001",
            amount=price.amount,
            status=TransactionStatus.COMPLETE,
            timestamp=now,
        )
        db_sess.add_all([tx1, tx2, tx3])
