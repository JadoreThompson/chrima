import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.notification import NotificationPublisher
from chrima.notification.channel import NotificationChannelType
from chrima.notification.enums import NotificationType
from chrima.notification.schema import (
    SubscriptionExpiredNotificationContext,
    SubscriptionExpiringNotificationContext,
)
from chrima.product import ProductService
from chrima.product.exception import ProductNotFoundException
from chrima.workspace import WorkspaceService
from chrima.workspace.exception import WorkspaceNotFoundException
from infra.db import get_db_session
from chrima.monitoring import trace_class
from util import get_datetime
from ..enums import SubscriptionStatus
from ..model import SubscriptionBalance


@trace_class()
class SubscriptionExpiryChecker:
    def __init__(
        self,
        *,
        product_service: ProductService,
        workspace_service: WorkspaceService,
        notification_publisher: NotificationPublisher,
        interval: int = 3600,
        notification_cooldown: int = 6 * 3600,
        expiry_window: int = 12 * 3600,
        max_attempts: int = 2,
    ):
        self._product_service = product_service
        self._workspace_service = workspace_service
        self._notification_publisher = notification_publisher
        self.interval = interval
        self.notification_cooldown = notification_cooldown
        self.expiry_window = expiry_window
        self.max_attempts = max_attempts
        self._logger = logging.getLogger("subscription_expiry_checker")

    async def run(self):
        self._logger.info(
            "Starting subscription expiry checker (interval=%ss)", self.interval
        )

        while True:
            try:
                await self.check_expirations()
                await asyncio.sleep(self.interval)
            except Exception:
                self._logger.exception("Error in expiry check cycle")
                await asyncio.sleep(self.interval)

    async def check_expirations(self):
        now = int(get_datetime().timestamp())
        in_12h = now + self.expiry_window

        async with get_db_session() as db_sess:
            rows = await db_sess.execute(
                select(SubscriptionBalance).where(
                    SubscriptionBalance.cycle_end.isnot(None),
                    SubscriptionBalance.attempt_count < self.max_attempts,
                    (
                        (SubscriptionBalance.cycle_end <= in_12h)
                        & (SubscriptionBalance.cycle_end >= now)
                        & (SubscriptionBalance.status == SubscriptionStatus.ACTIVE)
                    )
                    | (
                        (SubscriptionBalance.cycle_end < now)
                        & (SubscriptionBalance.status != SubscriptionStatus.CANCELLED)
                    ),
                    (
                        SubscriptionBalance.last_notified_at.is_(None)
                        | (
                            SubscriptionBalance.last_notified_at
                            <= now - self.notification_cooldown
                        )
                    ),
                )
            )

            for balance in rows.scalars().all():
                await self._process_expiry(balance, now, db_sess)

            await db_sess.commit()

    async def _process_expiry(
        self, balance: SubscriptionBalance, now: int, db_sess: AsyncSession
    ):
        try:
            product = await self._product_service.get_by_id(balance.product_id, db_sess)
        except ProductNotFoundException:
            self._logger.warning("Product %s not found, skipping", balance.product_id)
            return

        try:
            workspace = await self._workspace_service.get_by_id(
                product.workspace_id, db_sess
            )
        except WorkspaceNotFoundException:
            self._logger.warning(
                "Workspace for product %s not found, skipping", balance.product_id
            )
            return

        is_expired = balance.cycle_end < now

        ctx_data = {
            "guild_id": workspace.external_id,
            "channel_id": workspace.notification_channel_id,
            "platform_user_id": balance.platform_user_id,
            "product_id": balance.product_id,
            "product_name": product.name,
            "cycle_end": balance.cycle_end,
        }

        if is_expired:
            context = SubscriptionExpiredNotificationContext(**ctx_data)
            notif_type = NotificationType.SUBSCRIPTION_EXPIRED
            balance.status = SubscriptionStatus.EXPIRED
        else:
            context = SubscriptionExpiringNotificationContext(**ctx_data)
            notif_type = NotificationType.SUBSCRIPTION_EXPIRING

        await self._notification_publisher.publish(
            user_id=balance.platform_user_id,
            type=notif_type,
            context=context,
            channel_types=[
                NotificationChannelType.DISCORD,
                NotificationChannelType.EMAIL,
            ],
        )

        balance.attempt_count += 1
        balance.last_notified_at = now

        db_sess.add(balance)
        await db_sess.flush()
