from .types import EmailTemplate
from ..base import NotificationTemplateEngine
from ..exception import NotificationTemplateEngineException
from ....enums import NotificationType
from ....schema import Notification


class EmailNotificationTemplateEngine(NotificationTemplateEngine):
    def render(self, notification: Notification) -> EmailTemplate:
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

    def _render_subscription_sufficient(
        self, notification: Notification
    ) -> EmailTemplate:
        ctx = notification.context
        subject = "Subscription Covered"
        body = (
            f"Hi {ctx.platform_user_id},\n\n"
            f"Your subscription for {ctx.product_name} already has "
            f"sufficient credits for this cycle.\n\n"
            f"Product: {ctx.product_name}\n"
            f"Price: {ctx.product_price:.2f} {ctx.currency.upper()}\n"
            f"Remaining Balance: {ctx.remaining_amount:.2f} {ctx.currency.upper()}"
        )
        return EmailTemplate(subject=subject, body=body)

    def _render_subscription_expiring(
        self, notification: Notification
    ) -> EmailTemplate:
        ctx = notification.context
        subject = "Subscription Expiring Soon"
        body = (
            f"Hi {ctx.platform_user_id},\n\n"
            f"Your subscription for {ctx.product_name} "
            f"ends <t:{ctx.cycle_end}:F>.\n\n"
            f"Product: {ctx.product_name}"
        )
        return EmailTemplate(subject=subject, body=body)

    def _render_subscription_expired(self, notification: Notification) -> EmailTemplate:
        ctx = notification.context
        subject = "Subscription Expired"
        body = (
            f"Hi {ctx.platform_user_id},\n\n"
            f"Your subscription for {ctx.product_name} has expired.\n"
            f"Renew to regain access.\n\n"
            f"Product: {ctx.product_name}"
        )
        return EmailTemplate(subject=subject, body=body)
