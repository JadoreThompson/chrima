from aiohttp import ClientSession

from .base import EmailService


class BrevoEmailService(EmailService):
    BREVO_API_BASE_URL = "https://api.brevo.com/v3"

    def __init__(
        self,
        name: str,
        email_address: str,
        api_key: str,
        session: ClientSession | None = None,
    ):
        super().__init__()
        self.name = name
        self.email_address = email_address
        self._api_key = api_key
        self._session = session

    async def _get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                headers={
                    "api-key": self._api_key,
                    "accept": "application/json",
                }
            )
        return self._session

    async def send(self, recipient: str, subject: str, body: str) -> None:
        payload = {
            "sender": {"name": self.name, "email": self.email_address},
            "to": [{"email": recipient}],
            "subject": subject,
            "textContent": body,
        }
        session = await self._get_session()
        async with session.post(
            f"{self.BREVO_API_BASE_URL}/smtp/email", json=payload
        ) as response:
            response.raise_for_status()

    async def close(self):
        if self._session is not None:
            await self._session.close()
