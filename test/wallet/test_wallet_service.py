from uuid import uuid4

import pytest
from sqlalchemy import select

from chrima.workspace.enums import MessagePlatformType
from chrima.price.enums import Currency, PriceType
from chrima.price.schema import CreatePriceRequest
from chrima.product.enums import FulfilmentType
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.wallet.model import Wallet, WalletTokens
from chrima.wallet.exception import WalletNotFoundException, WalletInUseException
from core.db import get_db_session


@pytest.fixture
def setup_workspace_token(
    user_service,
    workspace_service,
    token_service,
    faker,
):
    async def _setup():
        async with get_db_session() as db_sess:
            owner = await user_service.create(
                username=faker.user_name(),
                email=faker.email(),
                password=faker.password(),
                db_sess=db_sess,
            )
            workspace = await workspace_service.create(
                user_id=owner.id,
                name=faker.user_name() + "-ws",
                platform=MessagePlatformType.DISCORD,
                external_id=str(uuid4().int)[:18],
                notification_channel_id="ch_test",
                db_sess=db_sess,
            )
            token = await token_service.create(
                name="TST",
                standard=TokenStandard.ERC_20,
                chain=TokenChain.ETH,
                address="0xtoken",
                db_sess=db_sess,
            )
            await db_sess.commit()
            return workspace, token

    return _setup


@pytest.mark.asyncio(loop_scope="session")
class TestCreate:

    async def test_creates_wallet(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            wallet = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="main-wallet",
                wallet_address="0xwallet",
                token_ids=[token.id],
                db_sess=db_sess,
            )

            assert wallet.name == "main-wallet"
            assert wallet.wallet_address == "0xwallet"
            assert wallet.token_ids == [token.id]

            row = await db_sess.get(Wallet, wallet.id)
            assert row is not None

            wt = await db_sess.scalar(
                select(WalletTokens).where(
                    WalletTokens.wallet_id == wallet.id,
                    WalletTokens.token_id == token.id,
                )
            )
            assert wt is not None

    async def test_nonexistent_workspace_raises(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            with pytest.raises(Exception):
                await workspace_wallet_service.create(
                    workspace_id=uuid4(),
                    name="wallet",
                    wallet_address="0xwallet",
                    token_ids=[token.id],
                    db_sess=db_sess,
                )

    async def test_nonexistent_token_fails_on_commit(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        with pytest.raises(Exception):
            async with get_db_session() as db_sess:
                await workspace_wallet_service.create(
                    workspace_id=workspace.id,
                    name="wallet",
                    wallet_address="0xwallet",
                    token_ids=[uuid4()],
                    db_sess=db_sess,
                )


@pytest.mark.asyncio(loop_scope="session")
class TestGetById:

    async def test_returns_wallet(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            created = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="get-by-id",
                wallet_address="0xwallet",
                token_ids=[token.id],
                db_sess=db_sess,
            )

            fetched = await workspace_wallet_service.get_by_id(created.id, db_sess)
            assert fetched.id == created.id
            assert fetched.name == "get-by-id"
            assert fetched.token_ids == [token.id]

    async def test_raises_when_not_found(
        self, workspace_wallet_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            with pytest.raises(WalletNotFoundException):
                await workspace_wallet_service.get_by_id(uuid4(), db_sess)


@pytest.mark.asyncio(loop_scope="session")
class TestGet:

    async def test_returns_wallet(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            created = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="get-wallet",
                wallet_address="0xwallet",
                token_ids=[token.id],
                db_sess=db_sess,
            )

            fetched = await workspace_wallet_service.get(
                created.id, workspace.id, db_sess
            )
            assert fetched.id == created.id

    async def test_raises_when_not_found(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            with pytest.raises(WalletNotFoundException):
                await workspace_wallet_service.get(uuid4(), workspace.id, db_sess)

    async def test_raises_when_wrong_workspace(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            created = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="wrong-ws",
                wallet_address="0xwallet",
                token_ids=[token.id],
                db_sess=db_sess,
            )

            with pytest.raises(WalletNotFoundException):
                await workspace_wallet_service.get(created.id, uuid4(), db_sess)

            row = await db_sess.get(Wallet, created.id)
            assert row is not None


@pytest.mark.asyncio(loop_scope="session")
class TestListByWorkspace:

    async def test_returns_wallets(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            w1 = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="wallet-a",
                wallet_address="0xa",
                token_ids=[token.id],
                db_sess=db_sess,
            )
            w2 = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="wallet-b",
                wallet_address="0xb",
                token_ids=[token.id],
                db_sess=db_sess,
            )

            result = await workspace_wallet_service.list_by_workspace(
                workspace.id,
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 2
            assert {w.id for w in result.data} == {w1.id, w2.id}

    async def test_paginates(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            for _ in range(3):
                await workspace_wallet_service.create(
                    workspace_id=workspace.id,
                    name="wallet",
                    wallet_address="0xw",
                    token_ids=[token.id],
                    db_sess=db_sess,
                )

            result = await workspace_wallet_service.list_by_workspace(
                workspace.id,
                page=1,
                limit=2,
                db_sess=db_sess,
            )
            assert result.size == 2
            assert result.has_next is True

    async def test_returns_empty_when_no_wallets(
        self, workspace_wallet_service, create_drop_tables
    ):
        async with get_db_session() as db_sess:
            result = await workspace_wallet_service.list_by_workspace(
                uuid4(),
                page=1,
                limit=10,
                db_sess=db_sess,
            )
            assert result.size == 0


@pytest.mark.asyncio(loop_scope="session")
class TestDelete:

    async def test_deletes_wallet(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            created = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="to-delete",
                wallet_address="0xwallet",
                token_ids=[token.id],
                db_sess=db_sess,
            )

            await workspace_wallet_service.delete(created.id, workspace.id, db_sess)

        async with get_db_session() as db_sess:
            row = await db_sess.get(Wallet, created.id)
            assert row is None

    async def test_raises_when_not_found(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            with pytest.raises(WalletNotFoundException):
                await workspace_wallet_service.delete(uuid4(), workspace.id, db_sess)

    async def test_raises_when_wrong_workspace(
        self, workspace_wallet_service, setup_workspace_token, create_drop_tables
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            created = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="wrong-ws-del",
                wallet_address="0xwallet",
                token_ids=[token.id],
                db_sess=db_sess,
            )

            with pytest.raises(WalletNotFoundException):
                await workspace_wallet_service.delete(created.id, uuid4(), db_sess)

            row = await db_sess.get(Wallet, created.id)
            assert row is not None

    async def test_raises_when_in_use(
        self,
        workspace_wallet_service,
        product_service,
        setup_workspace_token,
        create_drop_tables,
    ):
        workspace, token = await setup_workspace_token()
        async with get_db_session() as db_sess:
            wallet = await workspace_wallet_service.create(
                workspace_id=workspace.id,
                name="in-use",
                wallet_address="0xwallet",
                token_ids=[token.id],
                db_sess=db_sess,
            )

            await product_service.create(
                workspace_id=workspace.id,
                name="using-wallet",
                description=None,
                wallet_id=wallet.id,
                external_url=None,
                roles=None,
                fulfilment_type=FulfilmentType.ROLE,
                price_data=CreatePriceRequest(
                    workspace_id=workspace.id,
                    product_id=uuid4(),
                    type=PriceType.ONE_TIME,
                    currency=Currency.USD,
                    amount=10.0,
                ),
                db_sess=db_sess,
            )

            with pytest.raises(WalletInUseException):
                await workspace_wallet_service.delete(wallet.id, workspace.id, db_sess)

            row = await db_sess.get(Wallet, wallet.id)
            assert row is not None
