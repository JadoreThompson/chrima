import logging

from sqlalchemy.ext.asyncio import AsyncSession

from infra.db import get_db_session
from ..enums import NotificationStatus, NotificationType
from ..model import Notification, NotificationChannel
from ..schema import NotificationContextUnion, NotificationChannelConfig

MAX_RETRIES = 3


class NotificationPublisher:
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    async def publish(
        self,
        recipient: str,
        type: NotificationType,
        context: NotificationContextUnion,
        channel_configs: list[NotificationChannelConfig],
        *,
        db_sess: AsyncSession | None = None,
    ) -> None:
        notification = Notification(
            recipient=recipient,
            type=type.value,
            context=context.model_dump(mode="json"),
            status=NotificationStatus.PENDING,
        )

        if db_sess is None:
            async with get_db_session() as db_sess:
                await self._persist(notification, channel_configs, db_sess)
                await db_sess.commit()
        else:
            await self._persist(notification, channel_configs, db_sess)

        self._logger.info(
            f"Enqueued notification '{notification.id}' of type '{type.value}' for user '{recipient}'"
        )

    async def _persist(
        self,
        notification: Notification,
        channel_configs: list[NotificationChannelConfig],
        db_sess: AsyncSession,
    ) -> None:
        db_sess.add(notification)
        await db_sess.flush()
        await db_sess.refresh(notification)

        for ch_configs in channel_configs:
            channel = NotificationChannel(
                notification_id=notification.id,
                type=ch_configs.type,
                max_retries=ch_configs.max_retries,
                expires_at=ch_configs.expires_at,
            )
            db_sess.add(channel)
