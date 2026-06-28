import json

from core.event import EventDeserialiser
from .enums import TransactionEventType
from .event import TransactionCompletedEvent, TransactionEvent


class TransactionEventDeserialiser(EventDeserialiser[TransactionEvent]):

    def deserialise_json(self, value: str | bytes) -> TransactionEvent:
        data = json.loads(value)
        return self.deserialise(data)

    def deserialise(self, value: dict) -> TransactionEvent:
        event_type = value["type"]

        if event_type == TransactionEventType.COMPLETED:
            return TransactionCompletedEvent(**value)

        raise ValueError(f"Unknown event type '{event_type}'")
