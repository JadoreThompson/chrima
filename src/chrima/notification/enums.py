from enum import Enum


class NotificationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class NotificationType(str, Enum):
    SUBSCRIPTION_INCOMPLETE = "subscription.incomplete"
    SUBSCRIPTION_SUFFICIENT = "subscription.sufficient"
    SUBSCRIPTION_NOW_SUFFICIENT = "subscription.now_sufficient"
    SUBSCRIPTION_EXPIRING = "subscription.expiring"
    SUBSCRIPTION_EXPIRED = "subscription.expired"
