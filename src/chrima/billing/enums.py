from enum import Enum


class BillingProvider(str, Enum):
    STRIPE = "stripe"


class BillingStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
