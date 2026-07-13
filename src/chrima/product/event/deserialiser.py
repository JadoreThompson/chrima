import json

from core.event import EventDeserialiser
from .enums import ProductEventType
from .event import ProductWalletUpdatedEvent, ProductEvent


class ProductEventDeserialiser(EventDeserialiser[ProductEvent]):

    def deserialise_json(self, value: str | bytes) -> ProductWalletUpdatedEvent:
        data = json.loads(value)
        return self.deserialise(data)

    def deserialise(self, value: dict) -> ProductWalletUpdatedEvent:
        event_type = value["type"]
        if event_type == ProductEventType.WALLET_UPDATED:
            return ProductWalletUpdatedEvent(**value)
        raise ValueError(f"Unknown event type '{event_type}'")
