import asyncio
import logging

import stripe

from chrima.user.enums import Tier
from config import (
    BILLING_CANCEL_URL,
    BILLING_SUCCESS_URL,
    STRIPE_API_KEY,
    STRIPE_PRO_PRICE_ID,
)
from ..exception import BillingProviderDisabledException
from ..schema import CheckoutSession
from .base import BillingProvider


def ensure_enabled(func):
    """Decorator to ensure that the billing provider is enabled before calling the function."""

    async def wrapper(self, *args, **kwargs):
        if not self._enabled:
            raise BillingProviderDisabledException("stripe")
        return await func(self, *args, **kwargs)

    return wrapper


class StripeBillingProvider(BillingProvider):
    def __init__(
        self,
        *,
        api_key: str = STRIPE_API_KEY,
        success_url: str = BILLING_SUCCESS_URL,
        cancel_url: str = BILLING_CANCEL_URL,
        pro_price_id: str = STRIPE_PRO_PRICE_ID,
    ) -> None:
        super().__init__()

        self._logger = logging.getLogger("stripe_billing_provider")
        print(f"StripeBillingProvider initialized with api_key={api_key}, success_url={success_url}, cancel_url={cancel_url}, pro_price_id={pro_price_id}")
        self._enabled = bool(api_key and pro_price_id)
        if not self._enabled:
            self._logger.warning(
                "Stripe billing provider is not enabled. "
                "Set STRIPE_API_KEY and STRIPE_PRO_PRICE_ID in the environment variables."
            )
            return

        stripe.api_key = api_key
        self._api_key = api_key
        self._success_url = success_url
        self._cancel_url = cancel_url
        self._tier_price_map = {Tier.PRO: pro_price_id}

    @ensure_enabled
    async def create_checkout_session(
        self, tier: Tier, metadata: dict | None = None
    ) -> CheckoutSession:
        """Create a Stripe checkout session for the given tier."""
        price_id = self._tier_price_map.get(tier)
        if price_id is None:
            raise ValueError(f"No Stripe price configured for tier '{tier.value}'")

        metadata = metadata or {}

        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=self._success_url,
            cancel_url=self._cancel_url,
            metadata=metadata,
            subscription_data={"metadata": metadata},
        )

        self._logger.info(
            "Created checkout session '%s' for tier '%s'", session.id, tier.value
        )
        return CheckoutSession(id=session.id, url=session.url)

    @ensure_enabled
    async def cancel_subscription(self, subscription_id: str) -> None:
        """Cancel a Stripe subscription immediately."""
        await asyncio.to_thread(stripe.Subscription.cancel, subscription_id)
        self._logger.info("Cancelled subscription '%s'", subscription_id)
