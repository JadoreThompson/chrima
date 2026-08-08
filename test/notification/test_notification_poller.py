import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from chrima.notification.channel import NotificationChannel, NotificationChannelType
from chrima.notification.enums import NotificationStatus, NotificationType
from chrima.notification.model import (
    Notification,
    NotificationChannel as NotificationChannelModel,
)
from chrima.notification.service.poller import NotificationPoller
from infra.db import get_db_session
from util import get_datetime


@pytest.fixture
def mock_discord_channel():
    mock = AsyncMock(spec=NotificationChannel)
    mock.send = AsyncMock()
    return mock


@pytest.fixture
def mock_email_channel():
    mock = AsyncMock(spec=NotificationChannel)
    mock.send = AsyncMock()
    return mock


@pytest.fixture
def poller(mock_discord_channel, mock_email_channel):
    return NotificationPoller(
        notification_channels={
            NotificationChannelType.DISCORD: mock_discord_channel,
            NotificationChannelType.EMAIL: mock_email_channel,
        },
        interval=0.05,
        batch_size=10,
        timeout=5,
    )


async def _create_notification(
    db_sess,
    recipient="usr_1",
    type=NotificationType.SUBSCRIPTION_SUFFICIENT,
    context=None,
):
    if context is None:
        context = {
            "guild_id": "guild_1",
            "channel_id": "ch_1",
            "platform_user_id": "usr_1",
            "product_id": str(uuid4()),
            "product_name": "test-product",
            "product_price": 10.0,
            "currency": "USD",
            "remaining_amount": 10.0,
            "transaction_id": str(uuid4()),
        }
    notification = Notification(
        recipient=recipient,
        type=type.value,
        context=context,
        status=NotificationStatus.PENDING,
    )
    db_sess.add(notification)
    await db_sess.flush()
    await db_sess.refresh(notification)
    return notification


def _create_channel(
    db_sess,
    notification_id,
    type=NotificationChannelType.DISCORD,
    status=NotificationStatus.PENDING,
    retries=0,
    max_retries=3,
    expires_at=None,
):
    channel = NotificationChannelModel(
        notification_id=notification_id,
        type=type,
        status=status,
        retries=retries,
        max_retries=max_retries,
        expires_at=expires_at,
    )
    db_sess.add(channel)
    return channel


async def _run_one_cycle(poller):
    try:
        await asyncio.wait_for(
            poller.run(), timeout=(poller.interval + poller.timeout) * 2.5
        )
    except asyncio.TimeoutError:
        pass


@pytest.mark.asyncio(loop_scope="session")
async def test_processes_pending_discord(
    poller, mock_discord_channel, create_drop_tables
):
    """A single PENDING discord notification channel record is processed:
    send is called with the correct notification, status becomes COMPLETED,
    retries incremented, last_attempted_at set."""
    async with get_db_session() as db_sess:
        notification = await _create_notification(db_sess)
        _create_channel(db_sess, notification.id)
        await db_sess.commit()

    await poller.perform()

    assert mock_discord_channel.send.call_count == 1

    sent = mock_discord_channel.send.call_args[0][0]
    assert sent.recipient == "usr_1"
    assert sent.type == NotificationType.SUBSCRIPTION_SUFFICIENT

    async with get_db_session() as db_sess:
        row = await db_sess.scalar(
            select(NotificationChannelModel).where(
                NotificationChannelModel.notification_id == notification.id
            )
        )

    assert row.status == NotificationStatus.COMPLETED
    assert row.retries == 1
    assert row.last_attempted_at is not None


@pytest.mark.asyncio(loop_scope="session")
async def test_processes_pending_email(poller, mock_email_channel, create_drop_tables):
    """A single PENDING email notification channel record is processed."""
    async with get_db_session() as db_sess:
        notification = await _create_notification(db_sess)
        _create_channel(db_sess, notification.id, type=NotificationChannelType.EMAIL)
        await db_sess.commit()

    await poller.perform()

    assert mock_email_channel.send.call_count == 1
    assert mock_email_channel.send.call_args[0][0].recipient == "usr_1"


@pytest.mark.asyncio(loop_scope="session")
async def test_retries_failed_channel(poller, mock_discord_channel, create_drop_tables):
    """NotificationChannel with FAILED status and retries < max_retries
    is picked up and retried."""
    async with get_db_session() as db_sess:
        notification = await _create_notification(db_sess)
        _create_channel(
            db_sess, notification.id, status=NotificationStatus.FAILED, retries=1
        )
        await db_sess.commit()

    await poller.perform()

    assert mock_discord_channel.send.call_count == 1

    async with get_db_session() as db_sess:
        row = await db_sess.scalar(
            select(NotificationChannelModel).where(
                NotificationChannelModel.notification_id == notification.id
            )
        )
    assert row.status == NotificationStatus.COMPLETED
    assert row.retries == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_skips_when_max_retries_reached(
    poller, mock_discord_channel, create_drop_tables
):
    """A channel record with retries == max_retries is NOT processed."""
    async with get_db_session() as db_sess:
        notification = await _create_notification(db_sess)
        _create_channel(db_sess, notification.id, retries=5, max_retries=5)
        await db_sess.commit()

    await poller.perform()

    assert mock_discord_channel.send.call_count == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_skips_expired_channel(poller, mock_discord_channel, create_drop_tables):
    """A channel record with expires_at in the future is NOT processed
    (the poller skips records whose expiry has not yet been reached)."""
    now = int(get_datetime().timestamp())
    async with get_db_session() as db_sess:
        notification = await _create_notification(db_sess)
        _create_channel(db_sess, notification.id, expires_at=now + 3600)
        await db_sess.commit()

    await poller.perform()

    assert mock_discord_channel.send.call_count == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_processes_multiple_channels(
    poller, mock_discord_channel, mock_email_channel, create_drop_tables
):
    """Two channel records for the same notification are both processed."""
    async with get_db_session() as db_sess:
        notification = await _create_notification(db_sess)
        _create_channel(db_sess, notification.id, type=NotificationChannelType.DISCORD)
        _create_channel(db_sess, notification.id, type=NotificationChannelType.EMAIL)
        await db_sess.commit()

    await poller.perform()

    assert mock_discord_channel.send.call_count == 1
    assert mock_email_channel.send.call_count == 1

    async with get_db_session() as db_sess:
        rows = (
            (
                await db_sess.execute(
                    select(NotificationChannelModel).where(
                        NotificationChannelModel.notification_id == notification.id
                    )
                )
            )
            .scalars()
            .all()
        )

    for row in rows:
        assert row.status == NotificationStatus.COMPLETED
        assert row.retries == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_passed_context_is_deserialised(
    poller, mock_discord_channel, create_drop_tables
):
    """The context stored as JSON is deserialised back into the correct
    notification context object before being passed to channel.send."""
    context = {
        "guild_id": "guild_x",
        "channel_id": "ch_x",
        "platform_user_id": "usr_x",
        "product_id": str(uuid4()),
        "product_name": "premium-access",
        "product_price": 20.0,
        "currency": "EUR",
        "remaining_amount": 20.0,
        "transaction_id": str(uuid4()),
    }

    async with get_db_session() as db_sess:
        notification = await _create_notification(db_sess, context=context)
        _create_channel(db_sess, notification.id)
        await db_sess.commit()

    await poller.perform()

    sent = mock_discord_channel.send.call_args[0][0]
    assert sent.context.guild_id == "guild_x"
    assert sent.context.product_name == "premium-access"
    assert sent.context.product_price == 20.0


@pytest.mark.asyncio(loop_scope="session")
async def test_send_failure_updates_to_failed(
    poller, mock_discord_channel, create_drop_tables
):
    """When channel.send raises, the record status becomes FAILED and
    retries are incremented."""
    mock_discord_channel.send.side_effect = RuntimeError("channel error")

    async with get_db_session() as db_sess:
        notification = await _create_notification(db_sess)
        _create_channel(db_sess, notification.id)
        await db_sess.commit()

    await poller.perform()

    async with get_db_session() as db_sess:
        row = await db_sess.scalar(
            select(NotificationChannelModel).where(
                NotificationChannelModel.notification_id == notification.id
            )
        )
    assert row.status == NotificationStatus.FAILED
    assert 0 < row.retries <= row.max_retries
    assert row.last_attempted_at is not None
