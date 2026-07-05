from uuid import uuid4

import pytest

from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.tokens.exception import TokenNotFoundException
from chrima.tokens.model import Token
from core.db import get_db_session


@pytest.mark.asyncio(loop_scope="session")
class TestCreate:
    async def test_creates_token(self, token_service, create_drop_tables):
        async with get_db_session() as db_sess:
            token = await token_service.create(
                name="USDC",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xusdc",
                db_sess=db_sess,
            )

            assert token.name == "USDC"
            assert token.standard == TokenStandard.ERC_20
            assert token.chain == TokenChain.ETH
            assert token.address == "0xusdc"

            row = await db_sess.get(Token, token.id)
            assert row is not None
            assert row.name == "USDC"

    async def test_creates_multiple_tokens(self, token_service, create_drop_tables):
        async with get_db_session() as db_sess:
            t1 = await token_service.create(
                name="TOKEN_A",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xa",
                db_sess=db_sess,
            )
            t2 = await token_service.create(
                name="TOKEN_B",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xb",
                db_sess=db_sess,
            )

            assert t1.id != t2.id


@pytest.mark.asyncio(loop_scope="session")
class TestGetById:
    async def test_returns_token(self, token_service, create_drop_tables):
        async with get_db_session() as db_sess:
            created = await token_service.create(
                name="DAI",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xdai",
                db_sess=db_sess,
            )

            fetched = await token_service.get_by_id(created.id, db_sess)
            assert fetched.id == created.id
            assert fetched.name == "DAI"
            assert fetched.address == "0xdai"

    async def test_raises_when_not_found(self, token_service, create_drop_tables):
        async with get_db_session() as db_sess:
            with pytest.raises(TokenNotFoundException):
                await token_service.get_by_id(uuid4(), db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestGetTokens:
    async def test_returns_all_tokens(self, token_service, create_drop_tables):
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

            result = await token_service.get_tokens(page=1, limit=10, db_sess=db_sess)
            assert result.page == 1
            assert result.size == 2
            assert result.has_next is False

    async def test_paginates(self, token_service, create_drop_tables):
        async with get_db_session() as db_sess:
            for i in range(3):
                await token_service.create(
                    name=f"T{i}",
                    standard=TokenStandard.ERC_20,
                    chain=TokenChain.ETH,
                    address=f"0x{i}",
                    db_sess=db_sess,
                )

            result = await token_service.get_tokens(page=1, limit=2, db_sess=db_sess)
            assert result.size == 2
            assert result.has_next is True

            result = await token_service.get_tokens(page=2, limit=2, db_sess=db_sess)
            assert result.size == 1
            assert result.has_next is False

    async def test_returns_empty_when_no_tokens(
        self, token_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await token_service.get_tokens(page=1, limit=10, db_sess=db_sess)
            assert result.size == 0
            assert result.has_next is False


@pytest.mark.asyncio(loop_scope="session")
class TestGetByIds:
    async def test_returns_matching_tokens(self, token_service, create_drop_tables):
        async with get_db_session() as db_sess:
            t1 = await token_service.create(
                name="AAA",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xaaa",
                db_sess=db_sess,
            )
            t2 = await token_service.create(
                name="BBB",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xbbb",
                db_sess=db_sess,
            )
            t3 = await token_service.create(
                name="CCC",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xccc",
                db_sess=db_sess,
            )

            result = await token_service.get_by_ids(
                [t1.id, t3.id],
                db_sess=db_sess,
            )
            assert len(result) == 2
            ids = {r.id for r in result}
            assert ids == {t1.id, t3.id}

    async def test_returns_empty_when_none_match(
        self, token_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await token_service.get_by_ids([uuid4(), uuid4()], db_sess=db_sess)
            assert result == []

    async def test_returns_empty_on_empty_list(self, token_service, create_drop_tables):
        async with get_db_session() as db_sess:
            result = await token_service.get_by_ids([], db_sess=db_sess)
            assert result == []
