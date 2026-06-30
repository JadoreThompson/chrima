from argon2 import PasswordHasher
from sqlalchemy.ext.asyncio import AsyncSession

from config import IS_PRODUCTION
from chrima.workspace import WorkspaceService
from chrima.workspace.schema import WorkspaceResponse
from chrima.workspace.wallet import WorkspaceWalletService
from chrima.workspace.wallet.schema import WalletResponse
from chrima.price import PriceService
from chrima.price.enums import Currency, PriceType
from chrima.price.schema import PriceResponse
from chrima.product import ProductService
from chrima.product.enums import FulfilmentType as ProductFulfilmentType
from chrima.product.schema import ProductResponse
from chrima.tokens import TokenService
from chrima.tokens.schema import TokenResponse
from chrima.tokens.service import TokenSeeder
from chrima.user import UserService
from chrima.user.schema import UserResponse
from core.db import get_db_session


class DbSeeder:

    def __init__(self) -> None:
        pw_hasher = PasswordHasher()
        self._user_service = UserService(pw_hasher=pw_hasher)
        self._token_service = TokenService()
        self._token_seeder = TokenSeeder(mainnet=IS_PRODUCTION)
        self._merchant_service = WorkspaceService()
        self._wallet_service = WorkspaceWalletService()
        self._price_service = PriceService(token_service=self._token_service)
        self._product_service = ProductService(price_service=self._price_service)

    async def run(self) -> None:
        async with get_db_session() as db_sess:
            user = await self._seed_user(db_sess)
            tokens = await self._seed_tokens(db_sess)
            merchant = await self._seed_merchant(user, db_sess)
            wallet = await self._seed_wallet(merchant, tokens, db_sess)
            product = await self._seed_product(merchant, wallet, db_sess)
            await self._seed_price(merchant, product, tokens, db_sess)

    async def _seed_user(self, db_sess: AsyncSession) -> UserResponse:
        print("Seeding user ...")
        return await self._user_service.create(
            username="testuser",
            email="test@example.com",
            password="password123",
            db_sess=db_sess,
        )

    async def _seed_tokens(self, db_sess: AsyncSession) -> list[TokenResponse]:
        print("Seeding tokens ...")
        return await self._token_seeder.run(db_sess)

    async def _seed_merchant(
        self, user: UserResponse, db_sess: AsyncSession
    ) -> WorkspaceResponse:
        print("Seeding merchant ...")
        return await self._merchant_service.create(
            user_id=user.id,
            name="Test Merchant",
            wallet_address="0x1234567890abcdef1234567890abcdef12345678",
            notification_channel_id="1495532119961637047",
            db_sess=db_sess,
        )

    async def _seed_wallet(
        self,
        merchant: WorkspaceResponse,
        tokens: list[TokenResponse],
        db_sess: AsyncSession,
    ) -> WalletResponse:
        print("Seeding wallet ...")
        return await self._wallet_service.create(
            workspace_id=merchant.id,
            name="Test Wallet",
            wallet_address="0xabcdef1234567890abcdef1234567890abcdef12",
            token_ids=[t.id for t in tokens],
            db_sess=db_sess,
        )

    async def _seed_product(
        self, merchant: WorkspaceResponse, wallet: WalletResponse, db_sess: AsyncSession
    ) -> ProductResponse:
        print("Seeding product ...")
        return await self._product_service.create(
            workspace_id=merchant.id,
            name="Test Product",
            description="A test product for development",
            wallet_id=wallet.id,
            external_url="https://discord.gg/test",
            roles=["1520062782840508496"],
            fulfilment_type=ProductFulfilmentType.ROLE,
            price_data={
                "type": PriceType.ONE_TIME,
                "currency": Currency.USD,
                "amount": 10.0,
                "active": True,
                "recurring_interval": None,
                "recurring_interval_count": None,
                "trial_period_days": None,
            },
            db_sess=db_sess,
        )

    async def _seed_price(
        self,
        merchant: WorkspaceResponse,
        product: ProductResponse,
        tokens: list[TokenResponse],
        db_sess: AsyncSession,
    ) -> PriceResponse:
        print("Seeding price ...")
        return await self._price_service.create(
            workspace_id=merchant.id,
            product_id=product.id,
            type=PriceType.ONE_TIME,
            currency=Currency.USD,
            amount=10.0,
            active=True,
            token_ids=[t.id for t in tokens],
            db_sess=db_sess,
        )
