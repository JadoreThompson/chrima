from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.user import UserService
from chrima.user.exception import UserNotFoundException

from .exception import InvalidLoginCredentialsException
from .schema import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, *, user_service: UserService, pw_hasher: PasswordHasher):
        self.user_service = user_service
        self.pw_hasher = pw_hasher

    async def register_user(self, request: RegisterRequest, db_sess: AsyncSession):
        return await self.user_service.create_user(
            username=request.username,
            email=request.email,
            password=self.pw_hasher.hash(request.password),
            db_sess=db_sess,
        )

    async def verify_credentials(self, request: LoginRequest, db_sess: AsyncSession):
        try:
            user = await self.user_service.find_user(
                email=request.email, db_sess=db_sess
            )
        except UserNotFoundException:
            raise InvalidLoginCredentialsException()

        try:
            self.pw_hasher.verify(user.password, request.password)
        except Argon2Error:
            raise InvalidLoginCredentialsException()

        return user
