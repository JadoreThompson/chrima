import asyncio
import logging

import click

from chrima.event_bus.service.outbox import OutboxPoller
from chrima.price.event import PriceEventDeserialiser
from chrima.product.event import ProductEventDeserialiser
from chrima.subscription.event import SubscriptionEventDeserialiser
from chrima.transaction.event import TransactionEventDeserialiser
from infra.kafka import AsyncKafkaProducer

logger = logging.getLogger("outbox_cli")


async def _run_outbox(interval: int, batch_size: int, timeout: int) -> None:
    deserialisers = {
        "price": PriceEventDeserialiser(),
        "product": ProductEventDeserialiser(),
        "subscription": SubscriptionEventDeserialiser(),
        "transaction": TransactionEventDeserialiser(),
    }
    kafka_producer = AsyncKafkaProducer.create()
    poller = OutboxPoller(
        kafka_producer=kafka_producer,
        deserialisers=deserialisers,
        interval=interval,
        batch_size=batch_size,
        timeout=timeout,
    )

    try:
        await kafka_producer.start()
        await poller.run()
    finally:
        await kafka_producer.stop()


@click.group("event-bus")
def event_bus():
    pass


@event_bus.group("outbox")
def outbox():
    pass


@outbox.command(name="run")
@click.option("--interval", required=True, type=int, help="Polling interval in seconds")
@click.option("--batch-size", required=True, type=int, help="Batch size per poll cycle")
@click.option(
    "--timeout",
    default=5,
    type=int,
    help="Timeout in seconds for each Kafka publish",
)
def outbox_run(interval: int, batch_size: int, timeout: int) -> None:
    asyncio.run(_run_outbox(interval, batch_size, timeout))
