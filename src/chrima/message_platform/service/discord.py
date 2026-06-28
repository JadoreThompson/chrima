import logging

import discord

from ..exception import UserNotInGuildException


class DiscordService:
    def __init__(self, discord_client: discord.Client):
        self._discord_client = discord_client
        self._logger = logging.getLogger("discord_service")

    async def invite_user(self, group_url: str | None, user_id: str) -> None:
        ...

    async def assign_roles(
        self, guild_id: int, user_id: int, roles: list[str]
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
            raise UserNotInGuildException(user_id, guild_id)

        role_objects = []
        for role_name in roles:
            role = discord.utils.get(guild.roles, name=role_name)
            if role is not None:
                role_objects.append(role)
            else:
                self._logger.warning("Role %s not found in guild %s", role_name, guild_id)

        if role_objects:
            await member.add_roles(*role_objects, reason="Chrima product purchase")
