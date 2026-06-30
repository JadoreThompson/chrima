import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.notification import NotificationPublisher
from chrima.notification.channel.enums import NotificationChannelType
from chrima.notification.enums import NotificationType
from chrima.notification.schema import (
    SubscriptionExpiredNotificationContext,
    SubscriptionExpiringNotificationContext,
)
from chrima.product.service import ProductService
from chrima.workspace.service import WorkspaceService
from core.db import get_db_session
from util import get_datetime
from ..enums import SubscriptionStatus
from ..model import SubscriptionBalance

NOTIFICATION_COOLDOWN = 6 * 3600
EXPIRY_WINDOW = 12 * 3600
MAX_ATTEMPTS = 2


class SubscriptionExpiryChecker:

    def __init__(
        self,
        product_service: ProductService,
        workspace_service: WorkspaceService,
        notification_publisher: NotificationPublisher,
        interval: int = 3600,
    ):
        self._product_service = product_service
        self._workspace_service = workspace_service
        self._notification_publisher = notification_publisher
        self._interval = interval
        self._logger = logging.getLogger("subscription_expiry_checker")

    async def run(self):
        self._logger.info(
            "Starting subscription expiry checker (interval=%ss)", self._interval
        )

        while True:
            try:
                await self._check_expirations()
                await asyncio.sleep(self._interval)
            except Exception:
                self._logger.exception("Error in expiry check cycle")
                await asyncio.sleep(self._interval)

    async def _check_expirations(self):
        now = int(get_datetime().timestamp())
        in_12h = now + EXPIRY_WINDOW

        async with get_db_session() as db_sess:
            rows = await db_sess.execute(
                select(SubscriptionBalance).where(
                    SubscriptionBalance.cycle_end.isnot(None),
                    SubscriptionBalance.attempt_count < MAX_ATTEMPTS,
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
                            <= now - NOTIFICATION_COOLDOWN
                        )
                    ),
                )
            )

            for balance in rows.scalars().all():
                await self._process_expiry(balance, now, db_sess)

    async def _process_expiry(
        self, balance: SubscriptionBalance, now: int, db_sess: AsyncSession
    ):
        try:
            product = await self._product_service.get_product_by_id(
                balance.product_id, db_sess
            )
        except Exception:
            self._logger.warning("Product %s not found, skipping", balance.product_id)
            return

        try:
            workspace = await self._workspace_service.get_workspace(
                product.workspace_id, db_sess
            )
        except Exception:
            self._logger.warning(
                "Workspace for product %s not found, skipping", balance.product_id
            )
            return

        is_expired = balance.cycle_end < now

        ctx_data = {
            "guild_id": workspace.external_id,
            "channel_id": workspace.notification_channel_id,
            "platform_user_id": balance.platform_user_id,
            "product_id": str(balance.product_id),
            "product_name": product.name,
            "cycle_end": balance.cycle_end,
        }

        if is_expired:
            context = SubscriptionExpiredNotificationContext(**ctx_data)
            notif_type = NotificationType.SUBSCRIPTION_EXPIRED
        else:
            context = SubscriptionExpiringNotificationContext(**ctx_data)
            notif_type = NotificationType.SUBSCRIPTION_EXPIRING

        await self._notification_publisher.publish(
            user_id=balance.platform_user_id,
            type=notif_type,
            context=context,
            channel_types=[NotificationChannelType.DISCORD, NotificationChannelType.EMAIL],
        )

        balance.attempt_count += 1
        balance.last_notified_at = now

        await db_sess.flush()
