from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from core.schema import CustomBaseModel
from chrima.price.enums import RecurringInterval
from chrima.price.schema import PriceBase
from .enums import AccessType, GroupType


class CreatePriceRequest(PriceBase):
    recurring_interval: RecurringInterval | None = None
    recurring_interval_count: int | None = None
    trial_period_days: int | None = None
    active: bool = True


class CreateProductRequest(CustomBaseModel):
    name: str
    description: str | None = None
    wallet_id: UUID
    group_type: GroupType
    group_url: str | None = None
    group_id: str | None = None
    roles: list[str] | None = None
    access_type: AccessType
    price: CreatePriceRequest


class UpdateProductRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class ProductResponse(CustomBaseModel):
    id: UUID
    merchant_id: UUID
    name: str
    description: str | None
    wallet_id: UUID
    price_id: UUID | None
    group_type: GroupType
    group_url: str | None
    group_id: str | None
    roles: list[str] | None
    access_type: AccessType
    created_at: datetime
    updated_at: datetime
