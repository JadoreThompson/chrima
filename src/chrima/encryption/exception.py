class EncryptionException(Exception):
    """Base class for encryption-related exceptions."""

    pass


class IncorrectAADException(EncryptionException):
    """Raised when the provided AAD does not match the expected AAD."""

    def __init__(self, expected_aad: str, actual_aad: str):
        super().__init__(f"AAD mismatch: expected '{expected_aad}', got '{actual_aad}'")
