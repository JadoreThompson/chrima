from abc import ABC, abstractmethod

from chrima.user.enums import Tier
from ..schema import CheckoutSession


class BillingProvider(ABC):
    @abstractmethod
    async def create_checkout_session(
        self, tier: Tier, metadata: dict | None = None
    ) -> CheckoutSession:
        pass

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> None:
        pass
