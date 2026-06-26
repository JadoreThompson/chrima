from enum import Enum


class AccessType(str, Enum):
    INVITE = "invite"
    ROLE = "role"


class GroupType(str, Enum):
    DISCORD = "discord"
