from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from core.schema import CustomBaseModel
from .enums import Currency, PriceType, RecurringInterval


class PriceBase(CustomBaseModel):
    type: PriceType
    currency: Currency
    amount: float
    recurring_interval: RecurringInterval | None
    recurring_interval_count: int | None
    trial_period_days: int | None


class CreatePriceRequest(PriceBase):
    workspace_id: UUID
    product_id: UUID
    recurring_interval: RecurringInterval | None = None
    recurring_interval_count: int | None = None
    trial_period_days: int | None = None


class UpdatePriceRequest(BaseModel):
    currency: Currency | None = None
    amount: float | None = None
    recurring_interval: RecurringInterval | None = None
    recurring_interval_count: int | None = None
    trial_period_days: int | None = None


class PriceResponse(PriceBase):
    id: UUID
    workspace_id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: datetime
