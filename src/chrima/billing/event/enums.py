from enum import Enum


class BillingEventType(str, Enum):
    SUBSCRIPTION_ACTIVATED = "billing.subscription_activated"
    SUBSCRIPTION_CANCELLED = "billing.subscription_cancelled"
