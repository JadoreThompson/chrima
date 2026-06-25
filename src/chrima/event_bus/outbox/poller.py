import asyncio
import json
import logging
from typing import Type
from uuid import UUID

from sqlalchemy import case, select, update

from core.db import get_db_session
from core.event import BaseEvent, EventDeserialiser
from core.kafka import AsyncKafkaProducer
from ..enums import EventStatus
from ..model import EventOutbox


class OutboxPoller:
    """
    Periodically publishes events pending within the outbox.
    """

    def __init__(
        self,
        kafka_producer: AsyncKafkaProducer,
        deserialisers: dict[Type, EventDeserialiser],
        interval: int,
        batch_size: int,
        timeout: int = 5,
    ):
        self.interval = interval
        self.batch_size = batch_size
        self.timeout = timeout
        self._kafka_producer = kafka_producer
        self._deserialisers = deserialisers

        self._logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        self._logger.info(
            "Starting outbox poller (interval=%ss, batch_size=%s)",
            self.interval,
            self.batch_size,
        )

        while True:
            try:
                await asyncio.sleep(self.interval)

                events = await self._fetch_events()

                if not events:
                    self._logger.info("No pending outbox events found")
                    continue

                self._logger.info("Processing %s outbox events", len(events))

                results = await asyncio.gather(
                    *[self._emit_event(record.id, record.payload) for record in events],
                    return_exceptions=True,
                )

                updates: list[tuple[UUID, EventStatus]] = []

                success_count = 0
                failed_count = 0

                for result in results:
                    if isinstance(result, Exception):
                        failed_count += 1

                        self._logger.exception(
                            "Unhandled exception while processing outbox batch",
                            exc_info=result,
                        )

                        continue

                    event_id, success = result

                    status = EventStatus.COMPLETED if success else EventStatus.FAILED

                    updates.append((event_id, status))

                    if success:
                        success_count += 1
                    else:
                        failed_count += 1

                if updates:
                    await self._update_events(updates)

                self._logger.info(
                    (
                        "Completed outbox batch "
                        "(processed=%s, succeeded=%s, failed=%s)"
                    ),
                    len(updates),
                    success_count,
                    failed_count,
                )

            except Exception as e:
                self._logger.exception(
                    "Unexpected error in outbox poller loop", exc_info=e
                )

    async def _fetch_events(self):
        self._logger.info(
            "Fetching pending outbox events (batch_size=%s)", self.batch_size
        )

        async with get_db_session() as db_sess:
            res = await db_sess.execute(
                select(EventOutbox)
                .where(
                    EventOutbox.status.in_(
                        [
                            EventStatus.PENDING,
                            EventStatus.FAILED,
                        ]
                    )
                )
                .order_by(EventOutbox.timestamp.asc())
                .limit(self.batch_size)
            )

            events = res.scalars().all()

            self._logger.info("Fetched %s outbox events", len(events))

            return events

    async def _emit_event(self, outbox_id: UUID, raw_event: dict) -> tuple[UUID, bool]:
        try:
            event = self._parse_event(raw_event)

            self._logger.info(
                "Publishing event " "(outbox_id=%s, event_id=%s, type=%s)",
                outbox_id,
                event.id,
                event.type,
            )

            await asyncio.wait_for(
                self._kafka_producer.send_and_wait(
                    event.topic,
                    json.dumps(raw_event).encode(),
                    headers=self._build_headers(event),
                ),
                timeout=30,
            )

            self._logger.info(
                "Successfully published event " "(outbox_id=%s, event_id=%s, type=%s)",
                outbox_id,
                event.id,
                event.type,
            )

            return outbox_id, True
        except Exception:
            self._logger.warning(
                "Failed to publish outbox event " "(outbox_id=%s, raw_type=%s)",
                outbox_id,
                raw_event.get("type"),
                exc_info=True,
            )

            return outbox_id, False

    async def _update_events(
        self,
        event_id_status: list[tuple[UUID, EventStatus]],
    ):
        """
        Bulk update statuses in a single query.
        """
        if not event_id_status:
            return

        self._logger.info("Updating %s outbox event statuses", len(event_id_status))

        ids = [event_id for event_id, _ in event_id_status]

        stmt = (
            update(EventOutbox)
            .where(EventOutbox.id.in_(ids))
            .values(
                status=case(
                    *[
                        (EventOutbox.id == event_id, status)
                        for event_id, status in event_id_status
                    ],
                    else_=EventOutbox.status,
                )
            )
        )

        async with get_db_session() as db_sess:
            await db_sess.execute(stmt)
            await db_sess.commit()

        completed = sum(
            1 for _, status in event_id_status if status == EventStatus.COMPLETED
        )
        failed = sum(1 for _, status in event_id_status if status == EventStatus.FAILED)

        self._logger.info(
            "Updated outbox statuses (completed=%s, failed=%s)", completed, failed
        )

    def _parse_event(self, raw_event: dict) -> BaseEvent:
        cls = self.__class__

        event_type: str = raw_event["type"]

        self._logger.info(
            "Parsing event type '%s'",
            event_type,
        )

    def _build_headers(self, event: BaseEvent) -> list[tuple[str, bytes]]:
        headers = [("event_type", event.type.value.encode())]
        return headers
