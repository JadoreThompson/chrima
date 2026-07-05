import logging

import discord
from aiohttp import ClientSession
from sqlalchemy.ext.asyncio import AsyncSession

from config import DISCORD_BOT_TOKEN

from .service import MessagePlatformService
from ..enums import MessagePlatformType
from ..exception import UserNotInGuildException

BASE_URL = "https://discord.com/api/v10"


class DiscordService:
    def __init__(
        self,
        discord_client: discord.Client,
        message_platform_service: MessagePlatformService,
        bot_token: str = DISCORD_BOT_TOKEN,
    ):
        self._discord_client = discord_client
        self._message_platform_service = message_platform_service
        self._bot_token = bot_token
        self._session: ClientSession | None = None
        self._logger = logging.getLogger("discord_service")

    async def _get_http_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                headers={"Authorization": f"Bot {self._bot_token}"}
            )
        return self._session

    async def add_user_to_guild(
        self, *, guild_id: int, user_id: int, access_token: str
    ) -> dict:
        """
        Adds a user to a Discord guild (server) using the Discord OAuth2 access token.

        This endpoint uses Discord's "Add Guild Member" API, which requires a valid
        user OAuth2 access token that includes the `guilds.join` scope. The bot must
        also have the appropriate permissions in the target guild.

        Args:
            guild_id (int): The ID of the Discord guild (server) to add the user to.
            user_id (int): The Discord user ID of the member being added.
            access_token (str): The Discord OAuth2 access token for the user. This
                token must be issued with the `guilds.join` scope, which allows the
                bot to add the user to a guild on their behalf.

        Returns:
            dict: The JSON response from Discord if the request is successful.
                Returns an empty dict for successful responses with no body.

        Raises:
            RuntimeError: If the request to Discord fails. Includes the HTTP status
                code and response body for debugging purposes.
        """
        payload = {"access_token": access_token}
        session = await self._get_http_session()

        rsp = await session.put(
            f"{BASE_URL}/guilds/{guild_id}/members/{user_id}",
            json=payload,
            headers={"Authorization": f"Bot {self._bot_token}"},
        )

        data = await rsp.json(content_type=None)

        if rsp.status in (200, 201, 204):
            return data if data else {}

        raise RuntimeError(f"Failed to add user to guild ({rsp.status}): {data}")

    async def assign_roles(
        self, guild_id: int, user_id: int, roles: list[int], db_sess: AsyncSession
    ) -> None:
        guild = self._discord_client.get_guild(guild_id)
        if guild is None:
            try:
                guild = await self._discord_client.fetch_guild(guild_id)
            except discord.NotFound:
                raise UserNotInGuildException(user_id, guild_id)

        try:
            member = await guild.fetch_member(user_id)
        except discord.NotFound:
            payload = await self._message_platform_service.get_oauth_payload(
                MessagePlatformType.DISCORD, user_id, db_sess
            )
            access_token = payload.get("access_token")
            if not access_token:
                raise UserNotInGuildException(user_id, guild_id)

            await self.add_user_to_guild(
                guild_id=guild_id, user_id=user_id, access_token=access_token
            )
            member = await guild.fetch_member(user_id)

        role_objects = []
        for role_id in roles:
            role = guild.get_role(role_id)
            if role is None:
                raise ValueError(f"Role '{role_id}' not found in guild {guild_id}")
            role_objects.append(role)

        if role_objects:
            await member.add_roles(*role_objects, reason="Chrima product purchase")
