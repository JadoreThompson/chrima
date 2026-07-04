from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from chrima.auth.exception import InvalidLoginCredentialsException
from chrima.auth.schema import LoginRequest, RegisterRequest
from chrima.auth.service import AuthService
from chrima.user.exception import UserNotFoundException
from chrima.user.service import UserService


@pytest.fixture
def user_service():
    svc = MagicMock(spec=UserService)
    svc.create = AsyncMock()
    svc.find = AsyncMock()
    return svc


@pytest.fixture
def pw_hasher():
    return MagicMock(spec=PasswordHasher)


@pytest.fixture
def auth_service(user_service, pw_hasher):
    return AuthService(user_service=user_service, pw_hasher=pw_hasher)


@pytest.fixture
def db_sess():
    return AsyncMock()


@pytest.fixture
def stored_user():
    return MagicMock(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        password="hashed_password_value",
    )


@pytest.fixture
def created_user():
    return MagicMock(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
    )


@pytest.mark.asyncio(loop_scope="session")
class TestRegisterUser:
    async def test_registers_user_successfully(
        self, auth_service, user_service, pw_hasher, db_sess, created_user
    ):
        pw_hasher.hash.return_value = "hashed_password"
        user_service.create.return_value = created_user

        request = RegisterRequest(
            username="testuser", email="test@example.com", password="plain_pw"
        )
        result = await auth_service.register_user(request, db_sess)

        pw_hasher.hash.assert_called_once_with("plain_pw")
        user_service.create.assert_called_once_with(
            username="testuser",
            email="test@example.com",
            password="hashed_password",
            db_sess=db_sess,
        )
        assert result.id == created_user.id

    async def test_hashes_password_before_creating_user(
        self, auth_service, user_service, pw_hasher, db_sess, created_user
    ):
        pw_hasher.hash.return_value = "hashed_pw"
        user_service.create.return_value = created_user

        request = RegisterRequest(username="u", email="u@t.com", password="raw")
        await auth_service.register_user(request, db_sess)

        pw_hasher.hash.assert_called_once_with("raw")
        user_service.create.assert_called_once_with(
            username="u", email="u@t.com", password="hashed_pw", db_sess=db_sess
        )


@pytest.mark.asyncio(loop_scope="session")
class TestVerifyCredentials:
    async def test_verifies_with_correct_credentials(
        self, auth_service, user_service, pw_hasher, db_sess, stored_user
    ):
        user_service.find.return_value = stored_user

        request = LoginRequest(email="test@example.com", password="correct_pw")
        result = await auth_service.verify_credentials(request, db_sess)

        user_service.find.assert_called_once_with(
            email="test@example.com", db_sess=db_sess
        )
        pw_hasher.verify.assert_called_once_with("hashed_password_value", "correct_pw")
        assert result.id == stored_user.id
        assert result.email == "test@example.com"

    async def test_raises_when_user_not_found(
        self, auth_service, user_service, pw_hasher, db_sess
    ):
        user_service.find.side_effect = UserNotFoundException()

        request = LoginRequest(email="unknown@test.com", password="pw")
        with pytest.raises(InvalidLoginCredentialsException):
            await auth_service.verify_credentials(request, db_sess)

        pw_hasher.verify.assert_not_called()

    async def test_raises_on_wrong_password(
        self, auth_service, user_service, pw_hasher, db_sess, stored_user
    ):
        user_service.find.return_value = stored_user
        pw_hasher.verify.side_effect = VerifyMismatchError()

        request = LoginRequest(email="test@example.com", password="wrong_pw")
        with pytest.raises(InvalidLoginCredentialsException):
            await auth_service.verify_credentials(request, db_sess)

        pw_hasher.verify.assert_called_once()
