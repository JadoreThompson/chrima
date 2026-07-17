from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.jwt.schema import JWTPayload
from .schema import DiscordGuildResponse, DiscordUserResponse
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
