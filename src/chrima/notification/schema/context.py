from typing import Union
from uuid import UUID

from core.schema import CustomBaseModel
from ..enums import NotificationType


class NotificationContext(CustomBaseModel):
    pass


class SubscriptionSufficientNotificationContext(NotificationContext):
    guild_id: str
    channel_id: str
    platform_user_id: str
    product_id: UUID
    product_name: str
    product_price: float
    currency: str
    remaining_amount: float
    transaction_id: UUID


class SubscriptionExpiringNotificationContext(NotificationContext):
    guild_id: str
    channel_id: str
    platform_user_id: str
    product_id: UUID
    product_name: str
    cycle_end: int


class SubscriptionExpiredNotificationContext(NotificationContext):
    guild_id: str
    channel_id: str
    platform_user_id: str
    product_id: UUID
    product_name: str
    cycle_end: int


class SubscriptionRenewedNotificationContext(NotificationContext):
    guild_id: str
    channel_id: str
    platform_user_id: str
    product_id: UUID
    product_name: str
    product_price: float
    currency: str
    transaction_id: UUID


class OneTimePurchaseNotificationContext(NotificationContext):
    guild_id: str
    channel_id: str
    platform_user_id: str
    product_id: UUID
    product_name: str
    product_price: float
    currency: str
    transaction_id: UUID


class BillingSubscriptionActivatedNotificationContext(NotificationContext):
    user_id: str
    username: str
    email: str
    tier: str
    billing_provider: str
    subscription_id: str


class BillingSubscriptionCancelledNotificationContext(NotificationContext):
    user_id: str
    username: str
    email: str
    tier: str


NotificationContextUnion = Union[
    SubscriptionSufficientNotificationContext,
    SubscriptionExpiringNotificationContext,
    SubscriptionExpiredNotificationContext,
    SubscriptionRenewedNotificationContext,
    OneTimePurchaseNotificationContext,
    BillingSubscriptionActivatedNotificationContext,
    BillingSubscriptionCancelledNotificationContext,
]


class Notification(CustomBaseModel):
    recipient: str
    type: NotificationType
    context: NotificationContextUnion
