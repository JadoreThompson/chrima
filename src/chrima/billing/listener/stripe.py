import logging
from uuid import UUID

import stripe
from stripe import Event as StripeEvent
from stripe.checkout import Session as StripeCheckoutSession
from sqlalchemy.ext.asyncio import AsyncSession

from config import STRIPE_WEBHOOK_SECRET
from .base import BillingWebhookListener
from ..enums import BillingProvider
from ..exception import BillingWebhookVerificationException
from ..model import BillingWebhookEvent
from ..service.billing import BillingService

CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
SUBSCRIPTION_DELETED = "customer.subscription.deleted"
PAID_STATUSES = ("paid", "no_payment_required")
SignatureVerificationError = stripe.error.SignatureVerificationError


class StripeBillingWebhookListener(BillingWebhookListener):
    def __init__(
        self,
        *,
        billing_service: BillingService,
        webhook_secret: str = STRIPE_WEBHOOK_SECRET,
    ):
        self._billing_service = billing_service
        self._webhook_secret = webhook_secret
        self._logger = logging.getLogger("stripe_billing_webhook_listener")

    async def handle(self, headers: dict, payload: bytes, db_sess: AsyncSession):
        event = self._verify(payload, headers)

        if await self._already_processed(event, db_sess):
            return

        await self._process(event, db_sess)

        db_sess.add(
            BillingWebhookEvent(
                provider=BillingProvider.STRIPE,
                event_id=event.id,
                type=event.type,
            )
        )
        await db_sess.flush()

    def _verify(self, payload: bytes, headers: dict) -> StripeEvent:
        sig_header = headers.get("stripe-signature")
        if not sig_header:
            raise BillingWebhookVerificationException(
                "Missing 'stripe-signature' header."
            )
        if not self._webhook_secret:
            raise BillingWebhookVerificationException(
                "STRIPE_WEBHOOK_SECRET is not configured."
            )

        try:
            return stripe.Webhook.construct_event(
                payload, sig_header, self._webhook_secret
            )
        except (ValueError, SignatureVerificationError):
            raise BillingWebhookVerificationException()

    async def _already_processed(self, event, db_sess: AsyncSession) -> bool:
        existing = await db_sess.get(
            BillingWebhookEvent, (BillingProvider.STRIPE.value, event.id)
        )
        return existing is not None

    async def _process(self, event: StripeEvent, db_sess: AsyncSession) -> None:
        event_type = event.type
        data = event.data.object

        if event_type == CHECKOUT_SESSION_COMPLETED:
            await self._handle_checkout_session_completed(data, db_sess)
        elif event_type == SUBSCRIPTION_DELETED:
            await self._handle_subscription_deleted(data, db_sess)
        else:
            self._logger.info("Unhandled billing webhook event type '%s'", event_type)

    async def _handle_checkout_session_completed(
        self, session: StripeCheckoutSession, db_sess: AsyncSession
    ) -> None:
        if session.payment_status not in PAID_STATUSES:
            return

        metadata = session.metadata.to_dict() if session.metadata else {}
        user_id = metadata.get("user_id")
        customer_id = session.customer
        subscription_id = session.subscription

        if not user_id:
            self._logger.warning(
                "Checkout session '%s' is missing 'user_id' metadata",
                session.id,
            )
            return

        if not customer_id or not subscription_id:
            self._logger.warning(
                "Checkout session '%s' is missing customer or subscription",
                session.id,
            )
            return

        await self._billing_service.activate_subscription(
            user_id=UUID(user_id),
            subscription_id=subscription_id,
            customer_id=customer_id,
            billing_provider=BillingProvider.STRIPE,
            db_sess=db_sess,
        )

    async def _handle_subscription_deleted(
        self, subscription: stripe.Subscription, db_sess: AsyncSession
    ) -> None:
        subscription_id = subscription.id
        if not subscription_id:
            return
        await self._billing_service.cancel_subscription_webhook(
            subscription_id, db_sess
        )
