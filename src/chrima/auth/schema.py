from uuid import UUID

from pydantic import BaseModel
from core.schema import CustomBaseModel


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class SelectWorkspaceRequest(CustomBaseModel):
    workspace_id: UUID


class ChangeUsernameRequest(BaseModel):
    username: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ChangeEmailRequest(BaseModel):
    email: str
