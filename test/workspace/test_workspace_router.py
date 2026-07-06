from uuid import uuid4

import pytest


async def _register(client):
    await client.post(
        "/auth/register",
        json={"username": "wsuser", "email": "ws@test.com", "password": "pass"},
    )


@pytest.mark.asyncio(loop_scope="session")
class TestCreateWorkspace:

    async def test_201_creates_workspace(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.post(
            "/workspaces/",
            json={
                "name": "my-workspace",
                "platform": "discord",
                "external_id": "ext_001",
                "notification_channel_id": "ch_001",
            },
        )

        assert rsp.status_code == 201
        data = rsp.json()
        assert data["name"] == "my-workspace"
        assert data["platform"] == "discord"
        assert data["external_id"] == "ext_001"
        assert data["notification_channel_id"] == "ch_001"

    async def test_422_on_missing_name(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.post(
            "/workspaces/",
            json={
                "platform": "discord",
                "external_id": "ext",
                "notification_channel_id": "ch",
            },
        )
        assert rsp.status_code == 422

    async def test_422_on_invalid_platform(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.post(
            "/workspaces/",
            json={
                "name": "test",
                "platform": "telegram",
                "external_id": "ext",
                "notification_channel_id": "ch",
            },
        )
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.post(
            "/workspaces/",
            json={
                "name": "test",
                "platform": "discord",
                "external_id": "ext",
                "notification_channel_id": "ch",
            },
        )
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestGetWorkspace:

    async def _create_workspace(self, client):
        rsp = await client.post(
            "/workspaces/",
            json={
                "name": "get-test",
                "platform": "discord",
                "external_id": "ext_get",
                "notification_channel_id": "ch_get",
            },
        )
        return rsp.json()["id"]

    async def test_200_returns_workspace(self, client, create_drop_tables):
        await _register(client)
        ws_id = await self._create_workspace(client)

        rsp = await client.get(f"/workspaces/{ws_id}")
        assert rsp.status_code == 200
        assert rsp.json()["name"] == "get-test"

    async def test_404_on_nonexistent(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.get(f"/workspaces/{uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.get("/workspaces/not-a-uuid")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.get(f"/workspaces/{uuid4()}")
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestListWorkspaces:

    async def test_200_returns_list(self, client, create_drop_tables):
        await _register(client)

        await client.post(
            "/workspaces/",
            json={
                "name": "ws-a",
                "platform": "discord",
                "external_id": "ext_a",
                "notification_channel_id": "ch_a",
            },
        )
        await client.post(
            "/workspaces/",
            json={
                "name": "ws-b",
                "platform": "discord",
                "external_id": "ext_b",
                "notification_channel_id": "ch_b",
            },
        )

        rsp = await client.get("/workspaces/?limit=10")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["size"] >= 2

    async def test_200_empty_when_no_workspaces(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.get("/workspaces/")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["size"] == 0

    async def test_422_on_invalid_page(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.get("/workspaces/?page=0")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.get("/workspaces/")
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestUpdateWorkspace:

    async def test_200_updates_name(self, client, create_drop_tables):
        await _register(client)

        create_rsp = await client.post(
            "/workspaces/",
            json={
                "name": "original",
                "platform": "discord",
                "external_id": "ext_upd",
                "notification_channel_id": "ch_upd",
            },
        )
        ws_id = create_rsp.json()["id"]

        rsp = await client.patch(f"/workspaces/{ws_id}", json={"name": "updated"})
        assert rsp.status_code == 200
        assert rsp.json()["name"] == "updated"

    async def test_200_updates_channel_id(self, client, create_drop_tables):
        await _register(client)

        create_rsp = await client.post(
            "/workspaces/",
            json={
                "name": "ch-test",
                "platform": "discord",
                "external_id": "ext_ch",
                "notification_channel_id": "old_ch",
            },
        )
        ws_id = create_rsp.json()["id"]

        rsp = await client.patch(
            f"/workspaces/{ws_id}", json={"notification_channel_id": "new_ch"}
        )
        assert rsp.status_code == 200
        assert rsp.json()["notification_channel_id"] == "new_ch"

    async def test_422_on_empty_body(self, client, create_drop_tables):
        await _register(client)

        create_rsp = await client.post(
            "/workspaces/",
            json={
                "name": "empty-test",
                "platform": "discord",
                "external_id": "ext_emp",
                "notification_channel_id": "ch_emp",
            },
        )
        ws_id = create_rsp.json()["id"]

        rsp = await client.patch(f"/workspaces/{ws_id}", json={})
        assert rsp.status_code == 422

    async def test_404_on_nonexistent(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.patch(f"/workspaces/{uuid4()}", json={"name": "x"})
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.patch("/workspaces/not-a-uuid", json={"name": "x"})
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.patch(f"/workspaces/{uuid4()}", json={"name": "x"})
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestDeleteWorkspace:

    async def test_204_deletes_workspace(self, client, create_drop_tables):
        await _register(client)

        create_rsp = await client.post(
            "/workspaces/",
            json={
                "name": "to-delete",
                "platform": "discord",
                "external_id": "ext_del",
                "notification_channel_id": "ch_del",
            },
        )
        ws_id = create_rsp.json()["id"]

        rsp = await client.delete(f"/workspaces/{ws_id}")
        assert rsp.status_code == 204

        get_rsp = await client.get(f"/workspaces/{ws_id}")
        assert get_rsp.status_code == 404

    async def test_404_on_nonexistent(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.delete(f"/workspaces/{uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(self, client, create_drop_tables):
        await _register(client)

        rsp = await client.delete("/workspaces/not-a-uuid")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.delete(f"/workspaces/{uuid4()}")
        assert rsp.status_code == 401
