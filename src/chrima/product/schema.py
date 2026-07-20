from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from core.schema import CustomBaseModel
from .enums import FulfilmentType


class CreateProductRequest(CustomBaseModel):
    workspace_id: UUID
    name: str
    description: str | None = None
    wallet_id: UUID
    fulfilment_type: FulfilmentType
    external_url: str | None = None
    roles: list[str] | None = None


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
    external_url: str | None
    roles: list[str] | None
    fulfilment_type: FulfilmentType
    created_at: datetime
    updated_at: datetime
