from .types import EmailTemplate
from ..base import NotificationTemplateEngine
from ....schema import Notification


class EmailNotificationTemplateEngine(NotificationTemplateEngine):
    def render(self, notification: Notification) -> EmailTemplate:
        return 
