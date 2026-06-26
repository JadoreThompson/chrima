from uuid import UUID


class TokenNotFoundException(Exception):
    def __init__(self, token_id: UUID):
        super().__init__("Token not found")
        self.token_id = token_id
