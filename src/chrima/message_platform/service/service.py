import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.encryption import EncryptionService
from .oauth.discord import DiscordOauthService
from ..enums import MessagePlatformType
from ..model import DiscordAccessToken


class MessagePlatformService:
    def __init__(
        self,
        discord_oauth_service: DiscordOauthService,
        encryption_service: EncryptionService,
    ):
        self._discord_oauth_service = discord_oauth_service
        self._encryption_service = encryption_service

    async def store_oauth_payload(
        self,
        message_platform_type: MessagePlatformType,
        user_id: int,
        oauth_payload: str,
        db_sess: AsyncSession,
    ):
        encrypted_payload = self._encryption_service.encrypt(
            json.dumps(oauth_payload), aad=str(user_id)
        )
        existing = await db_sess.scalar(
            select(DiscordAccessToken).where(DiscordAccessToken.user_id == user_id)
        )
        if existing:
            existing.oauth_payload = encrypted_payload
        else:
            db_sess.add(
                DiscordAccessToken(user_id=user_id, oauth_payload=encrypted_payload)
            )

    async def get_oauth_payload(
        self,
        message_platform_type: MessagePlatformType,
        user_id: int,
        db_sess: AsyncSession,
    ) -> dict:
        row = await db_sess.scalar(
            select(DiscordAccessToken).where(DiscordAccessToken.user_id == user_id)
        )
        if row is None:
            raise ValueError(f"No OAuth token found for user {user_id}")

        decrypted_payload = self._encryption_service.decrypt(
            row.oauth_payload, expected_aad=str(user_id)
        )
        payload = json.loads(decrypted_payload)
        return payload

    async def _refresh_discord_oauth_payload(self, payload: dict) -> dict:
        return await self._discord_oauth_service.refresh_access_token(payload)
