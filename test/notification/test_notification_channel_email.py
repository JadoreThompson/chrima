from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from chrima.email import EmailService
from chrima.notification.channel.email import EmailNotificationChannel
from chrima.notification.enums import NotificationType
from chrima.notification.schema import (
    Notification,
    SubscriptionSufficientNotificationContext,
)
from chrima.notification.template.engine import EmailNotificationTemplateEngine
from chrima.notification.template.engine.email.types import EmailTemplate


@pytest.fixture
def mock_email_service():
    return AsyncMock(spec=EmailService)


@pytest.fixture
def mock_template_engine():
    return MagicMock(spec=EmailNotificationTemplateEngine)


@pytest.fixture
def channel(mock_email_service, mock_template_engine):
    return EmailNotificationChannel(
        email_service=mock_email_service,
        template_engine=mock_template_engine,
    )


@pytest.fixture
def sample_template():
    return EmailTemplate(subject="Test Subject", body="Test Body")


@pytest.fixture
def sufficient_context():
    return SubscriptionSufficientNotificationContext(
        guild_id="guild_1",
        channel_id="ch_1",
        platform_user_id="usr_1",
        product_id=uuid4(),
        product_name="test-product",
        product_price=10.0,
        currency="USD",
        remaining_amount=10.0,
        transaction_id=uuid4(),
    )


@pytest.mark.asyncio(loop_scope="session")
class TestUnit:

    async def test_send_success(
        self, channel, mock_email_service, mock_template_engine, sample_template, sufficient_context
    ):
        """A valid notification renders the email template and sends via
        email_service with the correct recipient, subject, and body."""
        mock_template_engine.render.return_value = sample_template

        notification = Notification(
            recipient="user@example.com",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sufficient_context,
        )

        await channel.send(notification)

        mock_template_engine.render.assert_called_once_with(notification)
        mock_email_service.send.assert_called_once_with(
            "user@example.com", "Test Subject", "Test Body"
        )

    async def test_send_raises_on_template_error(
        self, channel, mock_email_service, mock_template_engine, sufficient_context
    ):
        """When the template engine raises, the exception propagates and
        email_service.send is not called."""
        mock_template_engine.render.side_effect = ValueError("bad template")

        notification = Notification(
            recipient="user@example.com",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sufficient_context,
        )

        with pytest.raises(ValueError, match="bad template"):
            await channel.send(notification)

        mock_template_engine.render.assert_called_once_with(notification)
        mock_email_service.send.assert_not_called()

    async def test_send_raises_on_email_error(
        self, channel, mock_email_service, mock_template_engine, sample_template, sufficient_context
    ):
        """When the email service raises, the exception propagates. The
        template was rendered successfully before the failure, so render
        is verified as called."""
        mock_template_engine.render.return_value = sample_template
        mock_email_service.send.side_effect = RuntimeError("smtp error")

        notification = Notification(
            recipient="user@example.com",
            type=NotificationType.SUBSCRIPTION_SUFFICIENT,
            context=sufficient_context,
        )

        with pytest.raises(RuntimeError, match="smtp error"):
            await channel.send(notification)

        mock_template_engine.render.assert_called_once_with(notification)
        mock_email_service.send.assert_called_once_with(
            "user@example.com", "Test Subject", "Test Body"
        )
