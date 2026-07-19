import json

from core.event import EventDeserialiser
from .enums import SubscriptionEventType
from .event import SubscriptionCancelledEvent, SubscriptionEvent


class SubscriptionEventDeserialiser(EventDeserialiser[SubscriptionEvent]):

    def deserialise_json(self, value: str | bytes) -> SubscriptionCancelledEvent:
        data = json.loads(value)
        return self.deserialise(data)

    def deserialise(self, value: dict) -> SubscriptionCancelledEvent:
        event_type = value["type"]
        if event_type == SubscriptionEventType.SUBSCRIPTION_CANCELLED:
            return SubscriptionCancelledEvent(**value)
        raise ValueError(f"Unknown event type '{event_type}'")
