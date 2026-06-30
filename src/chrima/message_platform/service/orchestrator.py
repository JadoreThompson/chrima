import logging

from sqlalchemy.ext.asyncio import AsyncSession

from chrima.workspace import WorkspaceService
from chrima.notification import NotificationPublisher
from chrima.notification.channel.enums import NotificationChannelType
from chrima.notification.enums import NotificationType
from chrima.notification.schema import (
    SubscriptionIncompleteNotificationContext,
    SubscriptionNowSufficientNotificationContext,
    SubscriptionSufficientNotificationContext,
)
from chrima.price import PriceService
from chrima.product import ProductService
from chrima.product.enums import FulfilmentType
from chrima.product.schema import ProductResponse
from chrima.subscription import SubscriptionBalanceService
from chrima.subscription.exception import SubscriptionBalanceNotFoundException
from chrima.subscription.enums import SubscriptionStatus
from chrima.transaction.event import (
    TransactionEventType,
    TransactionCompletedEvent,
    TransactionCompletedEventV2,
    TransactionEventDeserialiser,
)
from config import KAKFA_TRANSACTION_EVENTS_TOPIC
from core.db import get_db_session
from core.kafka import AsyncKafkaConsumer
from .discord import DiscordService


class MessagePlatformOrchestrator:
    def __init__(
        self,
        discord_service: DiscordService,
        product_service: ProductService,
        price_service: PriceService,
        workspace_service: WorkspaceService,
        subscription_balance_service: SubscriptionBalanceService,
        deserialiser: TransactionEventDeserialiser,
        notification_service: NotificationPublisher,
    ):
        self._discord_service = discord_service
        self._product_service = product_service
        self._price_service = price_service
        self._workspace_service = workspace_service
        self._subscription_balance_service = subscription_balance_service
        self._deserialiser = deserialiser
        self._notification_service = notification_service
        self._kafka_consumer: AsyncKafkaConsumer | None = None
        self._logger = logging.getLogger("message_platform_orchestrator")

    async def run(self):
        self._kafka_consumer = AsyncKafkaConsumer.create(
            KAKFA_TRANSACTION_EVENTS_TOPIC,
            group_id="message_platform_orchestrator_group",
            enable_auto_commit=False,
        )

        try:
            await self._kafka_consumer.start()
            self._logger.info("Started listening for transaction events")

            async for msg in self._kafka_consumer:
                event = self._deserialiser.deserialise_json(msg.value)
                event_type = event.type

                async with get_db_session() as db_sess:
                    if event_type == TransactionEventType.COMPLETED:
                        await self._handle_transaction_completed(event, db_sess)

                await self._kafka_consumer.commit()
        finally:
            await self.close()

    async def _handle_transaction_completed(
        self, event: TransactionCompletedEventV2, db_sess: AsyncSession
    ) -> None:
        product = await self._product_service.get_product_by_id(
            event.product_id, db_sess
        )
        price = await self._price_service.get_price_by_id(product.price_id, db_sess)
        workspace = await self._workspace_service.get_workspace(
            product.workspace_id, db_sess
        )

        try:
            balance = await self._subscription_balance_service.get_balance(
                product.group_id, event.group_user_id, product.id, db_sess
            )
        except SubscriptionBalanceNotFoundException:
            balance = await self._subscription_balance_service.create(
                external_id=product.group_id,
                platform_user_id=event.group_user_id,
                product_id=product.id,
                credit_amount=0.0,
                status=SubscriptionStatus.INCOMPLETE,
                db_sess=db_sess,
            )

        was_sufficient = balance.credit_amount >= price.amount

        balance = await self._subscription_balance_service.increase_balance(
            external_id=product.group_id,
            platform_user_id=event.group_user_id,
            product_id=product.id,
            amount=event.amount,
            transaction_id=event.transaction_id,
            db_sess=db_sess,
        )

        now_sufficient = balance.credit_amount >= price.amount

        common = dict(
            guild_id=product.group_id,
            channel_id=workspace.notification_channel,
            platform_user_id=event.group_user_id,
            product_id=str(product.id),
            product_name=product.name,
            product_price=price.amount,
            currency=price.currency,
            remaining_amount=balance.credit_amount,
            transaction_id=event.transaction_id,
        )

        if was_sufficient:
            await self._subscription_balance_service.process_cycle(
                external_id=product.group_id,
                platform_user_id=event.group_user_id,
                product_id=product.id,
                amount=price.amount,
                recurring_interval=price.recurring_interval,
                recurring_interval_count=price.recurring_interval_count,
                transaction_id=event.transaction_id,
                db_sess=db_sess,
            )
            await self._notification_service.publish(
                user_id=event.group_user_id,
                type=NotificationType.SUBSCRIPTION_SUFFICIENT,
                context=SubscriptionSufficientNotificationContext(**common),
                channel_types=[NotificationChannelType.DISCORD, NotificationChannelType.EMAIL],
            )
            await self._handle_discord(product, event)
        elif now_sufficient:
            await self._subscription_balance_service.process_cycle(
                external_id=product.group_id,
                platform_user_id=event.group_user_id,
                product_id=product.id,
                amount=price.amount,
                recurring_interval=price.recurring_interval,
                recurring_interval_count=price.recurring_interval_count,
                transaction_id=event.transaction_id,
                db_sess=db_sess,
            )
            await self._notification_service.publish(
                user_id=event.group_user_id,
                type=NotificationType.SUBSCRIPTION_NOW_SUFFICIENT,
                context=SubscriptionNowSufficientNotificationContext(**common),
                channel_types=[NotificationChannelType.DISCORD, NotificationChannelType.EMAIL],
            )
            await self._handle_discord(product, event)
        else:
            await self._notification_service.publish(
                user_id=event.group_user_id,
                type=NotificationType.SUBSCRIPTION_INCOMPLETE,
                context=SubscriptionIncompleteNotificationContext(**common),
                channel_types=[NotificationChannelType.DISCORD, NotificationChannelType.EMAIL],
            )

    async def _handle_discord(
        self, product: ProductResponse, event: TransactionCompletedEvent
    ) -> None:
        access_type = product.fulfilment_type
        guild_id = int(product.group_id)
        user_id = int(event.group_user_id)
        roles = product.roles

        if access_type == FulfilmentType.INVITE:
            await self._discord_service.invite_user(
                group_url=product.external_url,
                user_id=event.group_user_id,
            )
        elif access_type == FulfilmentType.ROLE:
            await self._discord_service.assign_roles(
                guild_id=guild_id,
                user_id=user_id,
                roles=roles,
            )

    async def close(self):
        if self._kafka_consumer is not None:
            await self._kafka_consumer.stop()
            self._kafka_consumer = None
