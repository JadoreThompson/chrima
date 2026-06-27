from argon2 import PasswordHasher
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.merchant import MerchantService
from chrima.merchant.schema import MerchantResponse
from chrima.merchant.wallet import MerchantWalletService
from chrima.merchant.wallet.schema import WalletResponse
from chrima.price import PriceService
from chrima.price.enums import Currency, PriceType
from chrima.price.schema import PriceResponse
from chrima.product import ProductService
from chrima.product.enums import GroupType as ProductGroupType
from chrima.product.schema import ProductResponse
from chrima.tokens import TokenService
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.tokens.schema import TokenResponse
from chrima.user import UserService
from chrima.user.schema import UserResponse
from core.db import get_db_session


class DbSeeder:

    def __init__(self) -> None:
        pw_hasher = PasswordHasher()
        self._user_service = UserService(pw_hasher=pw_hasher)
        self._token_service = TokenService()
        self._merchant_service = MerchantService()
        self._wallet_service = MerchantWalletService()
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
        return await self._user_service.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            db_sess=db_sess,
        )

    async def _seed_tokens(self, db_sess: AsyncSession) -> list[TokenResponse]:
        print("Seeding tokens ...")
        tokens = [
            await self._token_service.create_token(
                "USDC", TokenStandard.ERC_20, TokenChain.ETH, db_sess
            ),
            await self._token_service.create_token(
                "WETH", TokenStandard.ERC_20, TokenChain.ETH, db_sess
            ),
            await self._token_service.create_token(
                "DAI", TokenStandard.ERC_20, TokenChain.ETH, db_sess
            ),
        ]
        return tokens

    async def _seed_merchant(
        self, user: UserResponse, db_sess: AsyncSession
    ) -> MerchantResponse:
        print("Seeding merchant ...")
        return await self._merchant_service.create_merchant(
            user_id=user.id,
            name="Test Merchant",
            wallet_address="0x1234567890abcdef1234567890abcdef12345678",
            db_sess=db_sess,
        )

    async def _seed_wallet(
        self, merchant: MerchantResponse, tokens: list[TokenResponse], db_sess: AsyncSession
    ) -> WalletResponse:
        print("Seeding wallet ...")
        return await self._wallet_service.create_wallet(
            merchant_id=merchant.id,
            name="Test Wallet",
            wallet_address="0xabcdef1234567890abcdef1234567890abcdef12",
            token_ids=[t.id for t in tokens],
            db_sess=db_sess,
        )

    async def _seed_product(
        self, merchant: MerchantResponse, wallet: WalletResponse, db_sess: AsyncSession
    ) -> ProductResponse:
        print("Seeding product ...")
        return await self._product_service.create_product(
            merchant_id=merchant.id,
            name="Test Product",
            description="A test product for development",
            wallet_id=wallet.id,
            group_type=ProductGroupType.DISCORD,
            group_url="https://discord.gg/test",
            roles=["member"],
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
        merchant: MerchantResponse,
        product: ProductResponse,
        tokens: list[TokenResponse],
        db_sess: AsyncSession,
    ) -> PriceResponse:
        print("Seeding price ...")
        return await self._price_service.create_price(
            merchant_id=merchant.id,
            product_id=product.id,
            type=PriceType.ONE_TIME,
            currency=Currency.USD,
            amount=10.0,
            active=True,
            token_ids=[t.id for t in tokens],
            db_sess=db_sess,
        )
