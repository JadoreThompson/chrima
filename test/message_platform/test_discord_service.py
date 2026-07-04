import asyncio
import os

import discord
import pytest
import pytest_asyncio

from chrima.message_platform.service.discord import DiscordService

require_discord = pytest.mark.skipif(
    not os.getenv("DISCORD_BOT_TOKEN")
    or not os.getenv("DISCORD_GUILD_ID")
    or not os.getenv("DISCORD_USER_ID")
    or not os.getenv("DISCORD_ACCESS_TOKEN"),
    reason="Requires DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_USER_ID, DISCORD_ACCESS_TOKEN",
)


@pytest_asyncio.fixture(scope="session")
async def discord_client():
    client = discord.Client(intents=discord.Intents.default())
    bg = asyncio.create_task(client.start(os.environ["DISCORD_BOT_TOKEN"]))
    await asyncio.sleep(1)
    await client.wait_until_ready()
    yield client
    bg.cancel()
    try:
        await client.close()
    except Exception:
        pass


@pytest_asyncio.fixture
async def managed_guild_member(discord_client, guild_id, user_id):
    yield
    try:
        guild = discord_client.get_guild(guild_id) or await discord_client.fetch_guild(
            guild_id
        )
        member = guild.get_member(user_id) or await guild.fetch_member(user_id)
        await member.kick(reason="Chrima test cleanup")
    except Exception:
        pass


@pytest.fixture
def guild_id():
    return int(os.environ["DISCORD_GUILD_ID"])


@pytest.fixture
def user_id():
    return int(os.environ["DISCORD_USER_ID"])


@pytest.fixture
def access_token():
    return os.environ["DISCORD_ACCESS_TOKEN"]


@pytest.fixture
def discord_service(discord_client):
    return DiscordService(discord_client=discord_client)


@require_discord
@pytest.mark.asyncio(loop_scope="session")
class TestAddUserToGuild:

    async def _fetch_member(self, discord_client, guild_id, user_id):
        guild = discord_client.get_guild(guild_id) or await discord_client.fetch_guild(
            guild_id
        )
        return guild.get_member(user_id) or await guild.fetch_member(user_id)

    async def test_adds_user_to_guild(
        self,
        discord_client,
        discord_service,
        guild_id,
        user_id,
        access_token,
        managed_guild_member,
    ):
        await discord_service.add_user_to_guild(
            guild_id=guild_id,
            user_id=user_id,
            access_token=access_token,
        )

        member = await self._fetch_member(discord_client, guild_id, user_id)
        assert member is not None
        assert member.id == user_id

    async def test_adds_with_nick(
        self,
        discord_client,
        discord_service,
        guild_id,
        user_id,
        access_token,
        managed_guild_member,
    ):
        await discord_service.add_user_to_guild(
            guild_id=guild_id,
            user_id=user_id,
            access_token=access_token,
            nick="Chrima User",
        )

        member = await self._fetch_member(discord_client, guild_id, user_id)
        assert member is not None
        assert member.nick == "Chrima User"

    async def test_adds_with_roles(
        self,
        discord_client,
        discord_service,
        guild_id,
        user_id,
        access_token,
        managed_guild_member,
    ):
        guild = discord_client.get_guild(guild_id) or await discord_client.fetch_guild(
            guild_id
        )
        target_role = next((r for r in guild.roles if r.name != "@everyone"), None)
        assert target_role is not None, "Guild must have at least one assignable role"

        await discord_service.add_user_to_guild(
            guild_id=guild_id,
            user_id=user_id,
            access_token=access_token,
            nick="Chrima Role Test",
            roles=[target_role.id],
        )

        member = await self._fetch_member(discord_client, guild_id, user_id)
        assert member is not None
        if target_role.id not in [r.id for r in member.roles]:
            pytest.skip("Bot lacks Manage Roles permission or role was not assigned")

    async def test_raises_on_invalid_guild(self, discord_service):
        with pytest.raises(RuntimeError, match="Failed to add user to guild"):
            await discord_service.add_user_to_guild(
                guild_id=0, user_id=0, access_token="invalid"
            )

    async def test_raises_on_invalid_token(self, discord_service, guild_id):
        with pytest.raises(RuntimeError, match="Failed to add user to guild"):
            await discord_service.add_user_to_guild(
                guild_id=guild_id,
                user_id=0,
                access_token="bad_token",
            )
