# price

A `price` is a workspace- and product-scoped sellable amount (type, currency, recurrence, trial period). The module
provides workspace-scoped CRUD over these prices and publishes change events for downstream consumers.

## Entry point

`api.IPriceService` — `OPEN` module (`api` is marked `ApplicationModule.Type.OPEN`).

## Dependencies

- `workspace.api.IWorkspaceService` / `product.api.IProductService` — validate the owning workspace and product exist.
- `events.api.IEventService` — publishes `PriceUpdatedEvent` on create/update via the transactional outbox.