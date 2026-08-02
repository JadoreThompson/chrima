from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession


class BillingWebhookListener(ABC):
    @abstractmethod
    async def handle(self, headers: dict, payload: bytes, db_sess: AsyncSession):
        pass
