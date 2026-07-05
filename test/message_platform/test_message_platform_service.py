import pytest

from chrima.encryption import EncryptionService
from chrima.message_platform.enums import MessagePlatformType
from chrima.message_platform.service.oauth.discord import DiscordOauthService
from chrima.message_platform.service.service import MessagePlatformService
from core.db import get_db_session


@pytest.fixture
def mp_service():
    return MessagePlatformService(
        discord_oauth_service=DiscordOauthService(),
        encryption_service=EncryptionService(),
    )


@pytest.fixture
def sample_payload():
    return {"access_token": "abc123", "refresh_token": "def456", "expires_in": 604800}


@pytest.mark.asyncio(loop_scope="session")
class TestStoreOauthPayload:
    async def test_stores_new_record(
        self, mp_service, sample_payload, create_drop_tables
    ):
        user_id = 12345
        async with get_db_session() as db_sess:
            await mp_service.store_oauth_payload(
                MessagePlatformType.DISCORD,
                user_id,
                sample_payload,
                db_sess,
            )

        async with get_db_session() as db_sess:
            result = await mp_service.get_oauth_payload(
                MessagePlatformType.DISCORD,
                user_id,
                db_sess,
            )
        assert result["access_token"] == "abc123"
        assert result["refresh_token"] == "def456"

    async def test_updates_existing_record(
        self, mp_service, sample_payload, create_drop_tables
    ):
        user_id = 67890
        async with get_db_session() as db_sess:
            await mp_service.store_oauth_payload(
                MessagePlatformType.DISCORD,
                user_id,
                {"access_token": "old"},
                db_sess,
            )

        new_payload = {"access_token": "new_token", "refresh_token": "new_refresh"}
        async with get_db_session() as db_sess:
            await mp_service.store_oauth_payload(
                MessagePlatformType.DISCORD,
                user_id,
                new_payload,
                db_sess,
            )

        async with get_db_session() as db_sess:
            result = await mp_service.get_oauth_payload(
                MessagePlatformType.DISCORD,
                user_id,
                db_sess,
            )
        assert result["access_token"] == "new_token"
        assert result["refresh_token"] == "new_refresh"

    async def test_stores_multiple_users(
        self, mp_service, sample_payload, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            await mp_service.store_oauth_payload(
                MessagePlatformType.DISCORD,
                111,
                {**sample_payload, "access_token": "abc123-111"},
                db_sess,
            )
            await mp_service.store_oauth_payload(
                MessagePlatformType.DISCORD,
                222,
                {**sample_payload, "access_token": "abc123-222"},
                db_sess,
            )

        async with get_db_session() as db_sess:
            for uid in (111, 222):
                result = await mp_service.get_oauth_payload(
                    MessagePlatformType.DISCORD,
                    uid,
                    db_sess,
                )
                assert result["access_token"] == f"abc123-{uid}"


@pytest.mark.asyncio(loop_scope="session")
class TestGetOauthPayload:
    async def test_returns_stored_payload(
        self, mp_service, sample_payload, create_drop_tables
    ):
        user_id = 999
        async with get_db_session() as db_sess:
            await mp_service.store_oauth_payload(
                MessagePlatformType.DISCORD,
                user_id,
                sample_payload,
                db_sess,
            )

        async with get_db_session() as db_sess:
            result = await mp_service.get_oauth_payload(
                MessagePlatformType.DISCORD,
                user_id,
                db_sess,
            )

        assert result["access_token"] == "abc123"
        assert result["refresh_token"] == "def456"

    async def test_raises_on_nonexistent_user(self, mp_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(ValueError, match="No OAuth token found for user 777"):
                await mp_service.get_oauth_payload(
                    MessagePlatformType.DISCORD,
                    777,
                    db_sess,
                )

    async def test_returns_correct_payload_per_user(
        self, mp_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            await mp_service.store_oauth_payload(
                MessagePlatformType.DISCORD,
                111,
                {"access_token": "token_a"},
                db_sess,
            )
            await mp_service.store_oauth_payload(
                MessagePlatformType.DISCORD,
                222,
                {"access_token": "token_b"},
                db_sess,
            )

        async with get_db_session() as db_sess:
            result_a = await mp_service.get_oauth_payload(
                MessagePlatformType.DISCORD,
                111,
                db_sess,
            )
            result_b = await mp_service.get_oauth_payload(
                MessagePlatformType.DISCORD,
                222,
                db_sess,
            )

        assert result_a["access_token"] == "token_a"
        assert result_b["access_token"] == "token_b"
