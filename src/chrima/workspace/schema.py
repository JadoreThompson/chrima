from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from core.schema import CustomBaseModel
from .enums import MessagePlatformType


class CreateWorkspaceRequest(CustomBaseModel):
    name: str
    platform: MessagePlatformType
    external_id: str
    notification_channel_id: str


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = None
    notification_channel_id: str | None = None

    def model_post_init(self, context):
        if not self.name and not self.notification_channel_id:
            raise ValueError("At least one field must be provided.")
        return self


class WorkspaceResponse(CustomBaseModel):
    id: UUID
    platform: MessagePlatformType
    external_id: str
    notification_channel_id: str
    name: str
    created_at: datetime
    updated_at: datetime
