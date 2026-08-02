import json

from core.event import EventDeserialiser
from .enums import BillingEventType
from .event import (
    BillingEvent,
    BillingSubscriptionActivatedEvent,
    BillingSubscriptionCancelledEvent,
)


class BillingEventDeserialiser(EventDeserialiser[BillingEvent]):

    def deserialise_json(self, value: str | bytes) -> BillingEvent:
        data = json.loads(value)
        return self.deserialise(data)

    def deserialise(self, value: dict) -> BillingEvent:
        event_type = value["type"]
        if event_type == BillingEventType.SUBSCRIPTION_ACTIVATED:
            return BillingSubscriptionActivatedEvent(**value)
        if event_type == BillingEventType.SUBSCRIPTION_CANCELLED:
            return BillingSubscriptionCancelledEvent(**value)
        raise ValueError(f"Unknown event type '{event_type}'")
