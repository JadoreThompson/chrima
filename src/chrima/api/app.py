from argon2 import PasswordHasher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import FRONTEND_DOMAIN, FRONTEND_SUB_DOMAIN, SCHEME
from chrima.auth import AuthService
from chrima.auth.router import router as auth_router
from chrima.jwt import JWTService
from chrima.merchant import MerchantService
from chrima.merchant.router import router as merchant_router
from chrima.merchant.wallet import MerchantWalletService
from chrima.merchant.wallet.router import router as wallet_router
from chrima.price import PriceService
from chrima.price.router import router as price_router
from chrima.product import ProductService
from chrima.product.router import router as product_router
from chrima.tokens import TokenService
from chrima.tokens.router import router as token_router
from chrima.user import UserService
from chrima.user.router import router as user_router
from .middleware import ExceptionHandlerMiddleware
from .object_registry import ObjectRegistry


async def lifespan(app: FastAPI):
    pw_hasher = PasswordHasher()
    user_service = UserService(pw_hasher=pw_hasher)
    jwt_service = JWTService()
    auth_service = AuthService(user_service=user_service, pw_hasher=pw_hasher)
    merchant_service = MerchantService()
    token_service = TokenService()
    price_service = PriceService(token_service=token_service)
    product_service = ProductService(price_service=price_service)
    wallet_service = MerchantWalletService()

    registry = ObjectRegistry()
    registry.register(user_service)
    registry.register(jwt_service)
    registry.register(auth_service)
    registry.register(merchant_service)
    registry.register(token_service)
    registry.register(price_service)
    registry.register(product_service)
    registry.register(wallet_service)

    app.state.object_registry = registry

    yield

    await registry.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"{SCHEME}://{FRONTEND_DOMAIN}",
        f"{SCHEME}://{FRONTEND_SUB_DOMAIN}{FRONTEND_DOMAIN}",
    ],
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
