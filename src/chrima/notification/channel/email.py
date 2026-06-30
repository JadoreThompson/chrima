from chrima.email import EmailService
from .base import NotificationChannel
from ..schema import Notification
from ..template.engine import EmailNotificationTemplateEngine


class EmailNotificationChannel(NotificationChannel):
    def __init__(
        self,
        email_service: EmailService,
        template_engine: EmailNotificationTemplateEngine,
    ):
        super().__init__()
        self.email_service = email_service
        self.template_engine = template_engine

    async def send(self, notification: Notification) -> None:
        template = self.template_engine.render(notification)
        await self.email_service.send(notification.recipient, template.subject, template.body)
