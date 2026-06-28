import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db_session
from ..channel import NotificationChannelType
from ..enums import NotificationStatus, NotificationType
from ..model import Notification
from ..schema import NotificationContextUnion


class NotificationPublisher:

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    async def publish(
        self,
        recipient: str,
        type: NotificationType,
        context: NotificationContextUnion,
        channel_type: NotificationChannelType,
        db_sess: AsyncSession | None = None
    ) -> None:
        notification = Notification(
            recipient=recipient,
            type=type.value,
            context=context.model_dump(mode="json"),
            channel_type=channel_type.value,
            status=NotificationStatus.PENDING,
        )

        if db_sess is None:
            async with get_db_session() as db_sess:
                db_sess.add(notification)
                await db_sess.commit()
        else:
            db_sess.add(notification)

        self._logger.info(
            f"Enqueued notification '{notification.id}' of type '{type.value}' for user '{recipient}'"
        )
