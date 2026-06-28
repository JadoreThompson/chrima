from typing import ClassVar, Union
from uuid import UUID

from config import KAKFA_TRANSACTION_EVENTS_TOPIC
from core.event import BaseEvent
from .enums import TransactionEventType


class BaseTransactionEvent(BaseEvent):
    topic: ClassVar[str] = KAKFA_TRANSACTION_EVENTS_TOPIC


class TransactionCompletedEvent(BaseTransactionEvent):
    type: TransactionEventType = TransactionEventType.COMPLETED
    transaction_id: UUID
    product_id: UUID
    price_id: UUID
    sender: str
    recipient: str
    token_address: str
    token_amount: int
    group_user_id: str


class TransactionCompletedEventV2(BaseTransactionEvent):
    type: TransactionEventType = TransactionEventType.COMPLETED
    transaction_id: UUID
    product_id: UUID
    price_id: UUID
    group_user_id: str
    amount: int


TransactionEvent = Union[TransactionCompletedEvent]
