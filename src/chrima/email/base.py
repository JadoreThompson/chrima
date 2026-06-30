from abc import ABC, abstractmethod


class EmailService(ABC):
    @abstractmethod
    async def send(self, recipient: str, subject: str, body: str) -> None: ...

    @abstractmethod
    async def close(self): ...
