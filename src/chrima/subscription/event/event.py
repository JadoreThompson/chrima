from typing import ClassVar, Union
from uuid import UUID

from config import KAKFA_SUBSCRIPTION_EVENTS_TOPIC
from core.event import BaseEvent
from .enums import SubscriptionEventType


class SubscriptionCancelledEvent(BaseEvent):
    topic: ClassVar[str] = KAKFA_SUBSCRIPTION_EVENTS_TOPIC

    type: SubscriptionEventType = SubscriptionEventType.SUBSCRIPTION_CANCELLED
    subscription_balance_id: UUID
    external_id: str
    platform_user_id: str
    product_id: UUID


SubscriptionEvent = Union[SubscriptionCancelledEvent]
