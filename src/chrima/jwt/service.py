import logging
from datetime import timedelta
from uuid import UUID

import jwt
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from chrima.user import UserService
from chrima.user.exception import UserNotFoundException
from config import (
    COOKIE_ALIAS,
    IS_PRODUCTION,
    JWT_ALGO,
    JWT_EXPIRY_SECS,
    JWT_SECRET,
)
from util import get_datetime
from .exception import JWTException
from .schema import JWTPayload


class JWTService:
    def __init__(
        self,
        *,
        user_service: UserService,
        jwt_secret: str = JWT_SECRET,
        jwt_algo: str = JWT_ALGO,
        jwt_expiry_secs: int = JWT_EXPIRY_SECS,
        cookie_alias: str = COOKIE_ALIAS,
        is_production: bool = IS_PRODUCTION,
    ):
        self.user_service = user_service
        self._jwt_secret = jwt_secret
        self._jwt_algo = jwt_algo
        self._jwt_expiry_secs = jwt_expiry_secs
        self._cookie_alias = cookie_alias
        self._is_production = is_production
        self._logger = logging.getLogger("jwt_service")

    def _generate_expiry(self) -> float:
        return (get_datetime() + timedelta(seconds=self._jwt_expiry_secs)).timestamp()

    def encode(self, *, sub: UUID, em: str, workspace_id: UUID | None = None) -> str:
        payload = JWTPayload(
            sub=sub,
            em=em,
            workspace_id=workspace_id,
            exp=self._generate_expiry(),
        )
        return jwt.encode(
            payload.model_dump(mode="json"), self._jwt_secret, algorithm=self._jwt_algo
        )

    def decode(self, token: str) -> JWTPayload:
        try:
            return JWTPayload(
                **jwt.decode(
                    token,
                    self._jwt_secret,
                    algorithms=[self._jwt_algo],
                )
            )
        except jwt.ExpiredSignatureError:
            raise JWTException("Token has expired")
        except jwt.InvalidTokenError:
            raise JWTException("Invalid token")

    def set_cookie(
        self, rsp: Response, sub: UUID, em: str, workspace_id: UUID | None = None
    ) -> str:
        """_summary_

        Args:
            rsp (Response): _description_
            sub (UUID): _description_
            em (str): _description_

        Returns:
            str: Token
        """
        token = self.encode(sub=sub, em=em, workspace_id=workspace_id)
        rsp.set_cookie(
            self._cookie_alias,
            token,
            httponly=True,
            secure=self._is_production,
            expires=self._generate_expiry(),
        )
        return token

    def remove_cookie(self, rsp: Response | None = None) -> Response:
        if rsp is None:
            rsp = Response()
        rsp.delete_cookie(
            self._cookie_alias,
            httponly=True,
            secure=self._is_production,
        )
        return rsp

    def decode_jwt(self, token: str) -> JWTPayload:
        try:
            return JWTPayload(
                **jwt.decode(
                    token,
                    self._jwt_secret,
                    algorithms=[self._jwt_algo],
                )
            )
        except jwt.ExpiredSignatureError:
            raise JWTException("Token has expired")
        except jwt.InvalidTokenError:
            raise JWTException("Invalid token")

    async def validate_jwt(self, token: str, db_sess: AsyncSession) -> JWTPayload:
        """Validate a JWT token and ensure the User exists

        Args:
            token (str): JWT token to validate.

        Raises:
            JWTException: No user found adhering to the constraints.

        Returns:
            JWTPayload: Original payload
        """
        payload = self.decode_jwt(token)

        if payload.exp < get_datetime().timestamp():
            raise JWTException("Expired jwt token")

        try:
            existing_token = await self.user_service.get_jwt_token(payload.sub, db_sess)
            if existing_token is None or existing_token != token:
                raise JWTException("Invalid jwt token")
        except UserNotFoundException:
            raise JWTException("Invalid jwt token")

        return payload
