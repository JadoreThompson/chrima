from uuid import UUID

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from argon2.exceptions import VerifyMismatchError

from chrima.monitoring import trace_class
from .enums import Tier
from .exception import (
    IncorrectPasswordException,
    UserNotFoundException,
    UserValidationException,
)
from .model import User
from .schema import UserDto


@trace_class()
class UserService:
    def __init__(self, *, pw_hasher: PasswordHasher):
        self.pw_hasher = pw_hasher

    async def create(
        self, username: str, email: str, password: str, db_sess: AsyncSession
    ) -> User:
        res = await db_sess.execute(select(User).where(User.username == username))
        if res.first():
            raise UserValidationException(
                f"User with username '{username}' already exists"
            )

        res = await db_sess.execute(select(User).where(User.email == email))
        if res.first():
            raise UserValidationException()

        user = User(username=username, email=email, password=password)
        db_sess.add(user)
        await db_sess.flush()
        await db_sess.refresh(user)
        return user

    def _to_dto(self, user: User) -> UserDto:
        return UserDto(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def get_by_id(self, user_id: UUID, db_sess: AsyncSession) -> UserDto:
        user = await self._get_by_id(user_id, db_sess)
        return self._to_dto(user)

    async def find(self, email: str, db_sess: AsyncSession) -> User:
        user = await db_sess.scalar(select(User).where(User.email == email))
        if user is None:
            raise UserNotFoundException()
        return user

    async def get_jwt_token(self, user_id: UUID, db_sess: AsyncSession) -> str | None:
        user = await self._get_by_id(user_id, db_sess)
        return user.jwt_token

    async def set_jwt_token(
        self, user_id: UUID, jwt_token: str | None, db_sess: AsyncSession
    ) -> None:
        user = await self._get_by_id(user_id, db_sess)
        user.jwt_token = jwt_token

    async def set_tier(
        self, user_id: UUID, tier: Tier, db_sess: AsyncSession
    ) -> None:
        user = await self._get_by_id(user_id, db_sess)
        user.tier = tier
        await db_sess.flush()

    async def change_username(
        self, user_id: UUID, new_username: str, db_sess: AsyncSession
    ) -> UserDto:
        user = await self._get_by_id(user_id, db_sess)

        res = await db_sess.execute(
            select(User).where(User.username == new_username, User.id != user_id)
        )
        if res.first():
            raise UserValidationException()

        user.username = new_username
        await db_sess.flush()
        await db_sess.refresh(user)
        return self._to_dto(user)

    async def change_password(
        self, user_id: UUID, old_password: str, new_password: str, db_sess: AsyncSession
    ) -> UserDto:
        user = await self._get_by_id(user_id, db_sess)

        try:
            self.pw_hasher.verify(user.password, old_password)
        except VerifyMismatchError:
            raise IncorrectPasswordException()

        user.password = self.pw_hasher.hash(new_password)
        await db_sess.flush()
        await db_sess.refresh(user)
        return self._to_dto(user)

    async def change_email(
        self, user_id: UUID, new_email: str, db_sess: AsyncSession
    ) -> UserDto:
        user = await self._get_by_id(user_id, db_sess)

        res = await db_sess.execute(
            select(User).where(User.email == new_email, User.id != user_id)
        )
        if res.first():
            raise UserValidationException()

        user.email = new_email
        await db_sess.flush()
        await db_sess.refresh(user)
        return self._to_dto(user)

    async def _get_by_id(self, user_id: UUID, db_sess: AsyncSession) -> User:
        user = await db_sess.get(User, user_id)
        if user is None:
            raise UserNotFoundException()
        return user
