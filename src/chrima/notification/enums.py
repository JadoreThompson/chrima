from enum import Enum


class NotificationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class NotificationType(str, Enum):
    SUBSCRIPTION_SUFFICIENT = "subscription.sufficient"
    SUBSCRIPTION_EXPIRING = "subscription.expiring"
    SUBSCRIPTION_EXPIRED = "subscription.expired"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    ONE_TIME_PURCHASE = "one_time.purchase"
    BILLING_SUBSCRIPTION_ACTIVATED = "billing.subscription_activated"
    BILLING_SUBSCRIPTION_CANCELLED = "billing.subscription_cancelled"
