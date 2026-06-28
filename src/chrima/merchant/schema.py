from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from core.schema import CustomBaseModel


class CreateMerchantRequest(CustomBaseModel):
    user_id: UUID
    name: str
    wallet_address: str
    notification_channel: str


class UpdateMerchantRequest(BaseModel):
    name: str | None = None
    wallet_address: str | None = None
    notification_channel: str | None = None

    def model_post_init(self, context):
        if not self.name and not self.wallet_address and not self.notification_channel:
            raise ValueError("At least one field must be provided.")
        return self


class MerchantResponse(CustomBaseModel):
    id: UUID
    user_id: UUID
    name: str
    wallet_address: str
    notification_channel: str
    created_at: datetime
    updated_at: datetime
