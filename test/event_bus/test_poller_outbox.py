import asyncio
import json
from enum import Enum
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chrima.event_bus.enums import EventStatus
from chrima.event_bus.model import EventOutbox
from chrima.event_bus.service.outbox.poller import OutboxPoller
from infra.db import get_db_session
from core.event import BaseEvent, EventDeserialiser
from util import get_datetime


class _TestEventType(str, Enum):
    TEST = "test.event"


class _TestEvent(BaseEvent):
    topic: str = "test.topic"
    type: _TestEventType = _TestEventType.TEST


class _TestDeserialiser(EventDeserialiser[_TestEvent]):
    def deserialise_json(self, value: str | bytes) -> _TestEvent:
        import json

        return _TestEvent(**json.loads(value))

    def deserialise(self, value: dict) -> _TestEvent:
        return _TestEvent(**value)


@pytest.fixture
def kafka_producer():
    return AsyncMock()


@pytest.fixture
def poller(kafka_producer):
    return OutboxPoller(
        kafka_producer=kafka_producer,
        deserialisers={"test": _TestDeserialiser()},
        interval=0.05,
        batch_size=10,
    )


def _make_event(**kw):
    now = int(get_datetime().timestamp())
    event_id = uuid4()
    defaults = dict(
        id=event_id,
        type="test.event",
        payload={
            "id": str(event_id),
            "type": "test.event",
            "timestamp": now,
        },
        status=EventStatus.PENDING,
        timestamp=now,
    )
    defaults.update(kw)
    return EventOutbox(**defaults)


async def _run_one_cycle(poller):
    try:
        await asyncio.wait_for(
            poller.run(), timeout=(poller.interval + poller.timeout) * 2.5
        )
    except asyncio.TimeoutError:
        pass


@pytest.mark.asyncio(loop_scope="session")
async def test_pending_to_completed(kafka_producer, poller, create_drop_tables):
    e = _make_event()

    async with get_db_session() as db_sess:
        db_sess.add(e)
        await db_sess.commit()

    await poller.perform()

    async with get_db_session() as db_sess:
        row = await db_sess.get(EventOutbox, e.id)

    assert row.status == EventStatus.COMPLETED
    kafka_producer.send_and_wait.assert_called_once()


@pytest.mark.asyncio(loop_scope="session")
async def test_publishes_event_id_in_payload(
    kafka_producer, poller, create_drop_tables
):
    e = _make_event()
    async with get_db_session() as db_sess:
        db_sess.add(e)

    await poller.perform()

    sent_payload = kafka_producer.send_and_wait.call_args[0][1]
    import json

    parsed = json.loads(sent_payload)
    assert parsed["id"] == str(e.id)
    assert parsed["type"] == "test.event"


@pytest.mark.asyncio(loop_scope="session")
async def test_publishes_to_correct_topic(kafka_producer, poller, create_drop_tables):
    e = _make_event()
    async with get_db_session() as db_sess:
        db_sess.add(e)

    await poller.perform()

    topic = kafka_producer.send_and_wait.call_args[0][0]
    assert topic == "test.topic"


@pytest.mark.asyncio(loop_scope="session")
async def test_multiple_events_all_published(
    kafka_producer, poller, create_drop_tables
):
    events = [_make_event() for _ in range(3)]

    async with get_db_session() as db_sess:
        db_sess.add_all(events)
        await db_sess.commit()

    await poller.perform()

    assert kafka_producer.send_and_wait.call_count == 3

    sent_ids = set()

    for call in kafka_producer.send_and_wait.call_args_list:
        payload = json.loads(call[0][1])
        sent_ids.add(payload["id"])
        await db_sess.commit()

    expected_ids = {str(e.id) for e in events}
    assert sent_ids == expected_ids

    async with get_db_session() as db_sess:
        for e in events:
            row = await db_sess.get(EventOutbox, e.id)
            assert row.status == EventStatus.COMPLETED


@pytest.mark.asyncio(loop_scope="session")
async def test_skips_completed_publishes_pending(
    kafka_producer, poller, create_drop_tables
):
    pending = _make_event()
    completed = _make_event(status=EventStatus.COMPLETED)

    async with get_db_session() as db_sess:
        db_sess.add_all([pending, completed])
        await db_sess.commit()

    await poller.perform()

    assert kafka_producer.send_and_wait.call_count == 1

    sent_payload = json.loads(kafka_producer.send_and_wait.call_args[0][1])
    assert sent_payload["id"] == str(pending.id)
    assert sent_payload["id"] != str(completed.id)

    async with get_db_session() as db_sess:
        assert (
            await db_sess.get(EventOutbox, pending.id)
        ).status == EventStatus.COMPLETED
        assert (
            await db_sess.get(EventOutbox, completed.id)
        ).status == EventStatus.COMPLETED


@pytest.mark.asyncio(loop_scope="session")
async def test_failed_reprocessed_and_published(
    kafka_producer, poller, create_drop_tables
):
    e = _make_event(status=EventStatus.FAILED)
    async with get_db_session() as db_sess:
        db_sess.add(e)
        await db_sess.commit()

    await poller.perform()

    assert kafka_producer.send_and_wait.call_count == 1

    sent_payload = json.loads(kafka_producer.send_and_wait.call_args[0][1])
    assert sent_payload["id"] == str(e.id)

    async with get_db_session() as db_sess:
        row = await db_sess.get(EventOutbox, e.id)

    assert row.status == EventStatus.COMPLETED


@pytest.mark.asyncio(loop_scope="session")
async def test_unknown_domain_not_published(kafka_producer, poller, create_drop_tables):
    e = _make_event(type="unknown.event", payload={"type": "unknown.event"})

    async with get_db_session() as db_sess:
        db_sess.add(e)
        await db_sess.commit()

    await poller.perform()

    kafka_producer.send_and_wait.assert_not_called()
    async with get_db_session() as db_sess:
        row = await db_sess.get(EventOutbox, e.id)

    assert row.status == EventStatus.FAILED
