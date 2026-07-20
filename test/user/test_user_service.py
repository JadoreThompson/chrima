from uuid import uuid4

import pytest

from argon2.exceptions import VerifyMismatchError

from chrima.user.exception import IncorrectPasswordException, UserNotFoundException, UserValidationException
from chrima.user.model import User
from core.db import get_db_session


@pytest.mark.asyncio(loop_scope="session")
class TestCreate:
    async def test_creates_user(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username="testuser",
                email="test@example.com",
                password="secure_pass",
                db_sess=db_sess,
            )

            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.password == "secure_pass"
            assert user.id is not None

            row = await db_sess.get(User, user.id)
            assert row is not None

    async def test_duplicate_username_raises(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            await user_service.create(
                username="dupuser",
                email="first@example.com",
                password="pass",
                db_sess=db_sess,
            )
            with pytest.raises(Exception):
                await user_service.create(
                    username="dupuser",
                    email="second@example.com",
                    password="pass",
                    db_sess=db_sess,
                )

    async def test_duplicate_email_raises(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            await user_service.create(
                username="user_a",
                email="dup@example.com",
                password="pass",
                db_sess=db_sess,
            )
            with pytest.raises(Exception):
                await user_service.create(
                    username="user_b",
                    email="dup@example.com",
                    password="pass",
                    db_sess=db_sess,
                )


@pytest.mark.asyncio(loop_scope="session")
class TestGetById:
    async def test_returns_user(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            created = await user_service.create(
                username="getbyid",
                email="get@example.com",
                password="pass",
                db_sess=db_sess,
            )

            fetched = await user_service.get_by_id(created.id, db_sess)
            assert fetched.id == created.id
            assert fetched.username == "getbyid"
            assert fetched.email == "get@example.com"

    async def test_raises_when_not_found(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(UserNotFoundException):
                await user_service.get_by_id(uuid4(), db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestFind:
    async def test_finds_by_email(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            created = await user_service.create(
                username="findtest",
                email="find@example.com",
                password="pass",
                db_sess=db_sess,
            )

            found = await user_service.find("find@example.com", db_sess)
            assert found.id == created.id
            assert found.username == "findtest"

    async def test_raises_when_not_found(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(UserNotFoundException):
                await user_service.find("nonexistent@example.com", db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestJwtToken:
    async def test_set_and_get_token(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username="jwttest",
                email="jwt@example.com",
                password="pass",
                db_sess=db_sess,
            )

            token = await user_service.get_jwt_token(user.id, db_sess)
            assert token is None

            await user_service.set_jwt_token(user.id, "my_token", db_sess)

            token = await user_service.get_jwt_token(user.id, db_sess)
            assert token == "my_token"

    async def test_clears_token(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username="cleartoken",
                email="clear@example.com",
                password="pass",
                db_sess=db_sess,
            )

            await user_service.set_jwt_token(user.id, "some_token", db_sess)
            await user_service.set_jwt_token(user.id, None, db_sess)

            token = await user_service.get_jwt_token(user.id, db_sess)
            assert token is None

    async def test_raises_when_user_not_found(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(UserNotFoundException):
                await user_service.get_jwt_token(uuid4(), db_sess)

            with pytest.raises(UserNotFoundException):
                await user_service.set_jwt_token(uuid4(), "token", db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestChangeUsername:
    async def test_changes_username(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username="oldname",
                email="test@example.com",
                password="pass",
                db_sess=db_sess,
            )
            updated = await user_service.change_username(
                user.id, "newname", db_sess
            )
            assert updated.username == "newname"

    async def test_duplicate_username_raises(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            await user_service.create(
                username="taken",
                email="a@example.com",
                password="pass",
                db_sess=db_sess,
            )
            user = await user_service.create(
                username="original",
                email="b@example.com",
                password="pass",
                db_sess=db_sess,
            )
            with pytest.raises(UserValidationException):
                await user_service.change_username(user.id, "taken", db_sess)

    async def test_raises_when_user_not_found(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(UserNotFoundException):
                await user_service.change_username(uuid4(), "any", db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestChangePassword:
    async def test_changes_password(self, user_service, pw_hasher, create_drop_tables):
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username="pwtest",
                email="pw@example.com",
                password=pw_hasher.hash("old_pass"),
                db_sess=db_sess,
            )
            await user_service.change_password(
                user.id, "old_pass", "new_pass", db_sess
            )

            row = await db_sess.get(User, user.id)
            assert pw_hasher.verify(row.password, "new_pass")

    async def test_wrong_old_password_raises(
        self, user_service, pw_hasher, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username="pwtest",
                email="pw@example.com",
                password=pw_hasher.hash("old_pass"),
                db_sess=db_sess,
            )
            with pytest.raises(IncorrectPasswordException):
                await user_service.change_password(
                    user.id, "wrong_pass", "new_pass", db_sess
                )

    async def test_raises_when_user_not_found(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(UserNotFoundException):
                await user_service.change_password(uuid4(), "old", "new", db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestChangeEmail:
    async def test_changes_email(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username="emailtest",
                email="old@example.com",
                password="pass",
                db_sess=db_sess,
            )
            updated = await user_service.change_email(
                user.id, "new@example.com", db_sess
            )
            assert updated.email == "new@example.com"

    async def test_duplicate_email_raises(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            await user_service.create(
                username="user_a",
                email="taken@example.com",
                password="pass",
                db_sess=db_sess,
            )
            user = await user_service.create(
                username="user_b",
                email="original@example.com",
                password="pass",
                db_sess=db_sess,
            )
            with pytest.raises(UserValidationException):
                await user_service.change_email(user.id, "taken@example.com", db_sess)

    async def test_raises_when_user_not_found(self, user_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(UserNotFoundException):
                await user_service.change_email(uuid4(), "any@example.com", db_sess)
