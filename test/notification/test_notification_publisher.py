import uuid

import pytest
from sqlalchemy import select

from chrima.notification.channel import NotificationChannelType
from chrima.notification.enums import NotificationStatus, NotificationType
from chrima.notification.model import Notification, NotificationChannel
from chrima.notification.schema import (
    NotificationChannelConfig,
    SubscriptionSufficientNotificationContext,
)
from chrima.notification.service.publisher import NotificationPublisher
from core.db import get_db_session


@pytest.fixture
def publisher():
    return NotificationPublisher()


@pytest.fixture
def sample_context():
    return SubscriptionSufficientNotificationContext(
        guild_id="guild_1",
        channel_id="ch_1",
        platform_user_id="usr_1",
        product_id=uuid.uuid4(),
        product_name="test-product",
        product_price=10.0,
        currency="USD",
        remaining_amount=10.0,
        transaction_id=uuid.uuid4(),
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_publishes_with_provided_session(
    publisher, sample_context, create_drop_tables
):
    """Verify that publish creates a Notification and NotificationChannel records
    when an explicit db_sess is provided."""
    async with get_db_session() as db_sess:
        await publisher.publish(
            recipient="usr_1",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sample_context,
            channel_configs=[
                NotificationChannelConfig(type=NotificationChannelType.DISCORD)
            ],
            db_sess=db_sess,
        )

        notification = await db_sess.scalar(
            select(Notification).where(Notification.recipient == "usr_1")
        )
        assert notification is not None
        assert notification.recipient == "usr_1"
        assert notification.type == NotificationType.SUBSCRIPTION_SUFFICIENT
        assert notification.context["product_name"] == "test-product"
        assert notification.status == NotificationStatus.PENDING

        channels = (
            (
                await db_sess.execute(
                    select(NotificationChannel).where(
                        NotificationChannel.notification_id == notification.id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(channels) == 1
        assert channels[0].type == NotificationChannelType.DISCORD
        assert channels[0].max_retries == 3
        assert channels[0].expires_at is None


@pytest.mark.asyncio(loop_scope="session")
async def test_publishes_without_session(publisher, sample_context, create_drop_tables):
    """Verify that publish creates records when no db_sess is provided
    (publisher creates its own internal session)."""
    await publisher.publish(
        recipient="usr_2",
        type=NotificationType.SUBSCRIPTION_SUFFICIENT,
        context=sample_context,
        channel_configs=[
            NotificationChannelConfig(type=NotificationChannelType.DISCORD)
        ],
    )

    async with get_db_session() as db_sess:
        notification = await db_sess.scalar(
            select(Notification).where(Notification.recipient == "usr_2")
        )
        assert notification is not None
        assert notification.recipient == "usr_2"


@pytest.mark.asyncio(loop_scope="session")
async def test_publishes_multiple_channels(
    publisher, sample_context, create_drop_tables
):
    """Verify that multiple channel configs create a NotificationChannel row
    for each."""
    async with get_db_session() as db_sess:
        await publisher.publish(
            recipient="usr_3",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sample_context,
            channel_configs=[
                NotificationChannelConfig(type=NotificationChannelType.DISCORD),
                NotificationChannelConfig(
                    type=NotificationChannelType.EMAIL, max_retries=5
                ),
            ],
            db_sess=db_sess,
        )

        notification = await db_sess.scalar(
            select(Notification).where(Notification.recipient == "usr_3")
        )
        channels = (
            (
                await db_sess.execute(
                    select(NotificationChannel).where(
                        NotificationChannel.notification_id == notification.id
                    )
                )
            )
            .scalars()
            .all()
        )

        assert len(channels) == 2
        assert {ch.type for ch in channels} == {
            NotificationChannelType.DISCORD,
            NotificationChannelType.EMAIL,
        }

        discord_ch = None
        for ch in channels:
            if ch.type == NotificationChannelType.DISCORD:
                discord_ch = ch

        assert discord_ch is not None
        assert discord_ch.max_retries == 3

        email_ch = None
        for ch in channels:
            if ch.type == NotificationChannelType.EMAIL:
                email_ch = ch

        assert email_ch is not None
        assert email_ch.max_retries == 5


@pytest.mark.asyncio(loop_scope="session")
async def test_publishes_with_expires_at(publisher, sample_context, create_drop_tables):
    """Verify that expires_at is persisted on the channel record when provided."""
    async with get_db_session() as db_sess:
        await publisher.publish(
            recipient="usr_4",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sample_context,
            channel_configs=[
                NotificationChannelConfig(
                    type=NotificationChannelType.DISCORD,
                    expires_at=1_800_000_000,
                )
            ],
            db_sess=db_sess,
        )

        notification = await db_sess.scalar(
            select(Notification).where(Notification.recipient == "usr_4")
        )
        channel = await db_sess.scalar(
            select(NotificationChannel).where(
                NotificationChannel.notification_id == notification.id
            )
        )
        assert channel.expires_at == 1_800_000_000


@pytest.mark.asyncio(loop_scope="session")
async def test_publishes_different_type(publisher, sample_context, create_drop_tables):
    """Verify that the notification type is correctly persisted for a type
    other than SUBSCRIPTION_SUFFICIENT."""
    async with get_db_session() as db_sess:
        await publisher.publish(
            recipient="usr_5",
            type=NotificationType.SUBSCRIPTION_EXPIRED,
            context=sample_context,
            channel_configs=[
                NotificationChannelConfig(type=NotificationChannelType.EMAIL)
            ],
            db_sess=db_sess,
        )

        notification = await db_sess.scalar(
            select(Notification).where(Notification.recipient == "usr_5")
        )
        assert notification.type == NotificationType.SUBSCRIPTION_EXPIRED


@pytest.mark.asyncio(loop_scope="session")
async def test_context_is_json(publisher, sample_context, create_drop_tables):
    """Verify that the context stored in the database is a JSON-serialised dict
    with the expected keys."""
    async with get_db_session() as db_sess:
        await publisher.publish(
            recipient="usr_6",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sample_context,
            channel_configs=[
                NotificationChannelConfig(type=NotificationChannelType.DISCORD)
            ],
            db_sess=db_sess,
        )

        notification = await db_sess.scalar(
            select(Notification).where(Notification.recipient == "usr_6")
        )
        assert isinstance(notification.context, dict)
        assert notification.context["product_name"] == "test-product"
        assert notification.context["product_price"] == 10.0
        assert notification.context["currency"] == "USD"
