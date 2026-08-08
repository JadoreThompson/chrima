import logging

from sqlalchemy.ext.asyncio import AsyncSession

from chrima.discord.exception import DiscordAccessTokenNotFoundException
from chrima.discord.service import DiscordService, DiscordMembershipService
from chrima.monitoring import trace_class
from chrima.notification import NotificationPublisher
from chrima.notification.channel import NotificationChannelType
from chrima.notification.enums import NotificationType
from chrima.notification.schema import (
    NotificationChannelConfig,
    OneTimePurchaseNotificationContext,
    SubscriptionRenewedNotificationContext,
    SubscriptionSufficientNotificationContext,
)
from chrima.price import PriceService
from chrima.price.enums import PriceType
from chrima.product import ProductService
from chrima.product.enums import FulfilmentType
from chrima.product.schema import ProductResponse
from chrima.transaction.event import (
    TransactionEventType,
    TransactionCompletedEvent,
    TransactionEventDeserialiser,
)
from chrima.workspace import WorkspaceService
from config import KAKFA_TRANSACTION_EVENTS_TOPIC
from infra.db import get_db_session
from infra.kafka import AsyncKafkaConsumer


@trace_class()
class TransactionOrchestrator:
    def __init__(
        self,
        *,
        discord_service: DiscordService,
        discord_membership_service: DiscordMembershipService,
        product_service: ProductService,
        price_service: PriceService,
        workspace_service: WorkspaceService,
        deserialiser: TransactionEventDeserialiser,
        notification_publisher: NotificationPublisher,
    ):
        self._discord_service = discord_service
        self._discord_membership_service = discord_membership_service
        self._product_service = product_service
        self._price_service = price_service
        self._workspace_service = workspace_service
        self._deserialiser = deserialiser
        self._notification_publisher = notification_publisher
        self._kafka_consumer: AsyncKafkaConsumer | None = None
        self._logger = logging.getLogger("transaction_orchestrator")

    async def run(self):
        self._kafka_consumer = AsyncKafkaConsumer.create(
            KAKFA_TRANSACTION_EVENTS_TOPIC,
            group_id="transaction_orchestrator_group",
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
                        await self.handle_transaction_completed(event, db_sess)

                await self._kafka_consumer.commit()
        finally:
            await self.close()

    async def handle_transaction_completed(
        self, event: TransactionCompletedEvent, db_sess: AsyncSession
    ) -> None:
        product = await self._product_service.get_by_id(event.product_id, db_sess)
        price = await self._price_service.get_by_id(event.price_id, db_sess)
        workspace = await self._workspace_service.get_by_id(
            product.workspace_id, db_sess
        )

        success = await self._handle_discord(int(workspace.external_id), product, event, db_sess)
        if not success:
            return

        await self._notification_publisher.publish(
            recipient=event.platform_user_id,
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=SubscriptionSufficientNotificationContext(
                guild_id=workspace.external_id,
                channel_id=workspace.notification_channel_id,
                platform_user_id=event.platform_user_id,
                product_id=str(product.id),
                product_name=product.name,
                product_price=price.amount,
                currency=price.currency,
                remaining_amount=price.amount,
                transaction_id=event.transaction_id,
            ),
            channel_configs=[
                NotificationChannelConfig(type=NotificationChannelType.DISCORD),
                NotificationChannelConfig(type=NotificationChannelType.EMAIL),
            ],
        )

        if price.type == PriceType.RECURRING:
            await self._notification_publisher.publish(
                recipient=event.platform_user_id,
                type=NotificationType.SUBSCRIPTION_RENEWED,
                context=SubscriptionRenewedNotificationContext(
                    guild_id=workspace.external_id,
                    channel_id=workspace.notification_channel_id,
                    platform_user_id=event.platform_user_id,
                    product_id=str(product.id),
                    product_name=product.name,
                    product_price=price.amount,
                    currency=price.currency,
                    transaction_id=event.transaction_id,
                ),
                channel_configs=[
                    NotificationChannelConfig(type=NotificationChannelType.DISCORD),
                    NotificationChannelConfig(type=NotificationChannelType.EMAIL),
                ],
            )
        elif price.type == PriceType.ONE_TIME:
            await self._notification_publisher.publish(
                recipient=event.platform_user_id,
                type=NotificationType.ONE_TIME_PURCHASE,
                context=OneTimePurchaseNotificationContext(
                    guild_id=workspace.external_id,
                    channel_id=workspace.notification_channel_id,
                    platform_user_id=event.platform_user_id,
                    product_id=str(product.id),
                    product_name=product.name,
                    product_price=price.amount,
                    currency=price.currency,
                    transaction_id=event.transaction_id,
                ),
                channel_configs=[
                    NotificationChannelConfig(type=NotificationChannelType.DISCORD),
                    NotificationChannelConfig(type=NotificationChannelType.EMAIL),
                ],
            )

    async def _handle_discord(
        self,
        guild_id: int,
        product: ProductResponse,
        event: TransactionCompletedEvent,
        db_sess: AsyncSession,
    ) -> bool:
        access_type = product.fulfilment_type
        user_id = int(event.platform_user_id)
        roles = [int(r) for r in product.roles] if product.roles else []

        try:
            if access_type == FulfilmentType.INVITE:
                access_token = await self._discord_service.get_access_token(
                    discord_user_id=user_id, db_sess=db_sess
                )
                await self._discord_membership_service.add_user_to_guild(
                    guild_id=guild_id,
                    user_id=user_id,
                    access_token=access_token,
                )
            elif access_type == FulfilmentType.ROLE:
                await self._discord_membership_service.assign_roles(
                    guild_id=guild_id,
                    user_id=user_id,
                    roles=roles,
                    db_sess=db_sess,
                )
        except DiscordAccessTokenNotFoundException as e:
            self._logger.error(str(e))
            return False
        
        return True

    async def close(self):
        if self._kafka_consumer is not None:
            await self._kafka_consumer.stop()
            self._kafka_consumer = None
