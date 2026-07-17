# AGENTS.md

## Dev commands

```bash
# Start test infrastructure (PostgreSQL, Redis, Kafka)
docker compose -p chrima-test -f docker-compose.infra.yaml --env-file .env.test up -d

# Run all tests
uv run pytest

# Run a single test
uv run pytest test/path/test_file.py::test_name

# Run tests with output (no capture)
uv run pytest -s test/path/test_file.py::test_name

# Compile smart contracts
cd src/resources/contract && bunx hardhat compile

# Deploy smart contract
cd src/resources/contract && bunx hardhat run scripts/deploy.js --network arbitrum
```

## Architecture

### Event pipeline (outbox pattern)

```
Service creates entity → EventPublisher.publish() → EventOutbox table (DB)
→ OutboxPoller picks up → Kafka topic → SyncService/Orchestrator consumes
```

- `OutboxEventPublisher` persists events to the `event_outbox` table in the same DB transaction as the business operation
- `OutboxPoller` (`src/chrima/event_bus/service/outbox/poller.py`) polls the table and publishes to Kafka
- Sync services (`PriceSyncService`, `ProductSyncService`) consume from Kafka and call on-chain contract methods
- `EthListener` listens for on-chain `TransactionComplete` events and persists transaction records

### Service layer conventions

- Services receive dependencies via constructor injection
- Services that mutate on-chain state do NOT call the contract directly; they emit outbox events consumed by sync services
- `PriceService` takes `event_publisher: EventPublisher` — on create/update, emits `PriceUpdatedEvent`
- `ProductService` takes `event_publisher: EventPublisher` — on create/wallet-update, emits `ProductWalletUpdatedEvent`
- Sync services (`PriceSyncService`, `ProductSyncService`) use `SIGNER_PRIVATE_KEY` and EIP-1559 gas params (`maxFeePerGas`, `maxPriorityFeePerGas`)
- `TransactionService` is read-only (query only); transaction records are persisted by `EthListener`

## Smart contracts

- Contracts at `src/resources/contract/contracts/`, Hardhat config at the same level
- `ChrimaPayment.sol` — USDT-only, uses `IERC20.transferFrom` via `usdtToken` address
- `TestUSDT.sol` — dev mock ERC20 with public `mint()` (no access control)
- Compiled ABI at `src/resources/ChrimaPayment.json`
- Deployed on Arbitrum Sepolia; EIP-1559 gas required (plain `gasPrice` fails)

## Tests

### Test infrastructure

- `test/conftest.py` provides shared fixtures which are commonly used across test modules: `user_service`, `price_service`, `product_service`, `workspace_service`, `token_service`, `transaction_service`, `event_publisher`, etc.
- `create_drop_tables` fixture drops and recreates the `public` schema, then creates all tables from the SQLAlchemy metadata (imports all modules via `util.import_modules(chrima)`)

### Test structure

- **Service and router tests use classes** grouping tests by method/endpoint (e.g. `TestCreate`, `TestGetById`, `TestUpdate`, `TestDeletePrice`). `test/subscription/test_expiry_checker.py` is the only exception — standalone async functions.
- **Every async test** uses `@pytest.mark.asyncio(loop_scope="session")` — either on the class or per-function.
- **Every test requests `create_drop_tables`** — the fixture is function-scoped, so each test gets a fresh empty database. No SQLite in-memory mocks — all tests hit real PostgreSQL.
- **Every test function** is to have a comment describing it's goal if it's a complex flow of operations or unclear at first glance.

### Service test conventions

- Use `class`-based grouping, e.g. `TestCreate`, `TestGet`, `TestDelete`.
- Test methods named `test_<action_description>` (e.g. `test_creates_price`, `test_updates_amount`).
- Error tests named `test_<condition>_raises` (e.g. `test_zero_amount_raises`, `test_nonexistent_product_raises`).
- DB session pattern: `async with get_db_session() as db_sess:` for both setup and verification reads.
- Service methods receive `db_sess=db_sess` as a keyword argument; the test caller commits.
- Delete verifications open a NEW session to confirm the row is gone.

### Router test conventions

- Use `class`-based grouping, e.g. `TestCreateProduct`, `TestGetPrice`, `TestDeleteWallet`.
- Test methods named `test_<HTTP_STATUS>_<description>` (e.g. `test_201_creates_price`, `test_422_on_zero_amount`, `test_404_on_nonexistent`, `test_401_without_auth`).
- Use the `client` fixture (httpx AsyncClient against FastAPI ASGI transport). **Do not use `_client`** — the `_client` naming in `test/price/` and `test/product/` is a legacy inconsistency.
- **Auth pattern**: most router tests call a module-level `async def _setup(client, ...)` helper that runs `POST /auth/login` then `POST /auth/select-workspace` before the test. `test_401_without_auth` tests intentionally skip the `_setup` call.
- Auth-gated endpoints: use `jwt_service.create_test_jwt_token()` to generate tokens, pass via `Authorization: Bearer <token>` header.

### Mocking conventions

- Mocks use `spec=<TheClass>` for attribute validation (e.g. `MagicMock(spec=NotificationPublisher)`).
- Async methods are mocked with `AsyncMock()`.
- Set return values/side effects on the mock object attribute, not in the constructor.
- Mock fixtures in conftest use `mock_` prefix (e.g. `mock_notification_publisher`).
- Test-file-local mock fixtures follow the same pattern (e.g. `mock_discord`).
- For edge-case tests, inline `MagicMock()` + `AsyncMock(side_effect=...)` is acceptable.

### Factory fixtures

- Helper fixtures that create setup data return an `async def _func(...)` inner function.
- Named as `setup_<what>` or `create_<what>` (e.g. `setup_workspace_product`, `create_subscription_balance`).
- They open their own `async with get_db_session()` and commit at the end.

### Integration tests (`test/integration/`)

- Use real on-chain contract, real Discord API, real Kafka — no mocking
- Require: `docker compose` infra running, TestUSDT deployed, `usdtToken` address set on ChrimaPayment contract
- Require env vars: `RPC_URL`, `CHRIMA_PAYMENT_CONTRACT_ADDRESS`, `SIGNER_PRIVATE_KEY`, `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`, `DISCORD_USER_ID`, `DISCORD_ACCESS_TOKEN`, `DISCORD_ROLE_1_ID`, `DISCORD_ROLE_2_ID`
- On-chain transactions require minting USDT to the signer and granting explicit gas limit (`"gas": 500000`) to skip Arbitrum gas estimation which can fail to see recent state changes
- Discord bot needs "Manage Roles" permission with role positioned above target roles

## Conventions

- Commit format: `<type>: <description>` (feat, refactor, test, chore, test(wip))
- Branch naming: `main` only (no PR/merge conventions enforced in repo)
- No linter/typechecker/formatter configured — run pytest as the primary verification
- `uv` for package management, Python 3.13+
- Discord bot permissions: Manage Roles, Kick Members, Send Messages
- **Bulk refactoring**: when renaming/moving a symbol used across many files, do all the grep + replacement edits in one batch before running tests. Only run tests once all edits are done — it saves time over iterative test-and-fix cycles.
