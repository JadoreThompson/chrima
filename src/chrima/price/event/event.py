from typing import ClassVar, Union
from uuid import UUID

from config import KAKFA_PRICE_EVENTS_TOPIC
from core.event import BaseEvent
from .enums import PriceEventType


class PriceUpdatedEvent(BaseEvent):
    topic: ClassVar[str] = KAKFA_PRICE_EVENTS_TOPIC

    type: PriceEventType = PriceEventType.PRICE_UPDATED
    price_id: UUID
    amount: float


PriceEvent = Union[PriceUpdatedEvent]
