from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import Response

from chrima.jwt.exception import JWTException
from chrima.jwt.service import JWTService
from config import COOKIE_ALIAS
from infra.db import get_db_session


@pytest.fixture
def jwt_service_mock_user_service():
    return JWTService(user_service=MagicMock())


class TestEncodeDecode:
    def test_roundtrip(self, jwt_service_mock_user_service):
        sub = uuid4()
        token = jwt_service_mock_user_service.encode(sub=sub, em="user@test.com")
        payload = jwt_service_mock_user_service.decode(token)
        assert payload.sub == sub
        assert payload.em == "user@test.com"
        assert payload.workspace_id is None
        assert isinstance(payload.exp, float)

    def test_with_workspace_id(self, jwt_service_mock_user_service):
        sub = uuid4()
        ws_id = uuid4()
        token = jwt_service_mock_user_service.encode(
            sub=sub, em="ws@test.com", workspace_id=ws_id
        )
        payload = jwt_service_mock_user_service.decode(token)
        assert payload.workspace_id == ws_id

    def test_expired_token_raises(self, jwt_service_mock_user_service):
        short = JWTService(user_service=MagicMock(), jwt_expiry_secs=0)
        token = short.encode(sub=uuid4(), em="x@y.com")
        with pytest.raises(JWTException, match="Token has expired"):
            jwt_service_mock_user_service.decode(token)

    def test_invalid_signature_raises(self, jwt_service_mock_user_service):
        other = JWTService(user_service=MagicMock(), jwt_secret="different-secret")
        token = other.encode(sub=uuid4(), em="x@y.com")
        with pytest.raises(JWTException, match="Invalid token"):
            jwt_service_mock_user_service.decode(token)

    def test_garbage_string_raises(self, jwt_service_mock_user_service):
        with pytest.raises(JWTException, match="Invalid token"):
            jwt_service_mock_user_service.decode("not.a.token")

    def test_decode_jwt_matches_decode(self, jwt_service_mock_user_service):
        sub = uuid4()
        token = jwt_service_mock_user_service.encode(sub=sub, em="match@test.com")
        assert (
            jwt_service_mock_user_service.decode(token).sub
            == jwt_service_mock_user_service.decode_jwt(token).sub
        )


class TestCookie:
    def test_set_cookie_sets_httponly(self, jwt_service_mock_user_service):
        rsp = Response()
        jwt_service_mock_user_service.set_cookie(rsp, sub=uuid4(), em="cookie@test.com")
        cookie = rsp.headers.get("set-cookie")
        assert cookie is not None
        assert f"{COOKIE_ALIAS}=" in cookie
        assert "HttpOnly" in cookie or "httponly" in cookie

    def test_set_cookie_returns_decodable_token(self, jwt_service_mock_user_service):
        rsp = Response()
        sub = uuid4()
        token = jwt_service_mock_user_service.set_cookie(
            rsp, sub=sub, em="return@test.com"
        )
        payload = jwt_service_mock_user_service.decode(token)
        assert payload.sub == sub
        assert payload.em == "return@test.com"

    def test_remove_cookie_deletes(self, jwt_service_mock_user_service):
        rsp = Response()
        jwt_service_mock_user_service.remove_cookie(rsp)
        cookie = rsp.headers.get("set-cookie")
        assert cookie is not None
        assert f"{COOKIE_ALIAS}=" in cookie
        assert "Max-Age=0" in cookie

    def test_remove_cookie_creates_response(self, jwt_service_mock_user_service):
        rsp = jwt_service_mock_user_service.remove_cookie()
        assert isinstance(rsp, Response)
        assert f"{COOKIE_ALIAS}=" in rsp.headers.get("set-cookie", "")


@pytest.mark.asyncio(loop_scope="session")
class TestValidate:
    async def test_valid_token_with_real_user(
        self, jwt_service, create_drop_tables, user_service, faker
    ):
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username=faker.user_name(),
                email=faker.email(),
                password="h",
                db_sess=db_sess,
            )
            token = jwt_service.encode(sub=user.id, em=user.email)
            await user_service.set_jwt_token(user.id, token, db_sess)
            await db_sess.commit()

        async with get_db_session() as db_sess:
            payload = await jwt_service.validate_jwt(token, db_sess)
        assert payload.sub == user.id
        assert payload.em == user.email

    async def test_rejects_wrong_token(
        self, jwt_service, create_drop_tables, user_service, faker
    ):
        async with get_db_session() as db_sess:
            user = await user_service.create(
                username=faker.user_name(),
                email=faker.email(),
                password="h",
                db_sess=db_sess,
            )
            correct = jwt_service.encode(sub=user.id, em=user.email)
            await user_service.set_jwt_token(user.id, correct, db_sess)
            wrong = jwt_service.encode(sub=user.id, em=user.email)
            await db_sess.commit()

        async with get_db_session() as db_sess:
            with pytest.raises(JWTException, match="Invalid jwt token"):
                await jwt_service.validate_jwt(wrong, db_sess)

    async def test_rejects_nonexistent_user(self, jwt_service, create_drop_tables):
        token = jwt_service.encode(sub=uuid4(), em="ghost@test.com")
        async with get_db_session() as db_sess:
            with pytest.raises(JWTException, match="Invalid jwt token"):
                await jwt_service.validate_jwt(token, db_sess)
