from contextlib import asynccontextmanager

from argon2 import PasswordHasher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from chrima.auth import AuthService
from chrima.auth.router import router as auth_router
from chrima.discord.router import router as discord_router
from chrima.discord.service.discord import DiscordService
from chrima.encryption import EncryptionService
from chrima.event_bus.publisher import OutboxEventPublisher
from chrima.jwt import JWTService
from chrima.monitoring.router import router as montoring_router
from chrima.price import PriceService
from chrima.price.router import router as price_router
from chrima.subscription.router import router as subscription_router
from chrima.subscription import SubscriptionBalanceService
from chrima.product import ProductService
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
from chrima.analytics import AnalyticsService
from chrima.analytics.router import router as analytics_router
from chrima.workspace.router import router as merchant_router
from .middleware import ExceptionHandlerMiddleware, MetricsMiddleware
from .object_registry import ObjectRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    pw_hasher = PasswordHasher()
    workspace_service = WorkspaceService()
    user_service = UserService(pw_hasher=pw_hasher)
    jwt_service = JWTService(user_service=user_service)
    auth_service = AuthService(user_service=user_service, pw_hasher=pw_hasher)
    token_service = TokenService()
    event_publisher = OutboxEventPublisher()
    price_service = PriceService(event_publisher=event_publisher)
    product_service = ProductService(event_publisher=event_publisher)
    wallet_service = WalletService()
    transaction_service = TransactionService()
    encryption_service = EncryptionService()
    discord_service = DiscordService(encryption_service=encryption_service)
    subscription_service = SubscriptionBalanceService(event_publisher=event_publisher)
    analytics_service = AnalyticsService()

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
    registry.register(discord_service)
    registry.register(subscription_service)
    registry.register(analytics_service)

    app.state.object_registry = registry

    yield

    await registry.close()


app = FastAPI(lifespan=lifespan, title="Chrima")
FastAPIInstrumentor.instrument_app(app)

app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.add_middleware(MetricsMiddleware, excluded_paths={"/monitoring"})

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(merchant_router)
app.include_router(wallet_router)
app.include_router(price_router)
app.include_router(product_router)
app.include_router(token_router)
app.include_router(transaction_router)
app.include_router(discord_router)
app.include_router(subscription_router)
app.include_router(analytics_router)
app.include_router(montoring_router)
