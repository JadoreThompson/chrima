from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.jwt.schema import JWTPayload
from .exception import DiscordChannelNotFoundException
from .schema import DiscordChannelResponse, DiscordGuildResponse, DiscordUserResponse
from .service.discord import DiscordService

router = APIRouter(prefix="/discord", tags=["discord"])


@router.get("/me", response_model=DiscordUserResponse)
async def get_discord_me(
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    discord_service: DiscordService = Depends(depends_object(DiscordService)),
):
    try:
        return await discord_service.get_me(jwt.sub, db_sess)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/guilds/{guild_id}", response_model=DiscordGuildResponse)
async def get_discord_guild(
    guild_id: str,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    discord_service: DiscordService = Depends(depends_object(DiscordService)),
):
    try:
        guild = await discord_service.get_guild(jwt.sub, guild_id, db_sess)
        return guild
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get(
    "/guilds/{guild_id}/channels/{channel_id}", response_model=DiscordChannelResponse
)
async def get_discord_guild_channel(
    guild_id: str,
    channel_id: str,
    jwt: JWTPayload = Depends(depends_jwt),
    discord_service: DiscordService = Depends(depends_object(DiscordService)),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    try:
        channels = await discord_service.get_guild_channels(jwt.sub, guild_id, db_sess)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    for c in channels:
        if c.id == channel_id:
            return c

    raise DiscordChannelNotFoundException(channel_id)


@router.get("/guilds/{guild_id}/channels", response_model=list[DiscordChannelResponse])
async def get_discord_guild_channels(
    guild_id: str,
    jwt: JWTPayload = Depends(depends_jwt),
    discord_service: DiscordService = Depends(depends_object(DiscordService)),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    try:
        return await discord_service.get_guild_channels(jwt.sub, guild_id, db_sess)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/guilds", response_model=list[DiscordGuildResponse])
async def get_discord_guilds(
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    discord_service: DiscordService = Depends(depends_object(DiscordService)),
):
    try:
        return await discord_service.get_guilds(jwt.sub, db_sess)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
