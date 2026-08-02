from uuid import uuid4

import pytest

from chrima.workspace.enums import MessagePlatformType
from chrima.tokens.enums import TokenChain, TokenStandard
from infra.db import get_db_session


async def _setup(
    client, user_service, pw_hasher, workspace_service, token_service, faker
):
    username = faker.user_name()
    email = faker.email()
    password = "test_pass_123"
    token_id = None

    async with get_db_session() as db_sess:
        owner = await user_service.create(
            username=username,
            email=email,
            password=pw_hasher.hash(password),
            db_sess=db_sess,
        )
        workspace = await workspace_service.create(
            user_id=owner.id,
            name="wallet-ws",
            platform=MessagePlatformType.DISCORD,
            external_id="ext_wallet",
            notification_channel_id="ch_wallet",
            db_sess=db_sess,
        )
        token = await token_service.create(
            name="TST",
            standard=TokenStandard.ERC_20,
            chain=TokenChain.ETH,
            address="0xtoken",
            db_sess=db_sess,
        )
        token_id = token.id
        await db_sess.commit()

    await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    await client.post(
        "/auth/select-workspace", json={"workspace_id": str(workspace.id)}
    )

    return workspace, token_id


@pytest.mark.asyncio(loop_scope="session")
class TestCreateWallet:
    async def test_201_creates_wallet(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/wallets/",
            json={
                "workspace_id": str(ws.id),
                "name": "main-wallet",
                "wallet_address": "0xwallet",
                "token_ids": [str(token_id)],
            },
        )

        assert rsp.status_code == 201
        data = rsp.json()
        assert data["name"] == "main-wallet"
        assert data["wallet_address"] == "0xwallet"
        assert str(token_id) in data["token_ids"]

    async def test_422_on_missing_name(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/wallets/",
            json={
                "workspace_id": str(ws.id),
                "wallet_address": "0xwallet",
                "token_ids": [str(token_id)],
            },
        )
        assert rsp.status_code == 422

    async def test_422_on_missing_token_ids(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/wallets/",
            json={
                "workspace_id": str(ws.id),
                "name": "test",
                "wallet_address": "0xwallet",
            },
        )
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.post(
            "/wallets/",
            json={
                "merchant_id": str(uuid4()),
                "name": "test",
                "wallet_address": "0xwallet",
                "token_ids": [str(uuid4())],
            },
        )
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestGetWallet:
    async def test_200_returns_wallet(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        create_rsp = await client.post(
            "/wallets/",
            json={
                "workspace_id": str(ws.id),
                "name": "get-test",
                "wallet_address": "0xwallet",
                "token_ids": [str(token_id)],
            },
        )
        wallet_id = create_rsp.json()["id"]

        rsp = await client.get(f"/wallets/{wallet_id}")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["name"] == "get-test"

    async def test_404_on_nonexistent(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        rsp = await client.get(f"/wallets/{uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        rsp = await client.get("/wallets/not-a-uuid")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.get(f"/wallets/{uuid4()}")
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestListWallets:
    async def test_200_returns_list(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        await client.post(
            "/wallets/",
            json={
                "workspace_id": str(ws.id),
                "name": "wallet-a",
                "wallet_address": "0xa",
                "token_ids": [str(token_id)],
            },
        )
        await client.post(
            "/wallets/",
            json={
                "workspace_id": str(ws.id),
                "name": "wallet-b",
                "wallet_address": "0xb",
                "token_ids": [str(token_id)],
            },
        )

        rsp = await client.get(f"/wallets/?workspace_id={ws.id}&limit=10")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["size"] >= 2

    async def test_200_empty_when_no_wallets(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        rsp = await client.get(f"/wallets/?workspace_id={ws.id}")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["size"] == 0

    async def test_422_on_invalid_page(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        rsp = await client.get(f"/wallets/?workspace_id={ws.id}&page=0")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.get("/wallets/")
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestDeleteWallet:
    async def test_204_deletes_wallet(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        create_rsp = await client.post(
            "/wallets/",
            json={
                "workspace_id": str(ws.id),
                "name": "to-delete",
                "wallet_address": "0xwallet",
                "token_ids": [str(token_id)],
            },
        )
        wallet_id = create_rsp.json()["id"]

        rsp = await client.delete(f"/wallets/{wallet_id}")
        assert rsp.status_code == 204

        get_rsp = await client.get(f"/wallets/{wallet_id}")
        assert get_rsp.status_code == 404

    async def test_404_on_nonexistent(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        rsp = await client.delete(f"/wallets/{uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, token_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            token_service,
            faker,
        )

        rsp = await client.delete("/wallets/not-a-uuid")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.delete(f"/wallets/{uuid4()}")
        assert rsp.status_code == 401
