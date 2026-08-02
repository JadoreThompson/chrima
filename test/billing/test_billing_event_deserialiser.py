from uuid import uuid4

import pytest

from chrima.billing.enums import BillingProvider
from chrima.billing.event import BillingEventDeserialiser
from chrima.billing.event.enums import BillingEventType
from chrima.user.enums import Tier


@pytest.fixture
def deserialiser():
    return BillingEventDeserialiser()


class TestDeserialise:
    def test_deserialises_activated_event(self, deserialiser):
        payload = {
            "type": BillingEventType.SUBSCRIPTION_ACTIVATED,
            "user_id": str(uuid4()),
            "customer_id": "cus_1",
            "subscription_id": "sub_1",
            "billing_provider": BillingProvider.STRIPE,
            "tier": Tier.PRO,
        }

        event = deserialiser.deserialise(payload)

        assert event.type == BillingEventType.SUBSCRIPTION_ACTIVATED
        assert event.subscription_id == "sub_1"
        assert event.billing_provider == BillingProvider.STRIPE
        assert event.tier == Tier.PRO

    def test_deserialises_cancelled_event(self, deserialiser):
        payload = {
            "type": BillingEventType.SUBSCRIPTION_CANCELLED,
            "user_id": str(uuid4()),
            "subscription_id": "sub_1",
            "billing_provider": BillingProvider.STRIPE,
        }

        event = deserialiser.deserialise(payload)

        assert event.type == BillingEventType.SUBSCRIPTION_CANCELLED
        assert event.subscription_id == "sub_1"

    def test_deserialises_json(self, deserialiser):
        payload = (
            '{"type": "billing.subscription_activated", '
            '"user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", '
            '"customer_id": "cus_1", "subscription_id": "sub_1", '
            '"billing_provider": "stripe", "tier": "pro"}'
        )

        event = deserialiser.deserialise_json(payload)

        assert event.type == BillingEventType.SUBSCRIPTION_ACTIVATED

    def test_raises_on_unknown_type(self, deserialiser):
        with pytest.raises(ValueError):
            deserialiser.deserialise({"type": "billing.unknown"})
