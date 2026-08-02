from uuid import UUID


class BillingNotFoundException(Exception):
    def __init__(self, user_id: UUID):
        super().__init__(f"Billing record not found for user '{user_id}'.")


class BillingAlreadyCancelledException(Exception):
    def __init__(self, subscription_id: str):
        super().__init__(
            f"Subscription '{subscription_id}' has already been cancelled."
        )


class BillingProviderDisabledException(Exception):
    def __init__(self, provider: str):
        super().__init__(f"Billing provider '{provider}' is not enabled.")


class BillingWebhookVerificationException(Exception):
    def __init__(self, message: str = "Invalid webhook signature."):
        super().__init__(message)
