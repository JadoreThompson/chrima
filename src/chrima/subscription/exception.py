from uuid import UUID


class SubscriptionBalanceNotFoundException(Exception):
    def __init__(self, platform_group_id: str, platform_user_id: str, product_id: UUID):
        super().__init__("Subscription balance not found")
        self.platform_group_id = platform_group_id
        self.platform_user_id = platform_user_id
        self.product_id = product_id
