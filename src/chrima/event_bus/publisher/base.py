from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from core.event import BaseEvent


class EventPublisher(ABC):

    @abstractmethod
    async def publish(
        self, event: BaseEvent, db_sess: AsyncSession | None = None
    ) -> None: ...

