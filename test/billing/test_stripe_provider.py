from unittest.mock import MagicMock, patch

import pytest

from chrima.billing.exception import BillingProviderDisabledException
from chrima.billing.provider.stripe import StripeBillingProvider
from chrima.billing.schema import CheckoutSession
from chrima.user.enums import Tier
from config import BILLING_CANCEL_URL, BILLING_SUCCESS_URL


@pytest.fixture
def mock_stripe():
    with patch("chrima.billing.provider.stripe.stripe") as mock:
        yield mock


@pytest.mark.asyncio(loop_scope="session")
class TestCreateCheckoutSession:
    async def test_creates_checkout_session(self, mock_stripe):
        mock_stripe.checkout.Session.create.return_value = MagicMock(
            id="cs_test_123", url="https://checkout.stripe.com/pay/cs_test_123"
        )

        provider = StripeBillingProvider(
            api_key="sk_test", pro_price_id="price_pro_123"
        )

        session = await provider.create_checkout_session(
            Tier.PRO, metadata={"user_id": "user_1"}
        )

        assert isinstance(session, CheckoutSession)
        assert session.id == "cs_test_123"
        assert session.url == "https://checkout.stripe.com/pay/cs_test_123"
        mock_stripe.checkout.Session.create.assert_called_once_with(
            mode="subscription",
            line_items=[{"price": "price_pro_123", "quantity": 1}],
            success_url=BILLING_SUCCESS_URL,
            cancel_url=BILLING_CANCEL_URL,
            metadata={"user_id": "user_1"},
            subscription_data={"metadata": {"user_id": "user_1"}},
        )

    async def test_raises_for_tier_without_price(self, mock_stripe):
        provider = StripeBillingProvider(
            api_key="sk_test", pro_price_id="price_pro_123"
        )

        with pytest.raises(ValueError):
            await provider.create_checkout_session(Tier.FREE)

        mock_stripe.checkout.Session.create.assert_not_called()

    async def test_raises_when_disabled(self, mock_stripe):
        provider = StripeBillingProvider(api_key="", pro_price_id=None)

        with pytest.raises(BillingProviderDisabledException):
            await provider.create_checkout_session(Tier.PRO)

        mock_stripe.checkout.Session.create.assert_not_called()


@pytest.mark.asyncio(loop_scope="session")
class TestCancelSubscription:
    async def test_cancels_subscription(self, mock_stripe):
        provider = StripeBillingProvider(
            api_key="sk_test", pro_price_id="price_pro_123"
        )

        await provider.cancel_subscription("sub_123")

        mock_stripe.Subscription.cancel.assert_called_once_with("sub_123")

    async def test_raises_when_disabled(self, mock_stripe):
        provider = StripeBillingProvider(api_key="", pro_price_id=None)

        with pytest.raises(BillingProviderDisabledException):
            await provider.cancel_subscription("sub_123")

        mock_stripe.Subscription.cancel.assert_not_called()
