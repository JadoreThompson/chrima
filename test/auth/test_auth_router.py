from uuid import uuid4
import pytest
from config import COOKIE_ALIAS


@pytest.mark.asyncio(loop_scope="session")
class TestRegister:
    async def test_success(self, client, create_drop_tables):
        rsp = await client.post(
            "/auth/register",
            json={"username": "newuser", "email": "new@test.com", "password": "secure_pass_123"},
        )

        assert rsp.status_code == 204
        set_cookie_header = rsp.headers.get("set-cookie")
        assert set_cookie_header is not None
        assert set_cookie_header.startswith(f"{COOKIE_ALIAS}=")

    async def test_422_on_missing_email(self, client, create_drop_tables):
        rsp = await client.post("/auth/register", json={"username": "u", "password": "p"})
        assert rsp.status_code == 422
        assert rsp.headers.get("set-cookie") is None

    async def test_422_on_missing_password(self, client, create_drop_tables):
        rsp = await client.post("/auth/register", json={"username": "u", "email": "e@t.com"})
        assert rsp.status_code == 422
        assert rsp.headers.get("set-cookie") is None

    async def test_422_on_missing_username(self, client, create_drop_tables):
        rsp = await client.post("/auth/register", json={"email": "e@t.com", "password": "p"})
        assert rsp.status_code == 422
        assert rsp.headers.get("set-cookie") is None

    async def test_422_on_empty_body(self, client, create_drop_tables):
        rsp = await client.post("/auth/register", json={})
        assert rsp.status_code == 422
        assert rsp.headers.get("set-cookie") is None

    async def test_sql_injection_in_username(self, client, create_drop_tables):
        rsp = await client.post(
            "/auth/register",
            json={"username": "'; DROP TABLE users; --", "email": "h@t.com", "password": "p"},
        )
        assert rsp.status_code in (204, 422)
        if rsp.status_code == 204:
            assert rsp.headers.get("set-cookie") is not None
        else:
            assert rsp.headers.get("set-cookie") is None

    async def test_xss_in_username(self, client, create_drop_tables):
        rsp = await client.post(
            "/auth/register",
            json={"username": "<script>alert('xss')</script>", "email": "x@t.com", "password": "p"},
        )
        assert rsp.status_code in (204, 422)
        if rsp.status_code == 204:
            assert rsp.headers.get("set-cookie") is not None
        else:
            assert rsp.headers.get("set-cookie") is None

    async def test_oversized_username(self, client, create_drop_tables):
        rsp = await client.post(
            "/auth/register",
            json={"username": "a" * 10000, "email": "b@t.com", "password": "p"},
        )
        assert rsp.status_code in (204, 422)
        if rsp.status_code == 204:
            assert rsp.headers.get("set-cookie") is not None
        else:
            assert rsp.headers.get("set-cookie") is None

    async def test_unicode_username(self, client, create_drop_tables):
        rsp = await client.post(
            "/auth/register",
            json={"username": "héllo𝒳world", "email": "u@t.com", "password": "p"},
        )
        assert rsp.status_code == 204
        assert rsp.headers.get("set-cookie").startswith(f"{COOKIE_ALIAS}=")


@pytest.mark.asyncio(loop_scope="session")
class TestLogin:
    async def _register(self, client):
        return await client.post(
            "/auth/register",
            json={"username": "loginuser", "email": "login@test.com", "password": "test_pass_123"},
        )

    async def test_success(self, client, create_drop_tables):
        await self._register(client)

        rsp = await client.post(
            "/auth/login", json={"email": "login@test.com", "password": "test_pass_123"},
        )

        assert rsp.status_code == 204
        assert rsp.headers.get("set-cookie").startswith(f"{COOKIE_ALIAS}=")

    async def test_422_on_missing_email(self, client, create_drop_tables):
        rsp = await client.post("/auth/login", json={"password": "p"})
        assert rsp.status_code == 422
        assert rsp.headers.get("set-cookie") is None

    async def test_422_on_missing_password(self, client, create_drop_tables):
        rsp = await client.post("/auth/login", json={"email": "t@t.com"})
        assert rsp.status_code == 422
        assert rsp.headers.get("set-cookie") is None

    async def test_422_on_empty_body(self, client, create_drop_tables):
        rsp = await client.post("/auth/login", json={})
        assert rsp.status_code == 422
        assert rsp.headers.get("set-cookie") is None

    async def test_401_on_wrong_password(self, client, create_drop_tables):
        await self._register(client)

        rsp = await client.post(
            "/auth/login", json={"email": "login@test.com", "password": "wrong_password"},
        )

        assert rsp.status_code == 401
        assert rsp.headers.get("set-cookie") is None

    async def test_401_on_nonexistent_user(self, client, create_drop_tables):
        rsp = await client.post(
            "/auth/login", json={"email": "nobody@test.com", "password": "any"},
        )

        assert rsp.status_code == 401
        assert rsp.headers.get("set-cookie") is None


@pytest.mark.asyncio(loop_scope="session")
class TestSelectWorkspace:
    async def _register_and_create_workspace(self, client):
        await client.post(
            "/auth/register",
            json={"username": "wsuser", "email": "ws@test.com", "password": "pass"},
        )

        rsp = await client.post(
            "/workspaces/",
            json={"name": "test-ws", "platform": "discord", "external_id": "ext_123", "notification_channel_id": "ch_1"},
        )
        return rsp

    async def test_success(self, client, create_drop_tables):
        ws_rsp = await self._register_and_create_workspace(client)
        ws_id = ws_rsp.json()["id"]

        rsp = await client.post("/auth/select-workspace", json={"workspace_id": ws_id})

        assert rsp.status_code == 204
        assert rsp.headers.get("set-cookie") is not None

    async def test_422_on_missing_workspace_id(self, client, create_drop_tables):
        await self._register_and_create_workspace(client)
        rsp = await client.post("/auth/select-workspace", json={})
        assert rsp.status_code == 422

    async def test_422_on_invalid_uuid(self, client, create_drop_tables):
        await self._register_and_create_workspace(client)
        rsp = await client.post("/auth/select-workspace", json={"workspace_id": "not-a-uuid"})
        assert rsp.status_code == 422

    async def test_404_on_nonexistent_workspace(self, client, create_drop_tables):
        await self._register_and_create_workspace(client)
        rsp = await client.post("/auth/select-workspace", json={"workspace_id": str(uuid4())})
        assert rsp.status_code == 404
        assert rsp.headers.get("set-cookie") is None

    async def test_401_without_jwt(self, client, create_drop_tables):
        rsp = await client.post("/auth/select-workspace", json={"workspace_id": str(uuid4())})
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestLogout:
    async def test_success(self, client, create_drop_tables):
        await client.post(
            "/auth/register",
            json={"username": "logoutuser", "email": "logout@test.com", "password": "pass"},
        )

        rsp = await client.post("/auth/logout")

        assert rsp.status_code == 200
        assert rsp.json()["message"] == "Logged out"
        set_cookie_header = rsp.headers.get("set-cookie")
        assert set_cookie_header is not None
        assert f"{COOKIE_ALIAS}=" in set_cookie_header
        assert "Max-Age=0" in set_cookie_header or "expires=" in set_cookie_header.lower()

    async def test_401_without_jwt(self, client, create_drop_tables):
        rsp = await client.post("/auth/logout")
        assert rsp.status_code == 401
