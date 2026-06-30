from .base import EmailService


class BrevoEmailService(EmailService):
    def __init__(self, name: str, email_address: str, api_key: str, secret_key: str):
        super().__init__()
        self.name = name
        self.email_address = email_address
        self._api_key = api_key
        self._secret_key = secret_key
