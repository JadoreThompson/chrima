from enum import Enum


class NotificationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class NotificationType(str, Enum):
    SUBSCRIPTION_SUFFICIENT = "subscription.sufficient"
    SUBSCRIPTION_EXPIRING = "subscription.expiring"
    SUBSCRIPTION_EXPIRED = "subscription.expired"
