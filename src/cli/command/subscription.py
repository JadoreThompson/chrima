import asyncio
import logging

import click

from chrima.event_bus.publisher import OutboxEventPublisher
from chrima.notification.service.publisher import NotificationPublisher
from chrima.price import PriceService
from chrima.product import ProductService
from chrima.subscription.service.expiry_checker import SubscriptionExpiryChecker
from chrima.workspace import WorkspaceService

logger = logging.getLogger("expiry_checker_cli")


async def _run_expiry_checker(
    interval: int,
    notification_cooldown: int,
    expiry_window: int,
    max_attempts: int,
) -> None:
    event_publisher = OutboxEventPublisher()
    workspace_service = WorkspaceService()
    price_service = PriceService(event_publisher=event_publisher)
    product_service = ProductService(event_publisher=event_publisher)
    notification_publisher = NotificationPublisher()

    checker = SubscriptionExpiryChecker(
        product_service=product_service,
        workspace_service=workspace_service,
        notification_publisher=notification_publisher,
        interval=interval,
        notification_cooldown=notification_cooldown,
        expiry_window=expiry_window,
        max_attempts=max_attempts,
    )

    await checker.run()


@click.group("subscription")
def subscription():
    pass


@subscription.group("expiry-checker")
def expiry_checker():
    pass


@expiry_checker.command(name="run")
@click.option(
    "--interval",
    default=3600,
    type=int,
    help="Check interval in seconds",
)
@click.option(
    "--notification-cooldown",
    default=21600,
    type=int,
    help="Notification cooldown in seconds",
)
@click.option(
    "--expiry-window",
    default=43200,
    type=int,
    help="Expiry window in seconds",
)
@click.option(
    "--max-attempts",
    default=2,
    type=int,
    help="Max notification attempts per balance",
)
def expiry_checker_run(
    interval: int,
    notification_cooldown: int,
    expiry_window: int,
    max_attempts: int,
) -> None:
    asyncio.run(
        _run_expiry_checker(
            interval, notification_cooldown, expiry_window, max_attempts
        )
    )
