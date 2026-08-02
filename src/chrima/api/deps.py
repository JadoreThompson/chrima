from typing import Type

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.object_registry import ObjectRegistry
from chrima.jwt import JWTService, JWTException
from config import COOKIE_ALIAS
from infra.db import smaker
from infra.db.session import get_db_session


def depends_object(typ: Type):
    def _func(req: Request):
        object_registry: ObjectRegistry = req.app.state.object_registry
        return object_registry.get(typ)

    return _func


async def depends_db_sess():
    async with get_db_session() as s:
        yield s


async def depends_jwt(req: Request, db_sess: AsyncSession = Depends(depends_db_sess)):
    token = req.cookies.get(COOKIE_ALIAS)
    if not token:
        raise JWTException("Not authenticated")

    object_registry: ObjectRegistry = req.app.state.object_registry
    jwt_service = object_registry.get(JWTService)
    # return jwt_service.decode(token)
    return await jwt_service.validate_jwt(token, db_sess)
