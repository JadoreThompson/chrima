---
name: commit
description: Project conventions, commit rules, and development tasks for chrima-backend
---

# Chrima Project Rules

## Commit conventions

- Format: `<type>: <description>` (feat, refactor, test, chore, test, (wip) feat, (wip) refactor, etc.)
- Do NOT commit unless explicitly asked

## Architecture rules

### Test conventions

- Every async test uses `@pytest.mark.asyncio(loop_scope="session")`
- Every test requests `create_drop_tables` fixture (function-scoped, fresh DB per test)
- Service tests use `class`-based grouping by method (e.g. `TestCreate`, `TestGet`)
- Router tests use `class`-based grouping by endpoint (e.g. `TestGetSummary`, `TestGetRevenue`)
- Router test `_setup` helper: creates user+workspace via services, then calls `POST /auth/login` + `POST /auth/select-workspace`
- `test_401_without_auth` tests intentionally skip `_setup`
- Factory fixtures return `async def _func(...)` inner functions
- Use conftest fixtures: `user_service`, `price_service`, `product_service`, `workspace_service`, `wallet_service`, `token_service`, `subscription_balance_service`, `analytics_service`, `transaction_service`

### Full test run

```bash
uv run pytest --ignore=test/integration
```

### Python toolchain

- Python 3.13+, `uv` for package management
- PostgreSQL (real, not mocked), via Docker
- No linter/typechecker/formatter configured
