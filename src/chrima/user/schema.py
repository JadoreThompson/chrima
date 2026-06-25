from datetime import datetime
from uuid import UUID

from core.schema import CustomBaseModel


class UserResponse(CustomBaseModel):
    id: UUID
    username: str
    email: str
    created_at: datetime
    updated_at: datetime
