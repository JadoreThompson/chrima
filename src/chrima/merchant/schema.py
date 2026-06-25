from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from core.schema import CustomBaseModel


class CreateMerchantRequest(CustomBaseModel):
    user_id: UUID
    name: str
    wallet_address: str


class UpdateMerchantRequest(BaseModel):
    name: str | None = None
    wallet_address: str | None = None

    def model_post_init(self, context):
        if not self.name and not self.wallet_address:
            raise ValueError("Either name or wallet_address must be provided.")
        return self


class MerchantResponse(CustomBaseModel):
    id: UUID
    user_id: UUID
    name: str
    wallet_address: str
    created_at: datetime
    updated_at: datetime
