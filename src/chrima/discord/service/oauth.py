from __future__ import annotations

import json
import logging

from aiohttp import ClientSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.encryption import EncryptionService
from config import DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_REDIRECT_URI
from util import get_datetime
from ..exception import DiscordUserNotFoundException
from ..model import DiscordAccessToken
from ..schema import DiscordGuildResponse, DiscordUserResponse

TOKEN_URL = "https://discord.com/api/v10/oauth2/token"
API_BASE = "https://discord.com/api/v10"


class DiscordOauthService:
    def __init__(self, encryption_service: EncryptionService):
        self._encryption_service = encryption_service
        self._session: ClientSession | None = None
        self._logger = logging.getLogger("discord_oauth_service")

    async def _get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        return self._session

    async def handle_callback(self, code: str, db_sess: AsyncSession) -> dict:
        body = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        }

        session = await self._get_session()
        rsp = await session.post(TOKEN_URL, data=body)
        data = await rsp.json()

        if rsp.status != 200:
            self._logger.error("Failed to exchange code: %s", data)
            raise RuntimeError(f"OAuth token exchange failed ({rsp.status})")

        user = await self._get_user(data["access_token"])
        await self.store_oauth_payload(
            user_id=int(user["id"]),
            oauth_payload=data,
            db_sess=db_sess,
        )

        return data

    async def get_access_token(
        self, user_id: int, db_sess: AsyncSession
    ) -> str:
        row = await db_sess.scalar(
            select(DiscordAccessToken).where(DiscordAccessToken.user_id == user_id)
        )
        if row is None:
            raise DiscordUserNotFoundException(user_id=user_id)

        decrypted_payload = self._encryption_service.decrypt(
            row.oauth_payload, expected_aad=str(user_id)
        )
        payload = json.loads(decrypted_payload)

        expires_in = payload.get("expires_in")
        if expires_in and (
            row.updated_at.timestamp() + expires_in
            <= get_datetime().timestamp()
        ):
            payload = await self._refresh_access_token(payload)
            await self.store_oauth_payload(
                user_id=user_id,
                oauth_payload=payload,
                db_sess=db_sess,
            )

        return payload["access_token"]

    async def get_me(
        self, user_id: int, db_sess: AsyncSession
    ) -> DiscordUserResponse:
        access_token = await self.get_access_token(user_id, db_sess)
        user = await self._get_user(access_token)
        return DiscordUserResponse(
            id=str(user["id"]),
            username=user["username"],
            avatar=user.get("avatar"),
        )

    async def get_guilds(
        self, user_id: int, db_sess: AsyncSession
    ) -> list[DiscordGuildResponse]:
        access_token = await self.get_access_token(user_id, db_sess)
        session = await self._get_session()

        rsp = await session.get(
            f"{API_BASE}/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = await rsp.json()

        if rsp.status != 200:
            self._logger.error("Failed to get user guilds: %s", data)
            raise RuntimeError(f"Failed to get user guilds ({rsp.status})")

        return [
            DiscordGuildResponse(
                id=str(g["id"]),
                name=g["name"],
                avatar=g.get("icon"),
            )
            for g in data
        ]

    async def _refresh_access_token(self, payload: dict) -> dict:
        refresh_token = payload.get("refresh_token")
        if not refresh_token:
            raise ValueError("No refresh token in payload")

        body = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        session = await self._get_session()
        rsp = await session.post(TOKEN_URL, data=body)
        result = await rsp.json()

        if rsp.status != 200:
            self._logger.error("Failed to refresh token: %s", result)
            raise RuntimeError(f"Token refresh failed ({rsp.status})")

        return result

    async def _get_user(self, access_token: str) -> dict:
        session = await self._get_session()

        rsp = await session.get(
            f"{API_BASE}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = await rsp.json()

        if rsp.status != 200:
            self._logger.error("Failed to get user info: %s", data)
            raise RuntimeError(f"Failed to get user info ({rsp.status})")

        return data

    async def store_oauth_payload(
        self,
        user_id: int,
        oauth_payload: dict,
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
                DiscordAccessToken(
                    user_id=user_id, oauth_payload=encrypted_payload
                )
            )
