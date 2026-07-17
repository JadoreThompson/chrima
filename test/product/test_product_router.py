from uuid import uuid4

import pytest

from chrima.workspace.enums import MessagePlatformType
from chrima.tokens.enums import TokenChain, TokenStandard
from core.db import get_db_session


async def _setup(
    client,
    user_service,
    pw_hasher,
    workspace_service,
    workspace_wallet_service,
    token_service,
    faker,
):
    username = faker.user_name()
    email = faker.email()
    password = "test_pass_123"

    wallet_id = None
    async with get_db_session() as db_sess:
        owner = await user_service.create(
            username=username,
            email=email,
            password=pw_hasher.hash(password),
            db_sess=db_sess,
        )
        workspace = await workspace_service.create(
            user_id=owner.id,
            name="product-ws",
            platform=MessagePlatformType.DISCORD,
            external_id="ext_product",
            notification_channel_id="ch_product",
            db_sess=db_sess,
        )
        token = await token_service.create(
            name="TST",
            standard=TokenStandard.ERC_20,
            chain=TokenChain.ETH,
            address="0xtoken",
            db_sess=db_sess,
        )
        wallet = await workspace_wallet_service.create(
            workspace_id=workspace.id,
            name="main",
            wallet_address="0xwallet",
            token_ids=[token.id],
            db_sess=db_sess,
        )
        wallet_id = wallet.id
        await db_sess.commit()

    await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    await client.post(
        "/auth/select-workspace", json={"workspace_id": str(workspace.id)}
    )

    return workspace, wallet_id


@pytest.mark.asyncio(loop_scope="session")
class TestCreateProduct:

    async def test_201_creates_product(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/products/",
            json={
                "name": "test-product",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 19.99,
                    "active": True,
                },
            },
        )

        assert rsp.status_code == 201
        data = rsp.json()
        assert data["name"] == "test-product"
        assert data["fulfilment_type"] == "role"
        assert data["wallet_id"] == str(wallet_id)

    async def test_201_invite_fulfilment(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/products/",
            json={
                "name": "invite-product",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "invite",
                "external_url": "https://discord.gg/test",
                "roles": ["member"],
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 5.0,
                    "active": True,
                },
            },
        )

        assert rsp.status_code == 201
        data = rsp.json()
        assert data["fulfilment_type"] == "invite"
        assert data["external_url"] == "https://discord.gg/test"
        assert data["roles"] == ["member"]

    async def test_201_with_recurring_price(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/products/",
            json={
                "name": "sub-product",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
                "price": {
                    "type": "recurring",
                    "currency": "usd",
                    "amount": 9.99,
                    "active": True,
                    "recurring_interval": "month",
                    "recurring_interval_count": 1,
                },
            },
        )

        assert rsp.status_code == 201

    async def test_422_on_missing_name(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/products/",
            json={
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        assert rsp.status_code == 422

    async def test_422_on_missing_wallet_id(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/products/",
            json={
                "name": "test",
                "fulfilment_type": "role",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        assert rsp.status_code == 422

    async def test_422_on_invalid_fulfilment_type(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/products/",
            json={
                "name": "test",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "invalid_type",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        assert rsp.status_code == 422

    async def test_422_on_missing_price(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/products/",
            json={
                "name": "test",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
            },
        )
        assert rsp.status_code == 422

    async def test_422_on_invalid_price_type(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/products/",
            json={
                "name": "test",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
                "price": {
                    "type": "bad_type",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        assert rsp.status_code == 422

    async def test_422_on_empty_body(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.post("/products/", json={})
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.post(
            "/products/",
            json={
                "name": "test",
                "wallet_id": str(uuid4()),
                "fulfilment_type": "role",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestGetProduct:

    async def test_200_returns_product(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        create_rsp = await client.post(
            "/products/",
            json={
                "name": "get-test",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        product_id = create_rsp.json()["id"]

        rsp = await client.get(f"/products/{product_id}")
        assert rsp.status_code == 200
        assert rsp.json()["name"] == "get-test"

    async def test_404_on_nonexistent(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.get(f"/products/{uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.get("/products/not-a-uuid")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.get(f"/products/{uuid4()}")
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestListProducts:

    async def test_200_returns_list(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp1 = await client.post(
            "/products/",
            json={
                "name": "product-a",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        assert rsp1.status_code == 201
        rsp2 = await client.post(
            "/products/",
            json={
                "name": "product-b",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "invite",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 5.0,
                    "active": True,
                },
            },
        )
        assert rsp2.status_code == 201

        rsp = await client.get("/products/?limit=10")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["size"] >= 2

    async def test_200_empty_when_no_products(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.get("/products/")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["size"] == 0

    async def test_422_on_invalid_page(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.get("/products/?page=0")
        assert rsp.status_code == 422

    async def test_422_on_excessive_limit(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.get("/products/?limit=200")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.get("/products/")
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestUpdateProduct:

    async def test_200_updates_name(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        create_rsp = await client.post(
            "/products/",
            json={
                "name": "original-name",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        product_id = create_rsp.json()["id"]

        rsp = await client.patch(
            f"/products/{product_id}", json={"name": "updated-name"}
        )
        assert rsp.status_code == 200
        assert rsp.json()["name"] == "updated-name"

    async def test_200_updates_description(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        create_rsp = await client.post(
            "/products/",
            json={
                "name": "desc-test",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        product_id = create_rsp.json()["id"]

        rsp = await client.patch(
            f"/products/{product_id}", json={"description": "new description"}
        )
        assert rsp.status_code == 200
        assert rsp.json()["description"] == "new description"

    async def test_200_on_empty_body_no_changes(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        create_rsp = await client.post(
            "/products/",
            json={
                "name": "nochange",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        product_id = create_rsp.json()["id"]

        rsp = await client.patch(f"/products/{product_id}", json={})
        assert rsp.status_code == 200
        assert rsp.json()["name"] == "nochange"

    async def test_404_on_nonexistent(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.patch(f"/products/{uuid4()}", json={"name": "x"})
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.patch("/products/not-a-uuid", json={"name": "x"})
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.patch(f"/products/{uuid4()}", json={"name": "x"})
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestDeleteProduct:

    async def test_204_deletes_product(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        create_rsp = await client.post(
            "/products/",
            json={
                "name": "to-delete",
                "wallet_id": str(wallet_id),
                "fulfilment_type": "role",
                "price": {
                    "type": "one_time",
                    "currency": "usd",
                    "amount": 10.0,
                    "active": True,
                },
            },
        )
        product_id = create_rsp.json()["id"]

        rsp = await client.delete(f"/products/{product_id}")
        assert rsp.status_code == 204

        get_rsp = await client.get(f"/products/{product_id}")
        assert get_rsp.status_code == 404

    async def test_404_on_nonexistent(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.delete(f"/products/{uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        workspace_wallet_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, wallet_id = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            workspace_wallet_service,
            token_service,
            faker,
        )

        rsp = await client.delete("/products/not-a-uuid")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.delete(f"/products/{uuid4()}")
        assert rsp.status_code == 401
