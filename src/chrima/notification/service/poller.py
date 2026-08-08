import asyncio
import logging
from uuid import UUID

from sqlalchemy import and_, case, or_, select, tuple_, update
from sqlalchemy.orm import selectinload

from chrima.monitoring import trace_class
from infra.db import get_db_session
from util import get_datetime
from ..channel import NotificationChannel, NotificationChannelType
from ..enums import NotificationStatus, NotificationType
from ..model import Notification, NotificationChannel as NotificationChannelModel
from ..schema import (
    Notification as NotificationSchema,
    NotificationContextUnion,
    BillingSubscriptionActivatedNotificationContext,
    BillingSubscriptionCancelledNotificationContext,
    SubscriptionExpiredNotificationContext,
    SubscriptionExpiringNotificationContext,
    SubscriptionSufficientNotificationContext,
)


@trace_class()
class NotificationPoller:
    def __init__(
        self,
        notification_channels: dict[NotificationChannelType, NotificationChannel],
        *,
        interval: int = 5,
        batch_size: int = 100,
        timeout: int = 5,
    ) -> None:
        self._notification_channels = notification_channels
        self.interval = interval
        self.batch_size = batch_size
        self.timeout = timeout
        self._logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        self._logger.info(
            "Starting notification poller (interval=%ss, batch_size=%s)",
            self.interval,
            self.batch_size,
        )

        while True:
            try:
                # records = await self._fetch_events()

                # if not records:
                #     continue

                # self._logger.info("Processing %s notifications", len(records))

                # results = await asyncio.gather(
                #     *[self._emit_notification(record) for record in records],
                #     return_exceptions=True,
                # )

                # updates: list[tuple[UUID, NotificationStatus]] = []
                # success_count = 0
                # failed_count = 0

                # for result in results:
                #     if isinstance(result, Exception):
                #         self._logger.exception(
                #             "Unhandled exception while processing notification batch",
                #             exc_info=result,
                #         )
                #         failed_count += 1
                #         continue

                #     event_id, channel_type, success = result
                #     status = (
                #         NotificationStatus.COMPLETED
                #         if success
                #         else NotificationStatus.FAILED
                #     )
                #     updates.append((event_id, channel_type, status))

                #     if success:
                #         success_count += 1
                #     else:
                #         failed_count += 1

                # if updates:
                #     await self._update_events(updates)

                success_count, failed_count = await self.perform()

                self._logger.info(
                    "Completed notification batch "
                    "(processed=%s, succeeded=%s, failed=%s)",
                    # len(updates),
                    success_count + failed_count,
                    success_count,
                    failed_count,
                )

            except Exception as e:
                self._logger.exception(
                    "Unexpected error in notification poller loop", exc_info=e
                )

            await asyncio.sleep(self.interval)

    async def perform(self) -> tuple[int, int]:
        records = await self._fetch_events()

        if not records:
            return 0, 0

        self._logger.info("Processing %s notifications", len(records))

        results = await asyncio.gather(
            *[self._emit_notification(record) for record in records],
            return_exceptions=True,
        )

        updates: list[tuple[UUID, NotificationChannelType, NotificationStatus]] = []
        success_count = 0
        failed_count = 0

        for result in results:
            if isinstance(result, BaseException):
                self._logger.exception(
                    "Unhandled exception while processing notification batch",
                    exc_info=result,
                )
                failed_count += 1
                continue

            event_id, channel_type, success = result
            status = (
                NotificationStatus.COMPLETED if success else NotificationStatus.FAILED
            )
            updates.append((event_id, channel_type, status))

            if success:
                success_count += 1
            else:
                failed_count += 1

        if updates:
            await self._update_events(updates)

        return success_count, failed_count

    async def _fetch_events(self) -> list[NotificationChannelModel]:
        self._logger.info(
            "Fetching pending notifications (batch_size=%s)", self.batch_size
        )

        now = int(get_datetime().timestamp())

        async with get_db_session() as db_sess:
            res = await db_sess.execute(
                select(NotificationChannelModel)
                .options(selectinload(NotificationChannelModel.notification))
                .join(
                    Notification,
                    Notification.id == NotificationChannelModel.notification_id,
                )
                .where(
                    NotificationChannelModel.status.in_(
                        [
                            NotificationStatus.PENDING,
                            NotificationStatus.FAILED,
                        ]
                    ),
                    or_(
                        NotificationChannelModel.expires_at.is_(None),
                        NotificationChannelModel.expires_at < now,
                    ),
                    NotificationChannelModel.retries
                    < NotificationChannelModel.max_retries,
                )
                .order_by(Notification.created_at.asc())
                .limit(self.batch_size)
            )

            records = res.scalars().all()
            self._logger.info("Fetched %s notifications", len(records))
            return records

    async def _emit_notification(
        self, record: NotificationChannelModel
    ) -> tuple[UUID, NotificationChannelType, bool]:
        try:
            notification = self._build_notification(record.notification)

            channel_type = NotificationChannelType(record.type)
            channel = self._notification_channels.get(channel_type)
            if channel is None:
                self._logger.warning(
                    "No channel found for type '%s' (notification_id=%s)",
                    channel_type,
                    record.notification_id,
                )
                return record.notification_id, record.type, False

            await asyncio.wait_for(channel.send(notification), timeout=self.timeout)

            self._logger.info(
                "Successfully sent notification (id=%s, type=%s, channel=%s)",
                record.notification_id,
                record.notification.type,
                record.type,
            )

            return record.notification_id, record.type, True

        except Exception:
            self._logger.warning(
                "Failed to send notification (id=%s, type=%s)",
                record.notification_id,
                record.type,
                exc_info=True,
            )
            return record.notification_id, record.type, False

    async def _update_events(
        self,
        updates: list[tuple[UUID, NotificationChannelType, NotificationStatus]],
    ) -> None:
        if not updates:
            return

        now = int(get_datetime().timestamp())

        keys = [
            (notification_id, channel_type)
            for notification_id, channel_type, _ in updates
        ]

        stmt = (
            update(NotificationChannelModel)
            .where(
                tuple_(
                    NotificationChannelModel.notification_id,
                    NotificationChannelModel.type,
                ).in_(keys)
            )
            .values(
                status=case(
                    *[
                        (
                            and_(
                                NotificationChannelModel.notification_id
                                == notification_id,
                                NotificationChannelModel.type == channel_type,
                            ),
                            status,
                        )
                        for notification_id, channel_type, status in updates
                    ],
                    else_=NotificationChannelModel.status,
                ),
                retries=NotificationChannelModel.retries + 1,
                last_attempted_at=now,
            )
        )

        async with get_db_session() as db_sess:
            await db_sess.execute(stmt)
            await db_sess.commit()

    def _build_notification(self, record: Notification) -> NotificationSchema:
        context = self._parse_context(record.type, record.context)
        return NotificationSchema(
            recipient=record.recipient,
            type=NotificationType(record.type),
            context=context,
        )

    def _parse_context(
        self, notification_type: str, context_data: dict
    ) -> NotificationContextUnion:
        notification_type_enum = NotificationType(notification_type)

        if notification_type_enum == NotificationType.SUBSCRIPTION_SUFFICIENT:
            return SubscriptionSufficientNotificationContext.model_validate(
                context_data
            )
        if notification_type_enum == NotificationType.SUBSCRIPTION_EXPIRING:
            return SubscriptionExpiringNotificationContext.model_validate(context_data)
        if notification_type_enum == NotificationType.SUBSCRIPTION_EXPIRED:
            return SubscriptionExpiredNotificationContext.model_validate(context_data)
        if notification_type_enum == NotificationType.BILLING_SUBSCRIPTION_ACTIVATED:
            return BillingSubscriptionActivatedNotificationContext.model_validate(
                context_data
            )
        if notification_type_enum == NotificationType.BILLING_SUBSCRIPTION_CANCELLED:
            return BillingSubscriptionCancelledNotificationContext.model_validate(
                context_data
            )

        raise ValueError(f"Unknown notification type: {notification_type}")
