from uuid import uuid4

import pytest


async def _register(client):
    rsp = await client.post(
        "/auth/register",
        json={
            "username": f"user_{uuid4().hex[:8]}",
            "email": f"{uuid4().hex[:8]}@example.com",
            "password": "secure_pass_123",
        },
    )
    assert rsp.status_code == 204
    return rsp


@pytest.mark.asyncio(loop_scope="session")
class TestCreateCheckoutSession:
    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.post("/billing/checkout-session", json={"tier": "pro"})
        assert rsp.status_code == 401

    async def test_422_on_invalid_tier(self, client, create_drop_tables):
        await _register(client)
        rsp = await client.post("/billing/checkout-session", json={"tier": "invalid"})
        assert rsp.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
class TestCancelSubscription:
    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.post("/billing/cancel-subscription")
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestWebhook:
    async def test_400_on_missing_signature(self, client, create_drop_tables):
        rsp = await client.post("/billing/webhook", content=b"{}")
        assert rsp.status_code == 400
