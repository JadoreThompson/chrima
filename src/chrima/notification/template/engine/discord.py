from typing import Type, TypeVar

import discord

from config import LOGO_URL
from util import get_datetime
from .base import NotificationTemplateEngine
from .exception import NotificationTemplateEngineException
from ...enums import NotificationType
from ...schema import (
    Notification,
    SubscriptionExpiredNotificationContext,
    SubscriptionExpiringNotificationContext,
    SubscriptionSufficientNotificationContext,
)

T = TypeVar("T")


class DiscordNotificationTemplateEngine(NotificationTemplateEngine):
    def render(self, notification: Notification) -> discord.Embed:
        notification_type = notification.type

        if notification_type == NotificationType.SUBSCRIPTION_SUFFICIENT:
            return self._render_subscription_sufficient(notification)
        if notification_type == NotificationType.SUBSCRIPTION_EXPIRING:
            return self._render_subscription_expiring(notification)
        if notification_type == NotificationType.SUBSCRIPTION_EXPIRED:
            return self._render_subscription_expired(notification)

        raise NotificationTemplateEngineException(
            f"Unknown notification type '{notification_type}'"
        )

    def _validate_ctx(self, notification: Notification, expected_type: Type[T]) -> T:
        if not isinstance(notification.context, expected_type):
            raise ValueError(
                f"Invalid notification context '{notification.context.__class__}' "
                f"expected '{expected_type.__name__}'"
            )
        return notification.context

    def _build_base_embed(
        self,
        *,
        title: str,
        description: str,
        color: discord.Color,
        product_name: str,
        product_price: float,
        currency: str,
        remaining_amount: float,
    ) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=get_datetime(),
        )
        embed.set_author(name="Chrima")
        embed.set_thumbnail(url=LOGO_URL)
        embed.add_field(
            name="Product",
            value=product_name,
            inline=True,
        )
        embed.add_field(
            name="Price",
            value=f"{product_price:.2f} {currency.upper()}",
            inline=True,
        )
        embed.add_field(
            name="Balance",
            value=f"{remaining_amount:.2f} {currency.upper()}",
            inline=False,
        )
        return embed

    def _render_subscription_sufficient(
        self, notification: Notification
    ) -> discord.Embed:
        ctx = self._validate_ctx(
            notification, SubscriptionSufficientNotificationContext
        )
        return self._build_base_embed(
            title="Subscription Covered",
            description=f"<@{ctx.platform_user_id}>, your subscription for **{ctx.product_name}** already has sufficient credits for this cycle.",
            color=discord.Color.green(),
            product_name=ctx.product_name,
            product_price=ctx.product_price,
            currency=ctx.currency,
            remaining_amount=ctx.remaining_amount
        )

    def _render_subscription_expiring(
        self, notification: Notification
    ) -> discord.Embed:
        ctx = self._validate_ctx(notification, SubscriptionExpiringNotificationContext)
        embed = discord.Embed(
            title="Subscription Expiring Soon",
            description=(
                f"<@{ctx.platform_user_id}>, your subscription "
                f"for **{ctx.product_name}** ends <t:{ctx.cycle_end}:R>."
            ),
            color=discord.Color.gold(),
            timestamp=get_datetime(),
        )
        embed.set_author(name="Chrima")
        embed.set_thumbnail(url=LOGO_URL)
        embed.add_field(name="Product", value=ctx.product_name, inline=True)
        embed.add_field(
            name="Expires",
            value=f"<t:{ctx.cycle_end}:F>",
            inline=True,
        )
        return embed

    def _render_subscription_expired(self, notification: Notification) -> discord.Embed:
        ctx = self._validate_ctx(notification, SubscriptionExpiredNotificationContext)
        embed = discord.Embed(
            title="Subscription Expired",
            description=(
                f"<@{ctx.platform_user_id}>, your subscription "
                f"for **{ctx.product_name}** has expired. "
                f"Renew to regain access."
            ),
            color=discord.Color.red(),
            timestamp=get_datetime(),
        )
        embed.set_author(name="Chrima")
        embed.set_thumbnail(url=LOGO_URL)
        embed.add_field(name="Product", value=ctx.product_name, inline=True)
        embed.add_field(
            name="Expired",
            value=f"<t:{ctx.cycle_end}:F>",
            inline=True,
        )
        return embed
