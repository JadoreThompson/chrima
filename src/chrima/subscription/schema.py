from datetime import datetime
from uuid import UUID

from core.schema import CustomBaseModel
from .enums import SubscriptionStatus


class SubscriptionBalanceResponse(CustomBaseModel):
    id: UUID
    external_id: str
    platform_user_id: str
    product_id: UUID
    credit_amount: float
    cycle_start: int | None
    cycle_end: int | None
    status: SubscriptionStatus
    last_processed_tx: UUID | None
    attempt_count: int
    last_notified_at: int | None
    updated_at: datetime
