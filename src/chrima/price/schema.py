from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from core.schema import CustomBaseModel
from chrima.tokens.schema import TokenResponse
from .enums import Currency, PriceType, RecurringInterval


class PriceBase(CustomBaseModel):
    type: PriceType
    currency: Currency
    amount: float
    recurring_interval: RecurringInterval | None
    recurring_interval_count: int | None
    trial_period_days: int | None
    active: bool


class CreatePriceRequest(PriceBase):
    workspace_id: UUID
    product_id: UUID
    token_ids: list[UUID] | None = None
    recurring_interval: RecurringInterval | None = None
    recurring_interval_count: int | None = None
    trial_period_days: int | None = None
    active: bool = True


class UpdatePriceRequest(BaseModel):
    currency: Currency | None = None
    amount: float | None = None
    recurring_interval: RecurringInterval | None = None
    recurring_interval_count: int | None = None
    trial_period_days: int | None = None
    active: bool | None = None


class PriceResponse(PriceBase):
    id: UUID
    workspace_id: UUID
    product_id: UUID
    tokens: list[TokenResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
