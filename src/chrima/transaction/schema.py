from uuid import UUID

from core.schema import CustomBaseModel
from .enums import TransactionStatus


class TransactionResponse(CustomBaseModel):
    id: UUID
    product_id: UUID
    price_id: UUID
    sender: str
    address: str
    amount: float
    status: TransactionStatus
    timestamp: int
