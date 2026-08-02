import asyncio
import os
from contextlib import asynccontextmanager
from decimal import Decimal

import discord
import pytest
import pytest_asyncio
from sqlalchemy import select
from web3 import AsyncWeb3

from chrima.event_bus.service.outbox import OutboxPoller
from chrima.workspace.enums import MessagePlatformType
from chrima.transaction.service.orchestrator import TransactionOrchestrator
from chrima.price.enums import Currency, PriceType
from chrima.price.event import PriceEventDeserialiser
from chrima.price.service.sync import PriceSyncService
from chrima.product.enums import FulfilmentType
from chrima.product.event import ProductEventDeserialiser
from chrima.product.service.sync import ProductSyncService
from chrima.tokens.enums import TokenChain, TokenStandard
from chrima.transaction.enums import TransactionStatus
from chrima.transaction.event import TransactionEventDeserialiser
from chrima.transaction.model import Transaction
from config import (
    CHRIMA_PAYMENT_CONTRACT_ABI,
    CHRIMA_PAYMENT_CONTRACT_ADDRESS,
    RPC_URL,
    SIGNER_PRIVATE_KEY,
)
from infra.db import get_db_session
from infra.kafka import AsyncKafkaProducer

require_discord = pytest.mark.skipif(
    not os.getenv("DISCORD_GUILD_ID")
    or not os.getenv("DISCORD_USER_ID")
    or not os.getenv("DISCORD_ROLE_1_ID")
    or not os.getenv("DISCORD_ACCESS_TOKEN"),
    reason="Requires DISCORD_ROLE_1_ID, DISCORD_GUILD_ID, DISCORD_USER_ID, DISCORD_ACCESS_TOKEN",
)


@pytest.fixture
def discord_user_id() -> int:
    return int(os.environ["DISCORD_USER_ID"])


@pytest.fixture
def discord_guild_id() -> int:
    return int(os.environ["DISCORD_GUILD_ID"])


@pytest.fixture
def discord_role_id() -> int:
    return int(os.environ["DISCORD_ROLE_1_ID"])


@pytest.fixture
def discord_access_token() -> str:
    return os.environ["DISCORD_ACCESS_TOKEN"]


@pytest_asyncio.fixture(loop_scope="session")
async def kafka_producer():
    producer = AsyncKafkaProducer.create()

    try:
        await producer.start()
        yield producer
    finally:
        await producer.stop()


@pytest.fixture
def price_event_deserialiser():
    return PriceEventDeserialiser()


@pytest.fixture
def product_event_deserialiser():
    return ProductEventDeserialiser()


@pytest.fixture
def outbox_event_poller(
    kafka_producer, price_event_deserialiser, product_event_deserialiser
):
    deserialisers = {
        "price": price_event_deserialiser,
        "product": product_event_deserialiser,
        "transaction": TransactionEventDeserialiser(),
    }
    return OutboxPoller(
        kafka_producer=kafka_producer,
        deserialisers=deserialisers,
        interval=1,
        batch_size=10,
    )


@pytest.fixture
def w3_client():
    return AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URL))


@pytest.fixture
def chrima_payment_contract(w3_client):
    return w3_client.eth.contract(
        address=AsyncWeb3.to_checksum_address(CHRIMA_PAYMENT_CONTRACT_ADDRESS),
        abi=CHRIMA_PAYMENT_CONTRACT_ABI,
    )


@pytest.fixture
def signer_account(w3_client):
    return w3_client.eth.account.from_key(SIGNER_PRIVATE_KEY)


@pytest.fixture
def price_sync_service(w3_client, chrima_payment_contract, price_event_deserialiser):
    return PriceSyncService(
        w3=w3_client,
        contract=chrima_payment_contract,
        signer_private_key=SIGNER_PRIVATE_KEY,
        deserialiser=price_event_deserialiser,
    )


@pytest.fixture
def product_sync_service(
    w3_client, chrima_payment_contract, product_event_deserialiser, wallet_service
):
    return ProductSyncService(
        w3=w3_client,
        contract=chrima_payment_contract,
        signer_private_key=SIGNER_PRIVATE_KEY,
        deserialiser=product_event_deserialiser,
        wallet_service=wallet_service,
    )


@asynccontextmanager
async def _run(coro):
    task = asyncio.create_task(coro)
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def _ensure_not_in_guild(discord_client, guild_id, user_id):
    guild = await discord_client.fetch_guild(guild_id)
    try:
        member = await guild.fetch_member(user_id)
        await guild.kick(member, reason="Chrima integration test cleanup")
    except discord.NotFound:
        pass


async def _ensure_in_guild(discord_client, guild_id, user_id, access_token):
    """Add user to guild via OAuth if not already a member."""
    guild = await discord_client.fetch_guild(guild_id)
    try:
        await guild.fetch_member(user_id)
        return  # Already a member
    except discord.NotFound:
        pass

    from chrima.discord import DiscordMembershipService, DiscordService
    from chrima.encryption import EncryptionService

    ds = DiscordMembershipService(
        discord_client=discord_client,
        discord_service=DiscordService(
            encryption_service=EncryptionService(),
        ),
    )
    await ds.add_user_to_guild(
        guild_id=guild_id,
        user_id=user_id,
        access_token=access_token,
    )


async def _strip_role(discord_client, guild_id, user_id, role_id):
    guild = await discord_client.fetch_guild(guild_id)
    member = await guild.fetch_member(user_id)
    role = guild.get_role(role_id)
    if role and role in member.roles:
        await member.remove_roles(role, reason="Chrima test cleanup")


async def _ensure_role(discord_client, guild_id, user_id, role_id):
    guild = await discord_client.fetch_guild(guild_id)
    member = await guild.fetch_member(user_id)
    role = guild.get_role(role_id)
    if role and role not in member.roles:
        await member.add_roles(role, reason="Chrima test setup")


async def _setup_db(
    user_service,
    workspace_service,
    wallet_service,
    product_service,
    price_service,
    token_service,
    faker,
    discord_guild_id,
    discord_role_id,
):
    """Create user, workspace, wallet, product, and price. Returns all created objects."""
    async with get_db_session() as db_sess:
        user = await user_service.create(
            username=faker.user_name(),
            email=faker.email(),
            password=faker.password(),
            db_sess=db_sess,
        )
        workspace = await workspace_service.create(
            user_id=user.id,
            name="int-ws",
            platform=MessagePlatformType.DISCORD,
            external_id=str(discord_guild_id),
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
        wallet = await wallet_service.create(
            workspace_id=workspace.id,
            name="main",
            wallet_address="0x0000000000000000000000000000000000000001",
            token_ids=[token.id],
            db_sess=db_sess,
        )
        product = await product_service.create(
            workspace_id=workspace.id,
            name="integration-product",
            description=None,
            wallet_id=wallet.id,
            external_url=None,
            roles=[str(discord_role_id)],
            fulfilment_type=FulfilmentType.ROLE,
            db_sess=db_sess,
        )
        price = await price_service.create(
            workspace_id=workspace.id,
            product_id=product.id,
            type=PriceType.ONE_TIME,
            currency=Currency.USD,
            amount=1.0,
            db_sess=db_sess,
        )
        await db_sess.commit()
    return product, price


@pytest.mark.asyncio(loop_scope="session")
async def test_processes_transaction_assigns_roles(
    discord_client: discord.Client,
    discord_service,
    discord_user_id,
    discord_guild_id,
    discord_role_id,
    discord_access_token,
    w3_client,
    chrima_payment_contract,
    signer_account,
    eth_listener,
    transaction_orchestrator: TransactionOrchestrator,
    outbox_event_poller,
    product_service,
    product_sync_service,
    price_service,
    price_sync_service,
    workspace_service,
    wallet_service,
    token_service,
    user_service,
    faker,
    create_drop_tables,
):
    """Creates a product with a 0.01 USD price, triggers processTransaction
    on-chain, waits for the pipeline to process it, then verifies the
    transaction record, subscription balance, on-chain price mapping,
    and Discord role assignment."""

    await _ensure_not_in_guild(discord_client, discord_guild_id, discord_user_id)

    async with get_db_session() as db_sess:
        await discord_service.store_oauth_payload(
            discord_user_id,
            {"access_token": discord_access_token},
            db_sess,
        )
        await db_sess.commit()

    guild = await discord_client.fetch_guild(discord_guild_id)
    assert discord_role_id in [
        r.id for r in guild.roles
    ], f"DISCORD_ROLE_ID {discord_role_id} not found in guild roles"

    async with get_db_session() as db_sess:
        user = await user_service.create(
            username=faker.user_name(),
            email=faker.email(),
            password=faker.password(),
            db_sess=db_sess,
        )

        workspace = await workspace_service.create(
            user_id=user.id,
            name="int-ws",
            platform=MessagePlatformType.DISCORD,
            external_id=str(discord_guild_id),
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

        wallet = await wallet_service.create(
            workspace_id=workspace.id,
            name="main",
            wallet_address="0x0000000000000000000000000000000000000001",
            token_ids=[token.id],
            db_sess=db_sess,
        )

        product = await product_service.create(
            workspace_id=workspace.id,
            name="integration-product",
            description=None,
            wallet_id=wallet.id,
            external_url=None,
            roles=[str(discord_role_id)],
            fulfilment_type=FulfilmentType.ROLE,
            db_sess=db_sess,
        )
        price = await price_service.create(
            workspace_id=workspace.id,
            product_id=product.id,
            type=PriceType.ONE_TIME,
            currency=Currency.USD,
            amount=0.01,
            db_sess=db_sess,
        )
        price_id = price.id
        usdt_amount = int(Decimal(str(price.amount)) * 10**6)

        await db_sess.commit()

    async with _run(outbox_event_poller.run()):
        async with _run(eth_listener.listen()):
            async with _run(transaction_orchestrator.run()):
                async with _run(price_sync_service.run()):
                    async with _run(product_sync_service.run()):
                        # Allow events to be emitted and handled
                        await asyncio.sleep(10)

                        latest_block = await w3_client.eth.get_block("latest")
                        max_fee = int(latest_block["baseFeePerGas"]) * 3
                        priority_fee = w3_client.to_wei(2, "gwei")

                        # Approve USDT spending
                        usdt_address = (
                            await chrima_payment_contract.functions.usdtToken().call()
                        )
                        usdt_token = w3_client.eth.contract(
                            address=AsyncWeb3.to_checksum_address(usdt_address),
                            abi=[
                                {
                                    "constant": False,
                                    "inputs": [
                                        {"name": "_spender", "type": "address"},
                                        {"name": "_value", "type": "uint256"},
                                    ],
                                    "name": "approve",
                                    "outputs": [{"name": "", "type": "bool"}],
                                    "type": "function",
                                },
                                {
                                    "constant": False,
                                    "inputs": [
                                        {"name": "to", "type": "address"},
                                        {"name": "amount", "type": "uint256"},
                                    ],
                                    "name": "mint",
                                    "outputs": [],
                                    "type": "function",
                                },
                            ],
                        )

                        # Mint USDT to signer
                        mint_amount = 1_000_000 * 10**6
                        mint_tx = await usdt_token.functions.mint(
                            signer_account.address, mint_amount
                        ).build_transaction(
                            {
                                "from": signer_account.address,
                                "nonce": await w3_client.eth.get_transaction_count(
                                    signer_account.address, "pending"
                                ),
                                "maxFeePerGas": max_fee,
                                "maxPriorityFeePerGas": priority_fee,
                            }
                        )
                        signed_mint = signer_account.sign_transaction(mint_tx)
                        mint_hash = await w3_client.eth.send_raw_transaction(
                            signed_mint.raw_transaction
                        )
                        mint_receipt = await w3_client.eth.wait_for_transaction_receipt(
                            mint_hash
                        )
                        assert mint_receipt["status"] == 1, "USDT mint failed"

                        approve_tx = await usdt_token.functions.approve(
                            chrima_payment_contract.address,
                            # 2**256 - 1,
                            usdt_amount,
                        ).build_transaction(
                            {
                                "from": signer_account.address,
                                "nonce": await w3_client.eth.get_transaction_count(
                                    signer_account.address, "pending"
                                ),
                                "maxFeePerGas": max_fee,
                                "maxPriorityFeePerGas": priority_fee,
                            }
                        )
                        signed_approve = signer_account.sign_transaction(approve_tx)
                        approve_hash = await w3_client.eth.send_raw_transaction(
                            signed_approve.raw_transaction
                        )
                        approve_receipt = (
                            await w3_client.eth.wait_for_transaction_receipt(
                                approve_hash
                            )
                        )
                        print(
                            f"\nAPPROVE RECEIPT: {approve_hash.hex()} status={approve_receipt['status']}"
                        )
                        assert approve_receipt["status"] == 1, "USDT approve failed"

                        await asyncio.sleep(2)

                        tx = await chrima_payment_contract.functions.processTransaction(
                            str(product.id),
                            str(price_id),
                            str(discord_user_id),
                        ).build_transaction(
                            {
                                "from": signer_account.address,
                                "nonce": await w3_client.eth.get_transaction_count(
                                    signer_account.address, "pending"
                                ),
                                "maxFeePerGas": max_fee,
                                "maxPriorityFeePerGas": priority_fee,
                                "gas": 500000,
                            }
                        )
                        signed = signer_account.sign_transaction(tx)
                        tx_hash = await w3_client.eth.send_raw_transaction(
                            signed.raw_transaction
                        )
                        receipt = await w3_client.eth.wait_for_transaction_receipt(
                            tx_hash
                        )
                        assert receipt["status"] == 1

                        # Allow events to be emitted and handled
                        await asyncio.sleep(15)

    # Assertions
    async with get_db_session() as db_sess:
        result = await db_sess.scalars(
            select(Transaction).order_by(Transaction.timestamp.desc())
        )
        txs = result.all()

        assert len(txs) == 1

        tx = txs[0]

        assert tx.product_id == product.id
        assert tx.price_id == price_id
        assert tx.platform_user_id == str(discord_user_id)
        assert tx.recipient == "0x0000000000000000000000000000000000000001"
        assert tx.status == TransactionStatus.COMPLETE

    # Ensuring on chain state
    onchain_price = await chrima_payment_contract.functions.priceIdToAmount(
        str(price_id)
    ).call()
    assert onchain_price == usdt_amount

    member = await guild.fetch_member(discord_user_id)

    assert member is not None, "User was not added to the guild"

    roles = set([role.id for role in member.roles])
    assert discord_role_id in roles, f"User doesn't have role {discord_role_id}"


@pytest.mark.asyncio(loop_scope="session")
async def test_user_in_guild_stripped_of_role(
    discord_client: discord.Client,
    discord_service,
    discord_user_id,
    discord_guild_id,
    discord_role_id,
    discord_access_token,
    w3_client,
    chrima_payment_contract,
    signer_account,
    eth_listener,
    transaction_orchestrator: TransactionOrchestrator,
    outbox_event_poller,
    product_service,
    product_sync_service,
    price_service,
    price_sync_service,
    workspace_service,
    wallet_service,
    token_service,
    user_service,
    faker,
    create_drop_tables,
):
    """User is already in the guild but has been stripped of the role.
    The orchestrator should assign the role without re-adding to guild."""
    await _ensure_in_guild(
        discord_client, discord_guild_id, discord_user_id, discord_access_token
    )
    await _strip_role(
        discord_client, discord_guild_id, discord_user_id, discord_role_id
    )

    async with get_db_session() as db_sess:
        await discord_service.store_oauth_payload(
            discord_user_id,
            {"access_token": discord_access_token},
            db_sess,
        )
        await db_sess.commit()

    product, price = await _setup_db(
        user_service,
        workspace_service,
        wallet_service,
        product_service,
        price_service,
        token_service,
        faker,
        discord_guild_id,
        discord_role_id,
    )
    price_id = price.id
    usdt_amount = int(Decimal(str(price.amount)) * 10**6)

    async with _run(outbox_event_poller.run()):
        async with _run(eth_listener.listen()):
            async with _run(transaction_orchestrator.run()):
                async with _run(price_sync_service.run()):
                    async with _run(product_sync_service.run()):
                        await asyncio.sleep(10)

                        latest_block = await w3_client.eth.get_block("latest")
                        max_fee = int(latest_block["baseFeePerGas"]) * 3
                        priority_fee = w3_client.to_wei(2, "gwei")

                        usdt_address = (
                            await chrima_payment_contract.functions.usdtToken().call()
                        )
                        usdt_token = w3_client.eth.contract(
                            address=AsyncWeb3.to_checksum_address(usdt_address),
                            abi=[
                                {
                                    "constant": False,
                                    "inputs": [
                                        {"name": "_spender", "type": "address"},
                                        {"name": "_value", "type": "uint256"},
                                    ],
                                    "name": "approve",
                                    "outputs": [{"name": "", "type": "bool"}],
                                    "type": "function",
                                },
                                {
                                    "constant": False,
                                    "inputs": [
                                        {"name": "to", "type": "address"},
                                        {"name": "amount", "type": "uint256"},
                                    ],
                                    "name": "mint",
                                    "outputs": [],
                                    "type": "function",
                                },
                            ],
                        )

                        # Mint USDT to signer
                        mint_amount = 1_000_000 * 10**6
                        mint_tx = await usdt_token.functions.mint(
                            signer_account.address, mint_amount
                        ).build_transaction(
                            {
                                "from": signer_account.address,
                                "nonce": await w3_client.eth.get_transaction_count(
                                    signer_account.address, "pending"
                                ),
                                "maxFeePerGas": max_fee,
                                "maxPriorityFeePerGas": priority_fee,
                            }
                        )
                        signed_mint = signer_account.sign_transaction(mint_tx)
                        mint_hash = await w3_client.eth.send_raw_transaction(
                            signed_mint.raw_transaction
                        )
                        mint_receipt = await w3_client.eth.wait_for_transaction_receipt(
                            mint_hash
                        )
                        assert mint_receipt["status"] == 1, "USDT mint failed"

                        approve_tx = await usdt_token.functions.approve(
                            chrima_payment_contract.address,
                            # 2**256 - 1,
                            usdt_amount,
                        ).build_transaction(
                            {
                                "from": signer_account.address,
                                "nonce": await w3_client.eth.get_transaction_count(
                                    signer_account.address, "pending"
                                ),
                                "maxFeePerGas": max_fee,
                                "maxPriorityFeePerGas": priority_fee,
                            }
                        )
                        signed_approve = signer_account.sign_transaction(approve_tx)
                        approve_hash = await w3_client.eth.send_raw_transaction(
                            signed_approve.raw_transaction
                        )
                        approve_receipt = (
                            await w3_client.eth.wait_for_transaction_receipt(
                                approve_hash
                            )
                        )
                        assert approve_receipt["status"] == 1

                        await asyncio.sleep(2)

                        tx = await chrima_payment_contract.functions.processTransaction(
                            str(product.id),
                            str(price_id),
                            str(discord_user_id),
                        ).build_transaction(
                            {
                                "from": signer_account.address,
                                "nonce": await w3_client.eth.get_transaction_count(
                                    signer_account.address, "pending"
                                ),
                                "maxFeePerGas": max_fee,
                                "maxPriorityFeePerGas": priority_fee,
                                "gas": 500000,
                            }
                        )
                        signed = signer_account.sign_transaction(tx)
                        tx_hash = await w3_client.eth.send_raw_transaction(
                            signed.raw_transaction
                        )
                        receipt = await w3_client.eth.wait_for_transaction_receipt(
                            tx_hash
                        )
                        assert receipt["status"] == 1

                        await asyncio.sleep(15)

    async with get_db_session() as db_sess:
        result = await db_sess.scalars(
            select(Transaction).order_by(Transaction.timestamp.desc())
        )
        txs = result.all()
        assert len(txs) == 1
        tx = txs[0]
        assert tx.product_id == product.id
        assert tx.price_id == price_id
        assert tx.platform_user_id == str(discord_user_id)
        assert tx.status == TransactionStatus.COMPLETE

    onchain_price = await chrima_payment_contract.functions.priceIdToAmount(
        str(price_id)
    ).call()
    assert onchain_price == usdt_amount

    guild = await discord_client.fetch_guild(discord_guild_id)
    member = await guild.fetch_member(discord_user_id)
    assert member is not None, "User should still be in the guild"
    roles = set([role.id for role in member.roles])
    assert discord_role_id in roles, f"Expected role {discord_role_id}, got {roles}"


@pytest.mark.asyncio(loop_scope="session")
async def test_user_in_guild_already_has_role(
    discord_client: discord.Client,
    discord_service,
    discord_user_id,
    discord_guild_id,
    discord_role_id,
    discord_access_token,
    w3_client,
    chrima_payment_contract,
    signer_account,
    eth_listener,
    transaction_orchestrator: TransactionOrchestrator,
    outbox_event_poller,
    product_service,
    product_sync_service,
    price_service,
    price_sync_service,
    workspace_service,
    wallet_service,
    token_service,
    user_service,
    faker,
    create_drop_tables,
):
    """User is already in the guild and already has the role.
    The orchestrator should retain the role and the subscription balance
    should reflect the correct state."""
    await _ensure_in_guild(
        discord_client, discord_guild_id, discord_user_id, discord_access_token
    )
    await _ensure_role(
        discord_client, discord_guild_id, discord_user_id, discord_role_id
    )

    async with get_db_session() as db_sess:
        await discord_service.store_oauth_payload(
            discord_user_id,
            {"access_token": discord_access_token},
            db_sess,
        )
        await db_sess.commit()

    product, price = await _setup_db(
        user_service,
        workspace_service,
        wallet_service,
        product_service,
        price_service,
        token_service,
        faker,
        discord_guild_id,
        discord_role_id,
    )
    price_id = price.id
    usdt_amount = int(Decimal(str(price.amount)) * 10**6)

    async with _run(outbox_event_poller.run()):
        async with _run(eth_listener.listen()):
            async with _run(transaction_orchestrator.run()):
                async with _run(price_sync_service.run()):
                    async with _run(product_sync_service.run()):
                        await asyncio.sleep(10)

                        latest_block = await w3_client.eth.get_block("latest")
                        max_fee = int(latest_block["baseFeePerGas"]) * 3
                        priority_fee = w3_client.to_wei(2, "gwei")

                        usdt_address = (
                            await chrima_payment_contract.functions.usdtToken().call()
                        )
                        usdt_token = w3_client.eth.contract(
                            address=AsyncWeb3.to_checksum_address(usdt_address),
                            abi=[
                                {
                                    "constant": False,
                                    "inputs": [
                                        {"name": "_spender", "type": "address"},
                                        {"name": "_value", "type": "uint256"},
                                    ],
                                    "name": "approve",
                                    "outputs": [{"name": "", "type": "bool"}],
                                    "type": "function",
                                },
                                {
                                    "constant": False,
                                    "inputs": [
                                        {"name": "to", "type": "address"},
                                        {"name": "amount", "type": "uint256"},
                                    ],
                                    "name": "mint",
                                    "outputs": [],
                                    "type": "function",
                                },
                            ],
                        )

                        # Mint USDT to signer
                        mint_amount = 1_000_000 * 10**6
                        mint_tx = await usdt_token.functions.mint(
                            signer_account.address, mint_amount
                        ).build_transaction(
                            {
                                "from": signer_account.address,
                                "nonce": await w3_client.eth.get_transaction_count(
                                    signer_account.address, "pending"
                                ),
                                "maxFeePerGas": max_fee,
                                "maxPriorityFeePerGas": priority_fee,
                            }
                        )
                        signed_mint = signer_account.sign_transaction(mint_tx)
                        mint_hash = await w3_client.eth.send_raw_transaction(
                            signed_mint.raw_transaction
                        )
                        mint_receipt = await w3_client.eth.wait_for_transaction_receipt(
                            mint_hash
                        )
                        assert mint_receipt["status"] == 1, "USDT mint failed"

                        approve_tx = await usdt_token.functions.approve(
                            chrima_payment_contract.address,
                            usdt_amount,
                        ).build_transaction(
                            {
                                "from": signer_account.address,
                                "nonce": await w3_client.eth.get_transaction_count(
                                    signer_account.address, "pending"
                                ),
                                "maxFeePerGas": max_fee,
                                "maxPriorityFeePerGas": priority_fee,
                            }
                        )
                        signed_approve = signer_account.sign_transaction(approve_tx)
                        approve_hash = await w3_client.eth.send_raw_transaction(
                            signed_approve.raw_transaction
                        )
                        approve_receipt = (
                            await w3_client.eth.wait_for_transaction_receipt(
                                approve_hash
                            )
                        )
                        assert approve_receipt["status"] == 1

                        await asyncio.sleep(2)

                        tx = await chrima_payment_contract.functions.processTransaction(
                            str(product.id),
                            str(price_id),
                            str(discord_user_id),
                        ).build_transaction(
                            {
                                "from": signer_account.address,
                                "nonce": await w3_client.eth.get_transaction_count(
                                    signer_account.address, "pending"
                                ),
                                "maxFeePerGas": max_fee,
                                "maxPriorityFeePerGas": priority_fee,
                                "gas": 500000,
                            }
                        )
                        signed = signer_account.sign_transaction(tx)
                        tx_hash = await w3_client.eth.send_raw_transaction(
                            signed.raw_transaction
                        )
                        receipt = await w3_client.eth.wait_for_transaction_receipt(
                            tx_hash
                        )
                        assert receipt["status"] == 1

                        await asyncio.sleep(15)

    async with get_db_session() as db_sess:
        result = await db_sess.scalars(
            select(Transaction).order_by(Transaction.timestamp.desc())
        )
        txs = result.all()
        assert len(txs) == 1
        tx = txs[0]
        assert tx.product_id == product.id
        assert tx.price_id == price_id
        assert tx.platform_user_id == str(discord_user_id)
        assert tx.status == TransactionStatus.COMPLETE

    onchain_price = await chrima_payment_contract.functions.priceIdToAmount(
        str(price_id)
    ).call()
    assert onchain_price == usdt_amount

    guild = await discord_client.fetch_guild(discord_guild_id)
    member = await guild.fetch_member(discord_user_id)
    assert member is not None, "User should still be in the guild"
    roles = set([role.id for role in member.roles])
    assert discord_role_id in roles, f"Expected role {discord_role_id}, got {roles}"
