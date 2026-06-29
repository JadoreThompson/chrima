from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from core.schema import CustomBaseModel
from chrima.price.enums import RecurringInterval
from chrima.price.schema import PriceBase
from .enums import FulfilmentType


class CreatePriceRequest(PriceBase):
    recurring_interval: RecurringInterval | None = None
    recurring_interval_count: int | None = None
    trial_period_days: int | None = None
    active: bool = True


class CreateProductRequest(CustomBaseModel):
    name: str
    description: str | None = None
    wallet_id: UUID
    fulfilment_type: FulfilmentType
    external_url: str | None = None
    roles: list[str] | None = None
    price: CreatePriceRequest


class UpdateProductRequest(BaseModel):
    name: str | None = None
    wallet_id: UUID | None = None
    description: str | None = None
    roles: list[str] | None = None


class ProductResponse(CustomBaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    wallet_id: UUID
    price_id: UUID | None
    external_url: str | None
    roles: list[str] | None
    fulfilment_type: FulfilmentType
    created_at: datetime
    updated_at: datetime
