import logging

from aiohttp import ClientSession

from config import DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_REDIRECT_URI

TOKEN_URL = "https://discord.com/api/v10/oauth2/token"


class DiscordOauthService:
    def __init__(self):
        self._session: ClientSession | None = None
        self._logger = logging.getLogger("discord_oauth_service")

    async def _get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession()
        return self._session

    async def handle_callback(self, code: str) -> dict:
        payload = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        }

        session = await self._get_session()
        rsp = await session.post(TOKEN_URL, data=payload)
        data = await rsp.json()
        if rsp.status != 200:
            self._logger.error("Failed to exchange code: %s", data)
            raise RuntimeError(f"OAuth token exchange failed ({rsp.status})")
        
        user = await self._get_user(data["access_token"])
        data["user"] = user
        return data

    async def refresh_access_token(self, payload: dict) -> dict:
        refresh_token = payload.get("refresh_token")
        if not refresh_token:
            raise ValueError("No refresh token in payload")

        data = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        session = await self._get_session()
        rsp = await session.post(TOKEN_URL, data=data)
        result = await rsp.json()
        if rsp.status != 200:
            self._logger.error("Failed to refresh token: %s", result)
            raise RuntimeError(f"Token refresh failed ({rsp.status})")
        return result

    async def _get_user(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        session = await self._get_session()
        rsp = await session.get("https://discord.com/api/v10/users/@me", headers=headers)
        data = await rsp.json()
        if rsp.status != 200:
            self._logger.error("Failed to get user info: %s", data)
            raise RuntimeError(f"Failed to get user info ({rsp.status})")
        return data