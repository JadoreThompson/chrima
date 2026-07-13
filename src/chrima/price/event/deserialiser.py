import json

from core.event import EventDeserialiser
from .enums import PriceEventType
from .event import PriceUpdatedEvent, PriceEvent


class PriceEventDeserialiser(EventDeserialiser[PriceEvent]):

    def deserialise_json(self, value: str | bytes) -> PriceUpdatedEvent:
        data = json.loads(value)
        return self.deserialise(data)

    def deserialise(self, value: dict) -> PriceUpdatedEvent:
        event_type = value["type"]
        if event_type == PriceEventType.PRICE_UPDATED:
            return PriceUpdatedEvent(**value)
        raise ValueError(f"Unknown event type '{event_type}'")
