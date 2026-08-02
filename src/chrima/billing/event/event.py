from typing import ClassVar, Union
from uuid import UUID

from chrima.user.enums import Tier
from config import KAKFA_BILLING_EVENTS_TOPIC
from core.event import BaseEvent
from ..enums import BillingProvider
from .enums import BillingEventType


class BillingSubscriptionActivatedEvent(BaseEvent):
    topic: ClassVar[str] = KAKFA_BILLING_EVENTS_TOPIC

    type: BillingEventType = BillingEventType.SUBSCRIPTION_ACTIVATED
    user_id: UUID
    customer_id: str
    subscription_id: str
    billing_provider: BillingProvider
    tier: Tier


class BillingSubscriptionCancelledEvent(BaseEvent):
    topic: ClassVar[str] = KAKFA_BILLING_EVENTS_TOPIC

    type: BillingEventType = BillingEventType.SUBSCRIPTION_CANCELLED
    user_id: UUID
    subscription_id: str
    billing_provider: BillingProvider


BillingEvent = Union[
    BillingSubscriptionActivatedEvent, BillingSubscriptionCancelledEvent
]
