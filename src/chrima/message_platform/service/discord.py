import logging

import discord
from aiohttp import ClientSession

from config import DISCORD_BOT_TOKEN

from ..exception import UserNotInGuildException


class DiscordService:
    BASE_URL = "https://discord.com/api/v10"

    def __init__(
        self, discord_client: discord.Client, bot_token: str = DISCORD_BOT_TOKEN
    ):
        self._discord_client = discord_client
        self._logger = logging.getLogger("discord_service")
        self._bot_token = bot_token
        self._session: ClientSession | None = None

    async def _get_http_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                headers={"Authorization": f"Bot {self._bot_token}"}
            )
        return self._session

    async def invite_user(self, group_url: str | None, user_id: str) -> None: ...

    async def add_user_to_guild(
        self,
        *,
        guild_id: int,
        user_id: int,
        access_token: str,
        nick: str | None = None,
        roles: list[int] | None = None,
        mute: bool = False,
        deaf: bool = False,
    ) -> dict:
        payload = {
            "access_token": access_token,
        }

        if nick is not None:
            payload["nick"] = nick

        if roles is not None:
            payload["roles"] = roles

        payload["mute"] = mute
        payload["deaf"] = deaf

        session = await self._get_http_session()
        async with session.put(
            f"{self.BASE_URL}/guilds/{guild_id}/members/{user_id}",
            json=payload,
            headers={
                "Authorization": f"Bot {self._bot_token}",
            },
        ) as resp:
            data = await resp.json(content_type=None)

            if resp.status in (200, 201, 204):
                return data if data else {}

            raise RuntimeError(f"Failed to add user to guild ({resp.status}): {data}")

    async def assign_roles(self, guild_id: int, user_id: int, roles: list[str]) -> None:
        guild = self._discord_client.get_guild(guild_id)
        if guild is None:
            try:
                guild = await self._discord_client.fetch_guild(guild_id)
            except discord.NotFound:
                raise UserNotInGuildException(user_id, guild_id)

        try:
            member = await guild.fetch_member(user_id)
        except discord.NotFound:
            raise UserNotInGuildException(user_id, guild_id)

        role_objects = []
        for role_name in roles:
            role = discord.utils.get(guild.roles, name=role_name)
            if role is not None:
                role_objects.append(role)
            else:
                self._logger.warning(
                    "Role %s not found in guild %s", role_name, guild_id
                )

        if role_objects:
            await member.add_roles(*role_objects, reason="Chrima product purchase")
