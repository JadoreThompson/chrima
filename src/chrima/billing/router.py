from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.jwt.schema import JWTPayload
from .listener import BillingWebhookListener
from .schema import CreateCheckoutSessionRequest
from .service.billing import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout-session")
async def create_checkout_session(
    body: CreateCheckoutSessionRequest,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    billing_service: BillingService = Depends(depends_object(BillingService)),
):
    ch = await billing_service.create_checkout_session(jwt.sub, body.tier, db_sess)
    await db_sess.commit()
    return ch


@router.post("/cancel-subscription")
async def cancel_subscription(
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    billing_service: BillingService = Depends(depends_object(BillingService)),
):
    ch = await billing_service.cancel_subscription(jwt.sub, db_sess)
    return ch


@router.post("/webhook")
async def webhook(
    req: Request,
    billing_webhook_listener: BillingWebhookListener = Depends(
        depends_object(BillingWebhookListener, subclass=True)
    ),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    await billing_webhook_listener.handle(req.headers, await req.body(), db_sess)
    await db_sess.commit()
