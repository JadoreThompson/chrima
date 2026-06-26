from uuid import UUID


class PriceNotFoundException(Exception):
    def __init__(self, price_id: UUID):
        super().__init__(f"Price not found")
        self.price_id = price_id
