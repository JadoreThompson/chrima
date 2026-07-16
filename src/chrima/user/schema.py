from datetime import datetime
from uuid import UUID

from core.schema import CustomBaseModel


class WorkspaceMeta(CustomBaseModel):
    id: UUID
    name: str


class UserDto(CustomBaseModel):
    id: UUID
    username: str
    email: str
    created_at: datetime
    updated_at: datetime


class UserProfile(UserDto):
    workspaces: list[WorkspaceMeta]
