from enum import Enum


class NotificationChannelType(str, Enum):
    DISCORD = "discord"
    EMAIL = "email"
