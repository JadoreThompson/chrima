from uuid import UUID


class SubscriptionBalanceNotFoundException(Exception):
    def __init__(
        self,
        external_id: str = "",
        platform_user_id: str = "",
        product_id: UUID | None = None,
        balance_id: UUID | None = None,
    ):
        super().__init__("Subscription balance not found")
        self.external_id = external_id
        self.platform_user_id = platform_user_id
        self.product_id = product_id
        self.balance_id = balance_id


class SubscriptionBalanceAlreadyCancelledException(Exception):
    def __init__(self, balance_id: UUID):
        super().__init__(f"Subscription balance {balance_id} is already cancelled")
        self.balance_id = balance_id
