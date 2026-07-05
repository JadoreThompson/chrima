from uuid import uuid4

import pytest

from chrima.tokens.enums import TokenChain, TokenStandard
from core.db import get_db_session


@pytest.mark.asyncio(loop_scope="session")
class TestGetToken:
    async def test_200_returns_token(self, client, token_service, create_drop_tables):
        async with get_db_session() as db_sess:
            created = await token_service.create(
                name="USDC",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xusdc",
                db_sess=db_sess,
            )
            token_id = created.id

        rsp = await client.get(f"/tokens/{token_id}")
        assert rsp.status_code == 200
        data = rsp.json()

        assert data["name"] == "USDC"
        assert data["standard"] == "erc-20"
        assert data["chain"] == "eth"
        assert data["address"] == "0xusdc"

    async def test_404_on_nonexistent(self, client, create_drop_tables):
        rsp = await client.get(f"/tokens/{uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(self, client, create_drop_tables):
        rsp = await client.get("/tokens/not-a-uuid")
        assert rsp.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
class TestListTokens:
    async def test_200_returns_list(self, client, token_service, create_drop_tables):
        async with get_db_session() as db_sess:
            await token_service.create(
                name="T1",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0x1",
                db_sess=db_sess,
            )
            await token_service.create(
                name="T2",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0x2",
                db_sess=db_sess,
            )

        rsp = await client.get("/tokens/?limit=10")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["size"] >= 2

    async def test_200_empty_when_no_tokens(self, client, create_drop_tables):
        rsp = await client.get("/tokens/")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["size"] == 0

    async def test_422_on_invalid_page(self, client, create_drop_tables):
        rsp = await client.get("/tokens/?page=0")
        assert rsp.status_code == 422

    async def test_422_on_excessive_limit(self, client, create_drop_tables):
        rsp = await client.get("/tokens/?limit=200")
        assert rsp.status_code == 422
