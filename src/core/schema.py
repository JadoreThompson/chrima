from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    model_config = {
        "json_encoders": {
            UUID: str,
            datetime: lambda dt: dt.isoformat().replace("+00:00", "Z"), # For Zod compatibility
            Enum: lambda e: e.value,
        }
    }
