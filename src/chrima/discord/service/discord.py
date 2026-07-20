from __future__ import annotations

import logging
from uuid import UUID

from aiohttp import ClientSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.encryption import EncryptionService
from config import (
    DISCORD_BOT_TOKEN,
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    DISCORD_REDIRECT_URI,
    DISCORD_API_BASE_URL,
)
from util import get_datetime
from ..exception import (
    DiscordAccessTokenNotFoundException,
    DiscordGuildNotFoundException,
    DiscordUserNotFoundException,
    UserDiscordAccessTokenNotFoundException,
)
from ..model import DiscordAccessToken, UserDiscordAccessToken
from ..schema import DiscordChannelResponse, DiscordGuildResponse, DiscordRoleResponse, DiscordUserResponse


class DiscordService:
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

    async def handle_callback(
        self, user_id: UUID, code: str, db_sess: AsyncSession
    ) -> dict:
        body = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        }

        session = await self._get_session()
        rsp = await session.post(f"{DISCORD_API_BASE_URL}/oauth2/token", data=body)
        data = await rsp.json()

        if rsp.status != 200:
            self._logger.error("Failed to exchange code: %s", data)
            raise RuntimeError(f"OAuth token exchange failed ({rsp.status})")

        user = await self._get_user(data["access_token"])
        await self.store_oauth_payload(
            discord_user_id=int(user["id"]),
            oauth_payload=data,
            db_sess=db_sess,
            user_id=user_id,
        )

        return data

    async def get_access_token(
        self,
        db_sess: AsyncSession,
        discord_user_id: int | None = None,
        user_id: UUID | None = None,
    ) -> str:
        if user_id is not None:
            row = await db_sess.get(UserDiscordAccessToken, user_id)
            if row is None:
                raise UserDiscordAccessTokenNotFoundException(user_id)

            discord_user_id = row.discord_user_id

        elif discord_user_id is not None:
            row = await db_sess.scalar(
                select(DiscordAccessToken).where(
                    DiscordAccessToken.user_id == discord_user_id
                )
            )
            if row is None:
                raise DiscordAccessTokenNotFoundException(discord_user_id)

        else:
            raise ValueError("Either discord_user_id or user_id must be provided")

        payload = self._encryption_service.decrypt(
            row.payload, expected_aad=str(discord_user_id)
        )
        expires_in = payload.get("expires_in")

        if expires_in and (
            row.updated_at.timestamp() + expires_in <= get_datetime().timestamp()
        ):
            payload = await self.refresh_access_token(payload["refresh_token"])
            await self.store_oauth_payload(
                discord_user_id=discord_user_id,
                oauth_payload=payload,
                db_sess=db_sess,
                user_id=user_id,
            )

        return payload["access_token"]

    async def get_me(self, user_id: UUID, db_sess: AsyncSession) -> DiscordUserResponse:
        entity = await db_sess.get(UserDiscordAccessToken, user_id)
        if entity is None:
            raise DiscordUserNotFoundException(user_id=user_id)

        access_token = await self.get_access_token(
            db_sess, user_id=user_id, discord_user_id=entity.discord_user_id
        )
        user = await self._get_user(access_token)
        return DiscordUserResponse(
            id=str(user["id"]),
            username=user["username"],
            avatar=user.get("avatar"),
        )

    async def get_guild(
        self, user_id: UUID, guild_id: str, db_sess: AsyncSession
    ) -> DiscordGuildResponse:
        guilds = await self.get_guilds(user_id, db_sess)
        for g in guilds:
            if g.id == guild_id:
                return g
        raise DiscordGuildNotFoundException(guild_id)

    async def get_guild_channels(
        self, user_id: UUID, guild_id: str, db_sess: AsyncSession
    ) -> list[DiscordChannelResponse]:
        guild = await self.get_guild(user_id, guild_id, db_sess)

        session = await self._get_session()
        rsp = await session.get(
            f"{DISCORD_API_BASE_URL}/guilds/{guild.id}/channels",
            headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
        )
        data = await rsp.json()

        if rsp.status != 200:
            self._logger.error("Failed to get guild channels: %s", data)
            raise RuntimeError(f"Failed to get guild channels ({rsp.status})")

        return [
            DiscordChannelResponse(id=str(c["id"]), name=c["name"])
            for c in data
            if c['type'] == 0
        ]

    async def get_guild_roles(
        self, user_id: UUID, guild_id: str, db_sess: AsyncSession
    ) -> list[DiscordRoleResponse]:
        guild = await self.get_guild(user_id, guild_id, db_sess)

        session = await self._get_session()
        rsp = await session.get(
            f"{DISCORD_API_BASE_URL}/guilds/{guild.id}/roles",
            headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
        )
        data = await rsp.json()

        if rsp.status != 200:
            self._logger.error("Failed to get guild roles: %s", data)
            raise RuntimeError(f"Failed to get guild roles ({rsp.status})")

        return [DiscordRoleResponse(id=str(r["id"]), name=r["name"]) for r in data]

    async def get_guilds(
        self, user_id: UUID, db_sess: AsyncSession
    ) -> list[DiscordGuildResponse]:
        access_token = await self.get_access_token(user_id=user_id, db_sess=db_sess)
        session = await self._get_session()

        rsp = await session.get(
            f"{DISCORD_API_BASE_URL}/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = await rsp.json()

        if rsp.status != 200:
            self._logger.error("Failed to get user guilds: %s", data)
            raise RuntimeError(f"Failed to get user guilds ({rsp.status})")

        return [
            DiscordGuildResponse(id=str(g["id"]), name=g["name"], avatar=g.get("icon"))
            for g in data
            if g.get("owner", False)
        ]

    async def refresh_access_token(self, refresh_token: str) -> dict:
        body = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        session = await self._get_session()
        rsp = await session.post(f"{DISCORD_API_BASE_URL}/oauth2/token", data=body)
        result = await rsp.json()

        if rsp.status != 200:
            self._logger.error("Failed to refresh token: %s", result)
            raise RuntimeError(f"Token refresh failed ({rsp.status})")

        return result

    async def _get_user(self, access_token: str) -> dict:
        session = await self._get_session()

        rsp = await session.get(
            f"{DISCORD_API_BASE_URL}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = await rsp.json()

        if rsp.status != 200:
            self._logger.error("Failed to get user info: %s", data)
            raise RuntimeError(f"Failed to get user info ({rsp.status})")

        return data

    async def store_oauth_payload(
        self,
        oauth_payload: dict,
        db_sess: AsyncSession,
        discord_user_id: int,
        user_id: UUID | None = None,
    ):
        encrypted_payload = self._encryption_service.encrypt(
            oauth_payload, aad=str(discord_user_id)
        )

        if user_id is not None:
            # Workspace owner: store/update in UserDiscordAccessToken
            entity = await db_sess.get(UserDiscordAccessToken, user_id)
            if entity:
                entity.payload = encrypted_payload
                entity.discord_user_id = discord_user_id
            else:
                entity = UserDiscordAccessToken(
                    user_id=user_id,
                    discord_user_id=discord_user_id,
                    payload=encrypted_payload,
                )
                db_sess.add(entity)
                await db_sess.flush()
                await db_sess.refresh(entity)

            return

        # Customer: store/update in DiscordAccessToken
        token_entity = await db_sess.scalar(
            select(DiscordAccessToken).where(
                DiscordAccessToken.user_id == discord_user_id
            )
        )
        if token_entity:
            token_entity.payload = encrypted_payload
        else:
            db_sess.add(
                DiscordAccessToken(user_id=discord_user_id, payload=encrypted_payload)
            )
