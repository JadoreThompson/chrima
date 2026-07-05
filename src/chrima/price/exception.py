from uuid import UUID


class PriceException(Exception):
    """Base class for all price exceptions"""


class PriceNotFoundException(PriceException):
    def __init__(self, price_id: UUID):
        super().__init__(f"Price not found")
        self.price_id = price_id


class PriceValidationException(PriceException):
    """Raised when price input fails validation."""
