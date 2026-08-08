from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponse, ClientResponseError, ClientSession

from chrima.email.brevo import BrevoEmailService


def _make_response(status: int = 201) -> AsyncMock:
    response = AsyncMock(spec=ClientResponse)
    response.status = status
    response.__aenter__.return_value = response
    response.__aexit__.return_value = False
    if status >= 400:
        response.raise_for_status.side_effect = ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=status,
            message="error",
        )
    return response


def _make_session(response: AsyncMock | None = None) -> AsyncMock:
    session = AsyncMock(spec=ClientSession)
    session.closed = False
    if response is not None:
        session.post.return_value = response
    return session


@pytest.mark.asyncio(loop_scope="session")
class TestSend:

    async def test_send_posts_transactional_email(self):
        """Sends a transactional email to Brevo with sender, recipient,
        subject and plain-text body."""
        response = _make_response()
        session = _make_session(response)

        service = BrevoEmailService(
            name="Chrima",
            email_address="no-reply@chrima.dev",
            api_key="test-api-key",
            session=session,
        )

        await service.send("user@example.com", "Subject", "Body")
        await service.close()

        session.post.assert_called_once_with(
            "https://api.brevo.com/v3/smtp/email",
            json={
                "sender": {"name": "Chrima", "email": "no-reply@chrima.dev"},
                "to": [{"email": "user@example.com"}],
                "subject": "Subject",
                "textContent": "Body",
            },
        )

    async def test_non_2xx_response_raises(self):
        """An error response from Brevo raises ClientResponseError."""
        response = _make_response(status=400)
        session = _make_session(response)

        service = BrevoEmailService(
            name="Chrima",
            email_address="no-reply@chrima.dev",
            api_key="test-api-key",
            session=session,
        )

        try:
            with pytest.raises(ClientResponseError):
                await service.send("user@example.com", "Subject", "Body")
        finally:
            await service.close()

    async def test_creates_session_with_api_key_header(self):
        """When no session is injected, one is created with the Brevo api-key
        header and the send still succeeds through it."""
        session = _make_session(_make_response())

        with patch(
            "chrima.email.brevo.ClientSession", return_value=session
        ) as mock_session_cls:
            service = BrevoEmailService(
                name="Chrima",
                email_address="no-reply@chrima.dev",
                api_key="test-api-key",
            )

            try:
                await service.send("user@example.com", "Subject", "Body")
            finally:
                await service.close()

        mock_session_cls.assert_called_once_with(
            headers={
                "api-key": "test-api-key",
                "accept": "application/json",
            }
        )
        session.post.assert_called_once()


@pytest.mark.asyncio(loop_scope="session")
class TestClose:

    async def test_close_closes_session(self):
        """close closes the underlying aiohttp session."""
        session = _make_session()

        service = BrevoEmailService(
            name="Chrima",
            email_address="no-reply@chrima.dev",
            api_key="test-api-key",
            session=session,
        )

        await service.close()

        session.close.assert_awaited_once()
