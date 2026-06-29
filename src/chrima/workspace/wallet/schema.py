from datetime import datetime
from uuid import UUID

from core.schema import CustomBaseModel


class CreateWalletRequest(CustomBaseModel):
    merchant_id: UUID
    name: str
    wallet_address: str
    token_ids: list[UUID]


class WalletResponse(CustomBaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    wallet_address: str
    token_ids: list[UUID]
    created_at: datetime
