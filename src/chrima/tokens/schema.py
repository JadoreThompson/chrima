from uuid import UUID

from core.schema import CustomBaseModel
from .enums import TokenChain, TokenStandard


class TokenResponse(CustomBaseModel):
    id: UUID
    name: str
    standard: TokenStandard
    chain: TokenChain
