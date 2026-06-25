from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.api.deps import depends_db_sess, depends_jwt, depends_object
from chrima.jwt.schema import JWTPayload
from chrima.user import UserService
from chrima.user.schema import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def me(
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
    user_service: UserService = Depends(depends_object(UserService)),
):
    return await user_service.get_user(jwt.sub, db_sess)
