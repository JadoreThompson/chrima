from uuid import UUID


class SubscriptionBalanceNotFoundException(Exception):
    def __init__(self, external_id: str, platform_user_id: str, product_id: UUID):
        super().__init__("Subscription balance not found")
        self.external_id = external_id
        self.platform_user_id = platform_user_id
        self.product_id = product_id
