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

### Integration tests (`test/integration/`)

- Use real on-chain contract, real Discord API, real Kafka — no mocking
- Require: `docker compose` infra running, TestUSDT deployed, `usdtToken` address set on ChrimaPayment contract
- Require env vars: `RPC_URL`, `CHRIMA_PAYMENT_CONTRACT_ADDRESS`, `SIGNER_PRIVATE_KEY`, `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`, `DISCORD_USER_ID`, `DISCORD_ACCESS_TOKEN`, `DISCORD_ROLE_1_ID`, `DISCORD_ROLE_2_ID`
- On-chain transactions require minting USDT to the signer and granting explicit gas limit (`"gas": 500000`) to skip Arbitrum gas estimation which can fail to see recent state changes
- Discord bot needs "Manage Roles" permission with role positioned above target roles

### Unit tests

- Service and router tests are in `test/<module>/` directories
- Router tests use the `client` fixture (httpx AsyncClient against FastAPI ASGI transport)

## Conventions

- Commit format: `<type>: <description>` (feat, refactor, test, chore, test(wip))
- Branch naming: `main` only (no PR/merge conventions enforced in repo)
- No linter/typechecker/formatter configured — run pytest as the primary verification
- `uv` for package management, Python 3.13+
- Discord bot permissions: Manage Roles, Kick Members, Send Messages
