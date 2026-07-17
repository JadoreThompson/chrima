from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .oauth import DiscordOauthService
from ..schema import DiscordGuildResponse, DiscordUserResponse


class DiscordService:
    def __init__(self, oauth_service: DiscordOauthService):
        self._oauth_service = oauth_service

    async def get_me(
        self, user_id: int, db_sess: AsyncSession
    ) -> DiscordUserResponse:
        return await self._oauth_service.get_me(user_id, db_sess)

    async def get_guilds(
        self, user_id: int, db_sess: AsyncSession
    ) -> list[DiscordGuildResponse]:
        return await self._oauth_service.get_guilds(user_id, db_sess)
