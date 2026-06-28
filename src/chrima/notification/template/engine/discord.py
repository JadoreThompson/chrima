import discord

from config import DOMAIN, LOGO_URL, SCHEME
from util import get_datetime

from .base import NotificationTemplateEngine
from .exception import NotificationTemplateEngineException
from ...enums import NotificationType
from ...schema import (
    Notification,
    NotificationContext,
    SubscriptionIncompleteNotificationContext,
    SubscriptionNowSufficientNotificationContext,
    SubscriptionSufficientNotificationContext,
)


class DiscordNotificationTemplateEngine(NotificationTemplateEngine):
    def render(self, notification: Notification) -> discord.Embed:
        notification_type = notification.type

        if notification_type == NotificationType.SUBSCRIPTION_INCOMPLETE:
            return self._render_subscription_incomplete(notification)
        if notification_type == NotificationType.SUBSCRIPTION_SUFFICIENT:
            return self._render_subscription_sufficient(notification)
        if notification_type == NotificationType.SUBSCRIPTION_NOW_SUFFICIENT:
            return self._render_subscription_now_sufficient(notification)

        raise NotificationTemplateEngineException(
            f"Unknown notification type '{notification_type}'"
        )

    def _validate_ctx(self, notification, expected_type):
        if not isinstance(notification.context, expected_type):
            raise ValueError(
                f"Invalid notification context '{notification.context.__class__}' "
                f"expected '{expected_type.__name__}'"
            )
        return notification.context

    def _build_base_embed(self, ctx, title, description, color):
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
            value=ctx.product_name,
            inline=True,
        )
        embed.add_field(
            name="Price",
            value=f"{ctx.product_price:.2f} {ctx.currency.upper()}",
            inline=True,
        )
        embed.add_field(
            name="Balance",
            value=f"{ctx.remaining_amount:.2f} {ctx.currency.upper()}",
            inline=False,
        )
        return embed

    def _render_subscription_incomplete(self, notification):
        ctx = self._validate_ctx(notification, SubscriptionIncompleteNotificationContext)
        embed = self._build_base_embed(
            ctx,
            title="Subscription Balance Low",
            description=f"<@{ctx.platform_user_id}>, your subscription for **{ctx.product_name}** is running low on credits.",
            color=discord.Color.orange(),
        )
        checkout_url = f"{SCHEME}://{DOMAIN}/checkout/{ctx.product_id}"
        embed.add_field(
            name="Checkout",
            value=f"[Top up your balance here]({checkout_url})",
            inline=False,
        )
        return embed

    def _render_subscription_sufficient(self, notification):
        ctx = self._validate_ctx(notification, SubscriptionSufficientNotificationContext)
        return self._build_base_embed(
            ctx,
            title="Subscription Covered",
            description=f"<@{ctx.platform_user_id}>, your subscription for **{ctx.product_name}** already has sufficient credits for this cycle.",
            color=discord.Color.green(),
        )

    def _render_subscription_now_sufficient(self, notification):
        ctx = self._validate_ctx(notification, SubscriptionNowSufficientNotificationContext)
        return self._build_base_embed(
            ctx,
            title="Subscription Now Covered",
            description=f"<@{ctx.platform_user_id}>, your subscription for **{ctx.product_name}** now has enough credits for this cycle.",
            color=discord.Color.green(),
        )
