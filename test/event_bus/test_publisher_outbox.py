from enum import Enum

import pytest
from sqlalchemy import select

from chrima.event_bus.enums import EventStatus
from chrima.event_bus.model import EventOutbox
from chrima.event_bus.publisher import OutboxEventPublisher
from infra.db import smaker
from core.event import BaseEvent


class _TestEventType(str, Enum):
    TEST_EVENT = "test.event"


class _TestEvent(BaseEvent):
    topic: str = "test.topic"
    type: _TestEventType = _TestEventType.TEST_EVENT
    user_id: str = ""
    amount: int = 0


@pytest.fixture
def publisher():
    return OutboxEventPublisher()


@pytest.mark.asyncio(loop_scope="session")
async def test_persists_event_with_session(publisher, create_drop_tables):
    event = _TestEvent(user_id="usr_123", amount=100)

    async with smaker.begin() as db_sess:
        await publisher.publish(event, db_sess=db_sess)

    async with smaker.begin() as db_sess:
        row = await db_sess.get(EventOutbox, event.id)

    assert row is not None
    assert row.id == event.id
    assert row.type == "test.event"
    assert row.status == EventStatus.PENDING
    assert row.payload["user_id"] == "usr_123"
    assert row.payload["amount"] == 100
    assert row.payload["type"] == "test.event"
    assert row.payload["id"] == str(event.id)
    assert row.timestamp == event.timestamp


@pytest.mark.asyncio(loop_scope="session")
async def test_persists_custom_timestamp(publisher, create_drop_tables):
    event = _TestEvent(user_id="usr_456", amount=250, timestamp=1234567890)

    async with smaker.begin() as db_sess:
        await publisher.publish(event, db_sess=db_sess)

    async with smaker.begin() as db_sess:
        row = await db_sess.get(EventOutbox, event.id)

    assert row.timestamp == 1234567890
    assert row.payload["user_id"] == "usr_456"
    assert row.payload["amount"] == 250


@pytest.mark.asyncio(loop_scope="session")
async def test_payload_contains_all_fields(publisher, create_drop_tables):
    event = _TestEvent(user_id="usr_789", amount=50)

    async with smaker.begin() as db_sess:
        await publisher.publish(event, db_sess=db_sess)

    async with smaker.begin() as db_sess:
        row = await db_sess.get(EventOutbox, event.id)

    payload = row.payload
    assert payload["user_id"] == "usr_789"
    assert payload["amount"] == 50
    assert payload["type"] == "test.event"
    assert payload["id"] == str(event.id)
    assert "timestamp" in payload


@pytest.mark.asyncio(loop_scope="session")
async def test_commits_when_no_session(publisher, create_drop_tables):
    event = _TestEvent(user_id="usr_auto", amount=999)
    await publisher.publish(event)

    async with smaker.begin() as db_sess:
        row = await db_sess.get(EventOutbox, event.id)

    assert row is not None
    assert row.status == EventStatus.PENDING
    assert row.payload["user_id"] == "usr_auto"


@pytest.mark.asyncio(loop_scope="session")
async def test_publishes_multiple_events(publisher, create_drop_tables):
    event_a = _TestEvent(user_id="usr_a", amount=1)
    event_b = _TestEvent(user_id="usr_b", amount=2)

    async with smaker.begin() as db_sess:
        await publisher.publish(event_a, db_sess=db_sess)
        await publisher.publish(event_b, db_sess=db_sess)

    async with smaker.begin() as db_sess:
        rows = (
            (
                await db_sess.execute(
                    select(EventOutbox).where(
                        EventOutbox.id.in_([event_a.id, event_b.id])
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(rows) == 2
    ids = {r.id for r in rows}
    assert event_a.id in ids
    assert event_b.id in ids
