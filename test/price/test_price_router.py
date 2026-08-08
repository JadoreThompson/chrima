from uuid import uuid4

import pytest

from chrima.workspace.enums import MessagePlatformType
from chrima.product.enums import FulfilmentType
from chrima.tokens.enums import TokenChain, TokenStandard
from infra.db import get_db_session


async def _setup(
    client,
    user_service,
    pw_hasher,
    workspace_service,
    wallet_service,
    product_service,
    token_service,
    faker,
):
    username = faker.user_name()
    email = faker.email()
    password = "test_pass_123"

    async with get_db_session() as db_sess:
        owner = await user_service.create(
            username=username,
            email=email,
            password=pw_hasher.hash(password),
            db_sess=db_sess,
        )
        workspace = await workspace_service.create(
            user_id=owner.id,
            name="price-ws",
            platform=MessagePlatformType.DISCORD,
            external_id="ext_price",
            notification_channel_id="ch_price",
            db_sess=db_sess,
        )
        token = await token_service.create(
            name="PRI",
            standard=TokenStandard.ERC_20,
            chain=TokenChain.ETH,
            address="0xtoken",
            db_sess=db_sess,
        )
        wallet = await wallet_service.create(
            workspace_id=workspace.id,
            name="main",
            wallet_address="0xwallet",
            db_sess=db_sess,
        )
        product = await product_service.create(
            workspace_id=workspace.id,
            name="test-product",
            description=None,
            wallet_id=wallet.id,
            external_url=None,
            roles=["premium"],
            fulfilment_type=FulfilmentType.ROLE,
            db_sess=db_sess,
        )
        await db_sess.commit()

    await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    await client.post(
        "/auth/select-workspace", json={"workspace_id": str(workspace.id)}
    )

    return workspace, product, token


@pytest.mark.asyncio(loop_scope="session")
class TestCreatePrice:
    async def test_201_creates_price(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/prices/",
            json={
                "workspace_id": str(ws.id),
                "product_id": str(product.id),
                "type": "one_time",
                "currency": "usd",
                "amount": 19.99,
            },
        )

        assert rsp.status_code == 201
        data = rsp.json()
        assert data["product_id"] == str(product.id)
        assert data["amount"] == 19.99
        assert data["type"] == "one_time"
        assert data["currency"] == "usd"

    async def test_201_creates_recurring(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/prices/",
            json={
                "workspace_id": str(ws.id),
                "product_id": str(product.id),
                "type": "recurring",
                "currency": "usd",
                "amount": 5.0,
                "recurring_interval": "month",
                "recurring_interval_count": 1,
                "trial_period_days": 7,
            },
        )

        assert rsp.status_code == 201
        data = rsp.json()
        assert data["type"] == "recurring"
        assert data["recurring_interval"] == "month"
        assert data["recurring_interval_count"] == 1
        assert data["trial_period_days"] == 7

    async def test_422_on_zero_amount(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/prices/",
            json={
                "workspace_id": str(ws.id),
                "product_id": str(product.id),
                "type": "one_time",
                "currency": "usd",
                "amount": 0,
            },
        )
        assert rsp.status_code == 422

    async def test_422_on_negative_amount(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/prices/",
            json={
                "workspace_id": str(ws.id),
                "product_id": str(product.id),
                "type": "one_time",
                "currency": "usd",
                "amount": -5.0,
            },
        )
        assert rsp.status_code == 422

    async def test_422_on_missing_required(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.post("/prices/", json={})
        assert rsp.status_code == 422

    async def test_422_on_invalid_type(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/prices/",
            json={
                "workspace_id": str(ws.id),
                "product_id": str(product.id),
                "type": "invalid_type",
                "currency": "usd",
                "amount": 10.0,
            },
        )
        assert rsp.status_code == 422

    async def test_422_on_invalid_currency(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )

        rsp = await client.post(
            "/prices/",
            json={
                "workspace_id": str(ws.id),
                "product_id": str(product.id),
                "type": "one_time",
                "currency": "gbp",
                "amount": 10.0,
            },
        )
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.post(
            "/prices/",
            json={
                "product_id": str(uuid4()),
                "type": "one_time",
                "currency": "usd",
                "amount": 10.0,
            },
        )
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestGetPrice:
    async def test_200_returns_price(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )

        create_rsp = await client.post(
            "/prices/",
            json={
                "workspace_id": str(ws.id),
                "product_id": str(product.id),
                "type": "one_time",
                "currency": "usd",
                "amount": 15.0,
            },
        )
        price_id = create_rsp.json()["id"]

        rsp = await client.get(f"/prices/{price_id}")
        assert rsp.status_code == 200
        assert rsp.json()["id"] == price_id
        assert rsp.json()["amount"] == 15.0

    async def test_404_on_nonexistent(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.get(f"/prices/{uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.get("/prices/not-a-uuid")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.get(f"/prices/{uuid4()}")
        assert rsp.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
class TestListPrices:
    async def test_200_returns_list(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )

        await client.post(
            "/prices/",
            json={
                "workspace_id": str(ws.id),
                "product_id": str(product.id),
                "type": "one_time",
                "currency": "usd",
                "amount": 10.0,
            },
        )
        await client.post(
            "/prices/",
            json={
                "workspace_id": str(ws.id),
                "product_id": str(product.id),
                "type": "recurring",
                "currency": "usd",
                "amount": 5.0,
                "recurring_interval": "month",
                "recurring_interval_count": 1,
            },
        )

        rsp = await client.get(f"/prices/?product_id={product.id}")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["size"] >= 1

    async def test_200_empty_when_no_prices(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.get(f"/prices/?product_id={uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_missing_product_id(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.get("/prices/")
        assert rsp.status_code == 422

    async def test_422_on_invalid_page(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.get(f"/prices/?product_id={product.id}&page=0")
        assert rsp.status_code == 422

    async def test_422_on_excessive_limit(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.get(f"/prices/?product_id={product.id}&limit=200")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.get(f"/prices/?product_id={uuid4()}")
        assert rsp.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
class TestUpdatePrice:
    async def _create_price(self, client):
        rsp = await client.post(
            "/prices/",
            json={
                "workspace_id": str(self.ws.id),
                "product_id": str(self.product.id),
                "type": "one_time",
                "currency": "usd",
                "amount": 10.0,
            },
        )
        return rsp.json()["id"]

    async def test_200_updates_amount(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        self.ws, self.product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        price_id = await self._create_price(client)

        rsp = await client.patch(f"/prices/{price_id}", json={"amount": 20.0})
        assert rsp.status_code == 200
        assert rsp.json()["amount"] == 20.0

    async def test_200_updates_multiple_fields(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        self.ws, self.product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        price_id = await self._create_price(client)

        rsp = await client.patch(f"/prices/{price_id}", json={"amount": 7.5})
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["amount"] == 7.5

    async def test_422_on_zero_amount(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        self.ws, self.product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        price_id = await self._create_price(client)

        rsp = await client.patch(f"/prices/{price_id}", json={"amount": 0})
        assert rsp.status_code == 422

    async def test_422_on_negative_amount(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        self.ws, self.product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        price_id = await self._create_price(client)

        rsp = await client.patch(f"/prices/{price_id}", json={"amount": -1.0})
        assert rsp.status_code == 422

    async def test_404_on_nonexistent(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.patch(f"/prices/{uuid4()}", json={"amount": 5.0})
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.patch("/prices/not-a-uuid", json={"amount": 5.0})
        assert rsp.status_code == 422

    async def test_200_on_empty_body_no_changes(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        self.ws, self.product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        price_id = await self._create_price(client)

        rsp = await client.patch(f"/prices/{price_id}", json={})
        assert rsp.status_code == 200
        assert rsp.json()["amount"] == 10.0

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.patch(f"/prices/{uuid4()}", json={"amount": 5.0})
        assert rsp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
class TestDeletePrice:
    async def test_204_deletes_price(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )

        create_rsp = await client.post(
            "/prices/",
            json={
                "workspace_id": str(ws.id),
                "product_id": str(product.id),
                "type": "one_time",
                "currency": "usd",
                "amount": 10.0,
            },
        )
        price_id = create_rsp.json()["id"]

        rsp = await client.delete(f"/prices/{price_id}")
        assert rsp.status_code == 204

        get_rsp = await client.get(f"/prices/{price_id}")
        assert get_rsp.status_code == 404

    async def test_404_on_nonexistent(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.delete(f"/prices/{uuid4()}")
        assert rsp.status_code == 404

    async def test_422_on_invalid_uuid(
        self,
        client,
        user_service,
        pw_hasher,
        workspace_service,
        wallet_service,
        product_service,
        token_service,
        faker,
        create_drop_tables,
    ):
        ws, product, token = await _setup(
            client,
            user_service,
            pw_hasher,
            workspace_service,
            wallet_service,
            product_service,
            token_service,
            faker,
        )
        rsp = await client.delete("/prices/not-a-uuid")
        assert rsp.status_code == 422

    async def test_401_without_auth(self, client, create_drop_tables):
        rsp = await client.delete(f"/prices/{uuid4()}")
        assert rsp.status_code == 401
