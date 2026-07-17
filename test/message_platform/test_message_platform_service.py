import pytest

from chrima.discord import DiscordOauthService
from chrima.discord.exception import DiscordUserNotFoundException
from chrima.encryption import EncryptionService
from core.db import get_db_session


@pytest.fixture
def oauth_service():
    return DiscordOauthService(encryption_service=EncryptionService())


@pytest.fixture
def sample_payload():
    return {"access_token": "abc123", "refresh_token": "def456", "expires_in": 604800}


@pytest.mark.asyncio(loop_scope="session")
class TestStoreOauthPayload:
    async def test_stores_new_record(
        self, oauth_service, sample_payload, create_drop_tables
    ):
        user_id = 12345
        async with get_db_session() as db_sess:
            await oauth_service.store_oauth_payload(
                user_id, sample_payload, db_sess
            )

        async with get_db_session() as db_sess:
            result = await oauth_service.get_access_token(user_id, db_sess)
        assert result == "abc123"

    async def test_updates_existing_record(
        self, oauth_service, sample_payload, create_drop_tables
    ):
        user_id = 67890
        async with get_db_session() as db_sess:
            await oauth_service.store_oauth_payload(
                user_id, {"access_token": "old"}, db_sess
            )

        new_payload = {"access_token": "new_token", "refresh_token": "new_refresh"}
        async with get_db_session() as db_sess:
            await oauth_service.store_oauth_payload(
                user_id, new_payload, db_sess
            )

        async with get_db_session() as db_sess:
            result = await oauth_service.get_access_token(user_id, db_sess)
        assert result == "new_token"

    async def test_stores_multiple_users(
        self, oauth_service, sample_payload, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            await oauth_service.store_oauth_payload(
                111, {**sample_payload, "access_token": "abc123-111"}, db_sess
            )
            await oauth_service.store_oauth_payload(
                222, {**sample_payload, "access_token": "abc123-222"}, db_sess
            )

        async with get_db_session() as db_sess:
            for uid in (111, 222):
                result = await oauth_service.get_access_token(uid, db_sess)
                assert result == f"abc123-{uid}"


@pytest.mark.asyncio(loop_scope="session")
class TestGetAccessToken:
    async def test_returns_stored_token(
        self, oauth_service, sample_payload, create_drop_tables
    ):
        user_id = 999
        async with get_db_session() as db_sess:
            await oauth_service.store_oauth_payload(
                user_id, sample_payload, db_sess
            )

        async with get_db_session() as db_sess:
            result = await oauth_service.get_access_token(user_id, db_sess)

        assert result == "abc123"

    async def test_raises_on_nonexistent_user(
        self, oauth_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            with pytest.raises(DiscordUserNotFoundException):
                await oauth_service.get_access_token(777, db_sess)

    async def test_returns_correct_token_per_user(
        self, oauth_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            await oauth_service.store_oauth_payload(
                111, {"access_token": "token_a"}, db_sess
            )
            await oauth_service.store_oauth_payload(
                222, {"access_token": "token_b"}, db_sess
            )

        async with get_db_session() as db_sess:
            result_a = await oauth_service.get_access_token(111, db_sess)
            result_b = await oauth_service.get_access_token(222, db_sess)

        assert result_a == "token_a"
        assert result_b == "token_b"
