# analytics

Aggregates workspace-scoped business metrics from transactions and subscriptions. The module is
read-only: it queries existing transaction and subscription data and returns bucketed time-series
or totals without mutating state.

## Entry point

`api.IAnalyticsService` — `OPEN` module (`api` is marked `ApplicationModule.Type.OPEN`).

## Dependencies

- `workspace.api.IWorkspaceService` — validates that the requesting user owns the workspace before
  any aggregation is returned.
- `jwt.api.IJwtService` — validates the HTTP-only auth cookie on controller endpoints.
- `transaction` / `price` / `product` / `subscription` tables — accessed via `EntityManager` native
  queries joining `transactions`→`prices` and `subscription_balances`→`products` on `workspace_id`.
