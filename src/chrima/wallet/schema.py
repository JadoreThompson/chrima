from datetime import datetime
from uuid import UUID

from core.schema import CustomBaseModel


class CreateWalletRequest(CustomBaseModel):
    workspace_id: UUID
    name: str
    wallet_address: str


class WalletResponse(CustomBaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    wallet_address: str
    created_at: datetime
