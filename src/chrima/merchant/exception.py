from uuid import UUID


class MerchantNotFoundException(Exception):
    def __init__(self, merchant_id: UUID):
        super().__init__("Merchant not found")
        self.merchant_id = merchant_id
