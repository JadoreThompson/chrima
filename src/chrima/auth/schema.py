from uuid import UUID

from pydantic import BaseModel
from core.schema import CustomBaseModel


class RegisterRequest(CustomBaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class SelectWorkspaceRequest(CustomBaseModel):
    workspace_id: UUID
