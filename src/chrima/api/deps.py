from typing import Type

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyCookie
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.object_registry import ObjectRegistry
from config import COOKIE_ALIAS
from core.db import get_db_session, smaker
from chrima.jwt import JWTService, JWTException
from chrima.user import UserService
from chrima.user.schema import UserResponse

cookie_scheme = APIKeyCookie(name=COOKIE_ALIAS, auto_error=False)


def depends_object(typ: Type):
    def _func(req: Request):
        object_registry: ObjectRegistry = req.app.state.object_registry
        return object_registry.get(typ)

    return _func


async def depends_db_sess():
    async with smaker.begin() as s:
        try:
            yield s
        except Exception:
            await s.rollback()
            raise


async def depends_current_user(
    request: Request,
    db_sess: AsyncSession = Depends(depends_db_sess),
    jwt_service: JWTService = Depends(depends_object(JWTService)),
    user_service: UserService = Depends(depends_object(UserService)),
) -> UserResponse | None:
    token = request.cookies.get(COOKIE_ALIAS)
    if token is None:
        return None
    try:
        payload = jwt_service.decode(token)
    except JWTException:
        return None
    return await user_service.get_user(payload.sub, db_sess)

async def depends_jwt(req: Request, db_sess: AsyncSession = Depends(depends_db_sess)):
    """Verify the JWT token from the request cookies"""
    token = req.cookies.get(COOKIE_ALIAS)

    if not token:
        raise JWTException("Authentication token is missing")

    object_registry: ObjectRegistry = req.app.state.object_registry
    jwt_service = object_registry.get(JWTService)
    return await jwt_service.validate_jwt(token, db_sess)


async def depends_auth(
    current_user: UserResponse | None = Depends(depends_current_user),
) -> UserResponse:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user
