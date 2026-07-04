from uuid import UUID

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .exception import UserNotFoundException
from .model import User
from .schema import UserResponse


class UserService:
    def __init__(self, *, pw_hasher: PasswordHasher):
        self.pw_hasher = pw_hasher

    async def create(
        self, username: str, email: str, password: str, db_sess: AsyncSession
    ) -> User:
        user = User(username=username, email=email, password=password)
        db_sess.add(user)
        await db_sess.flush()
        await db_sess.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID, db_sess: AsyncSession) -> UserResponse:
        user = await self._get_by_id(user_id, db_sess)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def find(self, email: str, db_sess: AsyncSession) -> User:
        user = await db_sess.scalar(select(User).where(User.email == email))
        if user is None:
            raise UserNotFoundException()
        return user

    async def set_jwt_token(
        self, user_id: UUID, jwt_token: str | None, db_sess: AsyncSession
    ) -> None:
        user = await self._get_by_id(user_id, db_sess)
        user.jwt_token = jwt_token

    async def _get_by_id(self, user_id: UUID, db_sess: AsyncSession) -> User:
        user = await db_sess.get(User, user_id)
        if user is None:
            raise UserNotFoundException()
        return user
