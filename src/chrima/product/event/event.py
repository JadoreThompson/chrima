from typing import ClassVar, Union
from uuid import UUID

from config import KAKFA_PRODUCT_EVENTS_TOPIC
from core.event import BaseEvent
from .enums import ProductEventType


class ProductWalletUpdatedEvent(BaseEvent):
    topic: ClassVar[str] = KAKFA_PRODUCT_EVENTS_TOPIC

    type: ProductEventType = ProductEventType.WALLET_UPDATED
    product_id: UUID
    wallet_id: UUID


ProductEvent = Union[ProductWalletUpdatedEvent]
