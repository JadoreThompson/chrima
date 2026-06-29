from enum import Enum
from chrima.message_platform.enums import MessagePlatform


class FulfilmentType(str, Enum):
    INVITE = "invite"
    ROLE = "role"
