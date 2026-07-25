from typing import Type, TypeVar
from uuid import UUID

import discord

from config import LOGO_URL
from util import get_datetime
from chrima.price.enums import PriceType
from chrima.price.schema import PriceResponse
from chrima.product.schema import ProductResponse
from chrima.subscription.schema import SubscriptionBalanceResponse
from chrima.subscription.enums import SubscriptionStatus
from .base import NotificationTemplateEngine
from .exception import NotificationTemplateEngineException
from ..enums import NotificationType
from ..schema import (
    Notification,
    OneTimePurchaseNotificationContext,
    SubscriptionExpiredNotificationContext,
    SubscriptionExpiringNotificationContext,
    SubscriptionRenewedNotificationContext,
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
        if notification_type == NotificationType.SUBSCRIPTION_RENEWED:
            return self._render_subscription_renewed(notification)
        if notification_type == NotificationType.ONE_TIME_PURCHASE:
            return self._render_one_time_purchase(notification)

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
            remaining_amount=ctx.remaining_amount,
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

    def _render_subscription_renewed(
        self, notification: Notification
    ) -> discord.Embed:
        ctx = self._validate_ctx(notification, SubscriptionRenewedNotificationContext)
        embed = discord.Embed(
            title="Subscription Renewed",
            description=(
                f"<@{ctx.platform_user_id}>, your subscription "
                f"for **{ctx.product_name}** has been renewed."
            ),
            color=discord.Color.green(),
            timestamp=get_datetime(),
        )
        embed.set_author(name="Chrima")
        embed.set_thumbnail(url=LOGO_URL)
        embed.add_field(name="Product", value=ctx.product_name, inline=True)
        embed.add_field(
            name="Price",
            value=f"{ctx.product_price:.2f} {ctx.currency.upper()}",
            inline=True,
        )
        return embed

    def _render_one_time_purchase(
        self, notification: Notification
    ) -> discord.Embed:
        ctx = self._validate_ctx(notification, OneTimePurchaseNotificationContext)
        embed = discord.Embed(
            title="Purchase Complete",
            description=(
                f"<@{ctx.platform_user_id}> purchased "
                f"**{ctx.product_name}** "
                f"for **{ctx.product_price:.2f} {ctx.currency.upper()}**."
            ),
            color=discord.Color.green(),
            timestamp=get_datetime(),
        )
        embed.set_author(name="Chrima")
        embed.set_thumbnail(url=LOGO_URL)
        embed.add_field(name="Product", value=ctx.product_name, inline=True)
        embed.add_field(
            name="Price",
            value=f"{ctx.product_price:.2f} {ctx.currency.upper()}",
            inline=True,
        )
        return embed

    def render_subscription_list(
        self, subscriptions: list[SubscriptionBalanceResponse], user_id: int
    ) -> discord.Embed:
        if not subscriptions:
            return discord.Embed(
                title="You currently have no subscriptions",
                color=discord.Color.blue(),
                timestamp=get_datetime(),
            )

        lines = []
        for sub in subscriptions:
            status_emoji = {
                SubscriptionStatus.ACTIVE: "\u2705",
                SubscriptionStatus.EXPIRED: "\u274c",
                SubscriptionStatus.CANCELLED: "\u26a0\ufe0f",
                SubscriptionStatus.INCOMPLETE: "\u26a0\ufe0f",
            }.get(sub.status, "\u2753")

            parts = [f"{status_emoji} `{sub.product_id}`"]
            if sub.cycle_end:
                parts.append(f"expires <t:{sub.cycle_end}:R>")
            if sub.credit_amount > 0:
                parts.append(f"${sub.credit_amount:.2f}")

            lines.append(" \u2022 ".join(parts))

        embed = discord.Embed(
            title="Your Subscriptions",
            description=(
                f"<@{user_id}>, here are your subscriptions in this server.\n\n"
                + "\n".join(lines)
            ),
            color=discord.Color.blue(),
            timestamp=get_datetime(),
        )
        embed.set_author(name="Chrima")
        embed.set_thumbnail(url=LOGO_URL)
        return embed

    def render_product_list(
        self, products_with_prices: list[tuple[ProductResponse, list[PriceResponse]]]
    ) -> discord.Embed:
        if not products_with_prices:
            return discord.Embed(
                title="No Products",
                description="This server has no products yet.",
                color=discord.Color.blue(),
                timestamp=get_datetime(),
            )

        embed = discord.Embed(
            title="Server Products",
            color=discord.Color.blue(),
            timestamp=get_datetime(),
        )
        embed.set_author(name="Chrima")
        embed.set_thumbnail(url=LOGO_URL)

        for product, prices in products_with_prices:
            desc = product.description or ""
            if len(desc) > 100:
                desc = desc[:97] + "..."

            price_lines = []
            for p in prices:
                amount = f"${p.amount:.2f}"
                if p.type == PriceType.RECURRING and p.recurring_interval:
                    interval = p.recurring_interval.value
                    price_lines.append(f"{amount} / {interval}")
                else:
                    price_lines.append(amount)

            value_parts = []
            if desc:
                value_parts.append(desc)
            if price_lines:
                value_parts.append("**" + "\n".join(price_lines) + "**")
            value_parts.append(f"`{product.id}`")

            embed.add_field(
                name=product.name,
                value="\n".join(value_parts),
                inline=False,
            )

        return embed

    def render_cancel_result(
        self,
        cancelled: list[SubscriptionBalanceResponse],
        user_id: int,
        product_id: UUID,
    ) -> discord.Embed:
        if not cancelled:
            if product_id:
                desc = f"<@{user_id}>, you don't have an active subscription for `{product_id}`."
            else:
                desc = f"<@{user_id}>, you don't have any active subscriptions to cancel."
            return discord.Embed(
                title="Nothing to Cancel",
                description=desc,
                color=discord.Color.blue(),
                timestamp=get_datetime(),
            )

        product_ids = "\n".join(f"`{s.product_id}`" for s in cancelled)
        embed = discord.Embed(
            title="Subscription Cancelled",
            description=f"<@{user_id}>, the following subscriptions have been cancelled.\n\n{product_ids}",
            color=discord.Color.green(),
            timestamp=get_datetime(),
        )
        embed.set_author(name="Chrima")
        embed.set_thumbnail(url=LOGO_URL)
        return embed
