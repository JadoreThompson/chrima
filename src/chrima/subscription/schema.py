from datetime import datetime
from uuid import UUID

from core.schema import CustomBaseModel
from .enums import SubscriptionStatus


class SubscriptionBalanceResponse(CustomBaseModel):
    id: UUID
    platform_group_id: str
    platform_user_id: str
    product_id: UUID
    credit_amount: float
    cycle_start: int
    cycle_end: int
    status: SubscriptionStatus
    last_processed_tx: UUID | None
    updated_at: datetime
