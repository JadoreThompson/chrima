import logging
from uuid import UUID

from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.event_bus.publisher import EventPublisher
from chrima.notification import NotificationPublisher
from chrima.notification.channel import NotificationChannelType
from chrima.notification.enums import NotificationType
from chrima.notification.schema import (
    BillingSubscriptionActivatedNotificationContext,
    BillingSubscriptionCancelledNotificationContext,
    NotificationChannelConfig,
)
from chrima.user import UserService
from chrima.user.enums import Tier
from config import REDIS_CHECKOUT_SESSION_PREFIX
from ..enums import BillingProvider as BillingProviderEnum, BillingStatus
from ..event import (
    BillingSubscriptionActivatedEvent,
    BillingSubscriptionCancelledEvent,
)
from ..exception import (
    BillingAlreadyCancelledException,
    BillingNotFoundException,
)
from ..model import Billing
from ..provider import BillingProvider
from ..schema import BillingResponse, CreateCheckoutSessionResponse


class BillingService:
    def __init__(
        self,
        *,
        billing_provider: BillingProvider,
        user_service: UserService,
        event_publisher: EventPublisher,
        notification_publisher: NotificationPublisher,
        redis_client: AsyncRedis,
    ):
        self._billing_provider = billing_provider
        self._user_service = user_service
        self._event_publisher = event_publisher
        self._notification_publisher = notification_publisher
        self._redis_client = redis_client
        self._logger = logging.getLogger(self.__class__.__name__)

    async def create_checkout_session(
        self, user_id: UUID, tier: Tier, db_sess: AsyncSession
    ) -> CreateCheckoutSessionResponse:
        if tier == Tier.FREE:
            raise ValueError("Cannot create a checkout session for the free tier")

        user = await self._user_service.get_by_id(user_id, db_sess)
        checkout = await self._billing_provider.create_checkout_session(
            tier, metadata={"user_id": str(user.id)}
        )
        await self._redis_client.set(
            f"{REDIS_CHECKOUT_SESSION_PREFIX}{checkout.id}", str(user_id)
        )
        return CreateCheckoutSessionResponse(url=checkout.url)

    async def cancel_subscription(
        self, user_id: UUID, db_sess: AsyncSession
    ) -> BillingResponse:
        billing = await self._get_billing_by_user(user_id, db_sess)
        if billing is None:
            raise BillingNotFoundException(user_id)
        if billing.status == BillingStatus.CANCELLED:
            raise BillingAlreadyCancelledException(billing.subscription_id)

        await self._billing_provider.cancel_subscription(billing.subscription_id)
        await self._mark_cancelled(billing, db_sess)
        await self._publish_cancelled(billing, db_sess)
        await self._notify_cancelled(billing, db_sess)
        return self._to_response(billing)

    async def activate_subscription(
        self,
        *,
        user_id: UUID,
        subscription_id: str,
        customer_id: str,
        billing_provider: BillingProviderEnum,
        db_sess: AsyncSession,
    ) -> BillingResponse:
        billing = await self._get_billing_by_user(user_id, db_sess)
        if billing is None:
            billing = Billing(
                user_id=user_id,
                subscription_id=subscription_id,
                billing_provider=billing_provider,
                customer_id=customer_id,
                status=BillingStatus.ACTIVE,
            )
            db_sess.add(billing)
        else:
            billing.subscription_id = subscription_id
            billing.customer_id = customer_id
            billing.billing_provider = billing_provider
            billing.status = BillingStatus.ACTIVE
        await db_sess.flush()
        await db_sess.refresh(billing)

        await self._user_service.set_tier(user_id, Tier.PRO, db_sess)
        await self._publish_activated(billing, db_sess)
        await self._notify_activated(billing, db_sess)
        return self._to_response(billing)

    async def cancel_subscription_webhook(
        self, subscription_id: str, db_sess: AsyncSession
    ) -> BillingResponse | None:
        billing = await self._get_billing_by_subscription(subscription_id, db_sess)
        if billing is None:
            self._logger.warning(
                "Received cancellation webhook for unknown subscription '%s'",
                subscription_id,
            )
            return None

        if billing.status == BillingStatus.CANCELLED:
            return self._to_response(billing)

        await self._mark_cancelled(billing, db_sess)
        await self._publish_cancelled(billing, db_sess)
        await self._notify_cancelled(billing, db_sess)
        return self._to_response(billing)

    async def get_billing(
        self, user_id: UUID, db_sess: AsyncSession
    ) -> BillingResponse:
        billing = await self._get_billing_by_user(user_id, db_sess)
        if billing is None:
            raise BillingNotFoundException(user_id)
        return self._to_response(billing)

    async def _get_billing_by_user(
        self, user_id: UUID, db_sess: AsyncSession
    ) -> Billing | None:
        return await db_sess.scalar(select(Billing).where(Billing.user_id == user_id))

    async def _get_billing_by_subscription(
        self, subscription_id: str, db_sess: AsyncSession
    ) -> Billing | None:
        return await db_sess.scalar(
            select(Billing).where(Billing.subscription_id == subscription_id)
        )

    async def _mark_cancelled(self, billing: Billing, db_sess: AsyncSession) -> None:
        billing.status = BillingStatus.CANCELLED
        await db_sess.flush()
        await self._user_service.set_tier(billing.user_id, Tier.FREE, db_sess)

    async def _publish_activated(self, billing: Billing, db_sess: AsyncSession) -> None:
        await self._event_publisher.publish(
            BillingSubscriptionActivatedEvent(
                user_id=billing.user_id,
                customer_id=billing.customer_id,
                subscription_id=billing.subscription_id,
                billing_provider=billing.billing_provider,
                tier=Tier.PRO,
            ),
            db_sess=db_sess,
        )

    async def _publish_cancelled(self, billing: Billing, db_sess: AsyncSession) -> None:
        await self._event_publisher.publish(
            BillingSubscriptionCancelledEvent(
                user_id=billing.user_id,
                subscription_id=billing.subscription_id,
                billing_provider=billing.billing_provider,
            ),
            db_sess=db_sess,
        )

    async def _notify_activated(self, billing: Billing, db_sess: AsyncSession) -> None:
        user = await self._user_service.get_by_id(billing.user_id, db_sess)
        await self._notification_publisher.publish(
            recipient=user.email,
            type=NotificationType.BILLING_SUBSCRIPTION_ACTIVATED,
            context=BillingSubscriptionActivatedNotificationContext(
                user_id=str(user.id),
                username=user.username,
                email=user.email,
                tier=Tier.PRO.value,
                billing_provider=BillingProviderEnum(billing.billing_provider).value,
                subscription_id=billing.subscription_id,
            ),
            channel_configs=[
                NotificationChannelConfig(type=NotificationChannelType.EMAIL),
            ],
            db_sess=db_sess,
        )

    async def _notify_cancelled(self, billing: Billing, db_sess: AsyncSession) -> None:
        user = await self._user_service.get_by_id(billing.user_id, db_sess)
        await self._notification_publisher.publish(
            recipient=user.email,
            type=NotificationType.BILLING_SUBSCRIPTION_CANCELLED,
            context=BillingSubscriptionCancelledNotificationContext(
                user_id=str(user.id),
                username=user.username,
                email=user.email,
                tier=Tier.FREE.value,
            ),
            channel_configs=[
                NotificationChannelConfig(type=NotificationChannelType.EMAIL),
            ],
            db_sess=db_sess,
        )

    def _to_response(self, billing: Billing) -> BillingResponse:
        return BillingResponse(
            id=billing.id,
            user_id=billing.user_id,
            subscription_id=billing.subscription_id,
            billing_provider=billing.billing_provider,
            customer_id=billing.customer_id,
            status=billing.status,
            created_at=billing.created_at,
            updated_at=billing.updated_at,
        )
