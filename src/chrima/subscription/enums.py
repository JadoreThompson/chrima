from enum import Enum


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"
    """The subscription requires more amount from the customer"""
