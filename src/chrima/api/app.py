import asyncio

from argon2 import PasswordHasher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from web3 import AsyncWeb3

from chrima.encryption import EncryptionService
from chrima.auth import AuthService
from chrima.auth.router import router as auth_router
from chrima.event_bus.publisher import OutboxEventPublisher
from chrima.jwt import JWTService
from chrima.message_platform import MessagePlatformService
from chrima.message_platform.service.oauth.discord import DiscordOauthService
from chrima.price import PriceService
from chrima.price.service.sync import PriceSyncService
from chrima.price.event import PriceEventDeserialiser
from chrima.price.router import router as price_router
from chrima.product import ProductService, ProductSyncService
from chrima.product.event import ProductEventDeserialiser
from chrima.product.router import router as product_router
from chrima.tokens import TokenService
from chrima.tokens.router import router as token_router
from chrima.transaction import TransactionService
from chrima.transaction.router import router as transaction_router
from chrima.user import UserService
from chrima.user.router import router as user_router
from chrima.wallet import WalletService
from chrima.wallet.router import router as wallet_router
from chrima.workspace import WorkspaceService
from chrima.workspace.router import router as merchant_router
from config import (
    CHRIMA_PAYMENT_CONTRACT_ABI,
    CHRIMA_PAYMENT_CONTRACT_ADDRESS,
    DOMAIN,
    RPC_URL,
    SCHEME,
    SIGNER_PRIVATE_KEY,
)
from .middleware import ExceptionHandlerMiddleware
from .object_registry import ObjectRegistry


async def lifespan(app: FastAPI):
    pw_hasher = PasswordHasher()
    workspace_service = WorkspaceService()
    user_service = UserService(pw_hasher=pw_hasher)
    jwt_service = JWTService(user_service=user_service)
    auth_service = AuthService(user_service=user_service, pw_hasher=pw_hasher)
    token_service = TokenService()
    event_publisher = OutboxEventPublisher()
    price_service = PriceService(
        token_service=token_service, event_publisher=event_publisher
    )
    product_service = ProductService(
        price_service=price_service,
        event_publisher=event_publisher,
    )
    wallet_service = WalletService()
    transaction_service = TransactionService()
    discord_oauth_service = DiscordOauthService()
    encryption_service = EncryptionService()
    message_platform_service = MessagePlatformService(
        discord_oauth_service=discord_oauth_service,
        encryption_service=encryption_service,
    )

    price_sync_task = None
    product_sync_task = None
    if CHRIMA_PAYMENT_CONTRACT_ADDRESS and SIGNER_PRIVATE_KEY:
        w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URL))
        contract = w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(CHRIMA_PAYMENT_CONTRACT_ADDRESS),
            abi=CHRIMA_PAYMENT_CONTRACT_ABI,
        )
        price_sync = PriceSyncService(
            w3=w3,
            contract=contract,
            signer_private_key=SIGNER_PRIVATE_KEY,
            deserialiser=PriceEventDeserialiser(),
        )
        price_sync_task = asyncio.create_task(price_sync.run())
        product_sync = ProductSyncService(
            w3=w3,
            contract=contract,
            signer_private_key=SIGNER_PRIVATE_KEY,
            deserialiser=ProductEventDeserialiser(),
        )
        product_sync_task = asyncio.create_task(product_sync.run())

    registry = ObjectRegistry()
    registry.register(user_service)
    registry.register(jwt_service)
    registry.register(auth_service)
    registry.register(workspace_service)
    registry.register(token_service)
    registry.register(price_service)
    registry.register(product_service)
    registry.register(wallet_service)
    registry.register(transaction_service)
    registry.register(discord_oauth_service)
    registry.register(message_platform_service)

    app.state.object_registry = registry

    yield

    if price_sync_task is not None:
        price_sync_task.cancel()
        try:
            await price_sync_task
        except asyncio.CancelledError:
            pass
    if product_sync_task is not None:
        product_sync_task.cancel()
        try:
            await product_sync_task
        except asyncio.CancelledError:
            pass
    await registry.close()


app = FastAPI(lifespan=lifespan, title="Chrima")

app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"{SCHEME}://{DOMAIN}"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(merchant_router)
app.include_router(wallet_router)
app.include_router(price_router)
app.include_router(product_router)
app.include_router(token_router)
app.include_router(transaction_router)
