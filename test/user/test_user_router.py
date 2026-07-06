import pytest


@pytest.mark.asyncio(loop_scope="session")
class TestMe:

    async def test_200_returns_current_user(self, client, create_drop_tables):
        await client.post(
            "/auth/register",
            json={
                "username": "currentuser",
                "email": "current@test.com",
                "password": "secure_pass_123",
            },
        )

        rsp = await client.get("/users/me")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["username"] == "currentuser"
        assert data["email"] == "current@test.com"

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.get("/users/me")
        assert rsp.status_code == 401
