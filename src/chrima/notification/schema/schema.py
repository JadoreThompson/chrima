from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from ..channel import NotificationChannelType


class NotificationChannelConfig(NamedTuple):
    type: "NotificationChannelType"
    expires_at: int | None = None
    """Unix epoch timestamp"""
    max_retries: int = 3
