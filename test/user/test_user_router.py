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

    async def test_200_returns_workspaces(self, client, create_drop_tables):
        await client.post(
            "/auth/register",
            json={
                "username": "wsuser",
                "email": "ws@example.com",
                "password": "secure_pass_123",
            },
        )

        create_rsp = await client.post(
            "/workspaces/",
            json={
                "name": "My Workspace",
                "platform": "discord",
                "external_id": "guild_123",
                "notification_channel_id": "ch_456",
            },
        )
        assert create_rsp.status_code == 201
        ws = create_rsp.json()

        rsp = await client.get("/users/me")
        assert rsp.status_code == 200
        data = rsp.json()
        
        assert "workspaces" in data
        assert len(data["workspaces"]) == 1
        assert data["workspaces"][0]["id"] == ws["id"]
        assert data["workspaces"][0]["name"] == "My Workspace"
