from enum import Enum


class SubscriptionEventType(str, Enum):
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
