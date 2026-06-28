from typing import Union
from uuid import UUID

from core.schema import CustomBaseModel
from .enums import NotificationType


class NotificationContext(CustomBaseModel):
    pass


class SubscriptionIncompleteNotificationContext(NotificationContext):
    guild_id: str
    channel_id: str
    platform_user_id: str
    product_id: str
    product_name: str
    product_price: float
    currency: str
    remaining_amount: float
    transaction_id: UUID


class SubscriptionSufficientNotificationContext(NotificationContext):
    guild_id: str
    channel_id: str
    platform_user_id: str
    product_id: str
    product_name: str
    product_price: float
    currency: str
    remaining_amount: float
    transaction_id: UUID


class SubscriptionNowSufficientNotificationContext(NotificationContext):
    guild_id: str
    channel_id: str
    platform_user_id: str
    product_id: str
    product_name: str
    product_price: float
    currency: str
    remaining_amount: float
    transaction_id: UUID


NotificationContextUnion = Union[
    SubscriptionIncompleteNotificationContext,
    SubscriptionSufficientNotificationContext,
    SubscriptionNowSufficientNotificationContext,
]


class Notification(CustomBaseModel):
    recipient: str
    type: NotificationType
    context: NotificationContextUnion
