from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from chrima.user.enums import Tier
from core.schema import CustomBaseModel
from .enums import BillingProvider, BillingStatus


class CreateCheckoutSessionRequest(CustomBaseModel):
    tier: Tier

    @field_validator("tier", mode="after")
    def validate_tier(cls, v: Tier) -> Tier:
        if v == Tier.FREE:
            raise ValueError("Cannot create checkout session for free tier")
        return v


class CheckoutSession(BaseModel):
    id: str
    url: str


class CreateCheckoutSessionResponse(CustomBaseModel):
    url: str


class BillingResponse(CustomBaseModel):
    id: UUID
    user_id: UUID
    subscription_id: str
    billing_provider: BillingProvider
    customer_id: str
    status: BillingStatus
    created_at: datetime
    updated_at: datetime
