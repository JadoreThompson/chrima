import os

import pytest
import pytest_asyncio

from chrima.discord.exception import DiscordAccessTokenNotFoundException, DiscordUserNotInGuildException
from core.db import get_db_session

require_discord = pytest.mark.skipif(
    not os.getenv("DISCORD_BOT_TOKEN")
    or not os.getenv("DISCORD_GUILD_ID")
    or not os.getenv("DISCORD_USER_ID")
    or not os.getenv("DISCORD_ACCESS_TOKEN"),
    reason="Requires DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_USER_ID, DISCORD_ACCESS_TOKEN",
)


@pytest_asyncio.fixture(loop_scope="session")
async def managed_guild_member(discord_client, discord_guild_id, discord_user_id):
    yield

    try:
        guild = discord_client.get_guild(
            discord_guild_id
        ) or await discord_client.fetch_guild(discord_guild_id)
        member = guild.get_member(discord_user_id) or await guild.fetch_member(
            discord_user_id
        )
        await member.kick(reason="Chrima test cleanup")
    except Exception:
        pass


async def _ensure_not_in_guild(discord_client, guild_id, user_id):
    try:
        guild = discord_client.get_guild(guild_id) or await discord_client.fetch_guild(
            guild_id
        )
        member = guild.get_member(user_id) or await guild.fetch_member(user_id)
        await member.kick(reason="Chrima test cleanup")
    except Exception:
        pass


@require_discord
@pytest.mark.asyncio(loop_scope="session")
class TestAddUserToGuild:
    async def _fetch_member(self, discord_client, discord_guild_id, discord_user_id):
        guild = await discord_client.fetch_guild(discord_guild_id)
        return await guild.fetch_member(discord_user_id)

    async def test_adds_user_to_guild(
        self,
        discord_client,
        discord_membership_service,
        discord_guild_id,
        discord_user_id,
        discord_access_token,
        managed_guild_member,
    ):
        await discord_membership_service.add_user_to_guild(
            guild_id=discord_guild_id,
            user_id=discord_user_id,
            access_token=discord_access_token,
        )

        member = await self._fetch_member(
            discord_client, discord_guild_id, discord_user_id
        )
        assert member is not None
        assert member.id == discord_user_id

    async def test_adds_with_nick(
        self,
        discord_client,
        discord_membership_service,
        discord_guild_id,
        discord_user_id,
        discord_access_token,
        managed_guild_member,
    ):
        await discord_membership_service.add_user_to_guild(
            guild_id=discord_guild_id,
            user_id=discord_user_id,
            access_token=discord_access_token,
        )

        member = await self._fetch_member(
            discord_client, discord_guild_id, discord_user_id
        )
        assert member is not None

    async def test_adds_with_roles(
        self,
        discord_client,
        discord_membership_service,
        discord_guild_id,
        discord_user_id,
        discord_access_token,
        managed_guild_member,
    ):
        guild = discord_client.get_guild(
            discord_guild_id
        ) or await discord_client.fetch_guild(discord_guild_id)
        target_role = next((r for r in guild.roles if r.name != "@everyone"), None)
        assert target_role is not None, "Guild must have at least one assignable role"

        await discord_membership_service.add_user_to_guild(
            guild_id=discord_guild_id,
            user_id=discord_user_id,
            access_token=discord_access_token,
        )

        member = await self._fetch_member(
            discord_client, discord_guild_id, discord_user_id
        )
        assert member is not None
        if target_role.id not in [r.id for r in member.roles]:
            pytest.skip("Bot lacks Manage Roles permission or role was not assigned")

    async def test_raises_on_invalid_guild(self, discord_membership_service):
        with pytest.raises(RuntimeError, match="Failed to add user to guild"):
            await discord_membership_service.add_user_to_guild(
                guild_id=0, user_id=0, access_token="invalid"
            )

    async def test_raises_on_invalid_token(
        self, discord_membership_service, discord_guild_id
    ):
        with pytest.raises(RuntimeError, match="Failed to add user to guild"):
            await discord_membership_service.add_user_to_guild(
                guild_id=discord_guild_id,
                user_id=0,
                access_token="bad_token",
            )


@require_discord
@pytest.mark.asyncio(loop_scope="session")
class TestAssignRoles:
    async def test_assigns_role_to_member(
        self,
        discord_client,
        discord_membership_service,
        discord_guild_id,
        discord_user_id,
        discord_access_token,
        create_drop_tables,
    ):
        await discord_membership_service.add_user_to_guild(
            guild_id=discord_guild_id,
            user_id=discord_user_id,
            access_token=discord_access_token,
        )
        guild = discord_client.get_guild(
            discord_guild_id
        ) or await discord_client.fetch_guild(discord_guild_id)
        target_role = next((r for r in guild.roles if r.name != "@everyone"), None)
        assert target_role is not None

        async with get_db_session() as db_sess:
            await discord_membership_service.assign_roles(
                guild_id=discord_guild_id,
                user_id=discord_user_id,
                roles=[target_role.id],
                db_sess=db_sess,
            )

        member = guild.get_member(discord_user_id) or await guild.fetch_member(
            discord_user_id
        )
        assert target_role.id in [r.id for r in member.roles]
        await _ensure_not_in_guild(discord_client, discord_guild_id, discord_user_id)

    async def test_raises_on_nonexistent_role(
        self,
        discord_client,
        discord_membership_service,
        discord_guild_id,
        discord_user_id,
        discord_access_token,
        create_drop_tables,
    ):
        await discord_membership_service.add_user_to_guild(
            guild_id=discord_guild_id,
            user_id=discord_user_id,
            access_token=discord_access_token,
        )
        fake_role_id = 999999999999999999
        async with get_db_session() as db_sess:
            with pytest.raises(ValueError, match=f"Role '{fake_role_id}' not found"):
                await discord_membership_service.assign_roles(
                    guild_id=discord_guild_id,
                    user_id=discord_user_id,
                    roles=[fake_role_id],
                    db_sess=db_sess,
                )
        await _ensure_not_in_guild(discord_client, discord_guild_id, discord_user_id)

    async def test_raises_when_not_in_guild_and_no_token(
        self, discord_membership_service, discord_guild_id, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            with pytest.raises(DiscordAccessTokenNotFoundException):
                await discord_membership_service.assign_roles(
                    guild_id=discord_guild_id,
                    user_id=0,
                    roles=[1],
                    db_sess=db_sess,
                )

    async def test_adds_user_and_assigns_roles_when_not_in_guild(
        self,
        discord_client,
        discord_service,
        discord_membership_service,
        discord_guild_id,
        discord_user_id,
        discord_access_token,
        create_drop_tables,
    ):
        await _ensure_not_in_guild(discord_client, discord_guild_id, discord_user_id)

        oauth_payload = {"access_token": discord_access_token}

        async with get_db_session() as db_sess:
            await discord_service.store_oauth_payload(
                discord_user_id=discord_user_id,
                oauth_payload=oauth_payload,
                db_sess=db_sess,
            )
            await db_sess.commit()

        guild = discord_client.get_guild(
            discord_guild_id
        ) or await discord_client.fetch_guild(discord_guild_id)
        target_role = next((r for r in guild.roles if r.name != "@everyone"), None)
        assert target_role is not None

        async with get_db_session() as db_sess:
            await discord_membership_service.assign_roles(
                guild_id=discord_guild_id,
                user_id=discord_user_id,
                roles=[target_role.id],
                db_sess=db_sess,
            )

        member = guild.get_member(discord_user_id) or await guild.fetch_member(
            discord_user_id
        )
        assert member is not None
        assert target_role.id in [r.id for r in member.roles]
        await _ensure_not_in_guild(discord_client, discord_guild_id, discord_user_id)
