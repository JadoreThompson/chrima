# price — workspace/product-scoped prices

A `price` belongs to a `product` and a `workspace`; it carries the sellable amount/type/currency.
Mirrors `chrima.price` from the Python backend.

## Entry point

`api.IPriceService` — `OPEN` module (`api._PackageInfo`). Methods mirror `chrima.price.service.PriceService`.

## Service

- `create(workspaceId, productId, type, currency, amount, recurringInterval, recurringIntervalCount, trialPeriodDays)` — validates `amount > 0` (`PriceValidationException`), workspace via `workspace.api.IWorkspaceService.getById`, product via `product.api.IProductService.getById` (unknown ids → `WorkspaceNotFoundException` / `ProductNotFoundException`), persists `Price`, publishes `PriceUpdatedEvent`.
- `getById(priceId)` — throws `PriceNotFoundException` when missing.
- `get(priceId, workspaceId)` — scoped by `workspaceId` (wrong workspace → not found); uses `findByIdAndWorkspaceId`.
- `listByProduct(productId, pageable)` — Spring `Page<PriceResponse>` via `Pageable` (`PageRequest.of(page-1, limit)`), validates product, delegates to `PriceRepository.findByProductId`; legacy overload `listByProduct(productId, page, limit)`.
- `update(priceId, workspaceId, currency, amount, recurringInterval, recurringIntervalCount, trialPeriodDays)` — scoped by workspace; updates non-null fields only, validates `amount > 0` when provided; publishes `PriceUpdatedEvent`.
- `delete(priceId, workspaceId)` — scoped by workspace.

## Event

- `event.PriceUpdatedEvent` — `IEventPayload` annotated `@EventType(value = "price.updated", topic = "price-events")` with `priceId` + `amount`; published on create/update via `events.api.IEventService.publish` (transactional outbox → Kafka). Mirrors Python `PriceUpdatedEvent` + `price-events` topic.

## Model

- `model.Price` — JPA `@Entity` (`prices`), `UUID id`, `workspaceId` (column `workspace_id`), `productId` (column `product_id`), `type` (`PriceType.ONE_TIME` / `RECURRING` as `VARCHAR`), `currency` (`Currency.USD`), `amount` (`double`), `recurringInterval` / `recurringIntervalCount` / `trialPeriodDays` (nullable), `createdAt` (`@CreationTimestamp`) / `updatedAt` (`@UpdateTimestamp`).
- `api.enums.Currency` — `USD("usd")`.
- `api.enums.PriceType` — `ONE_TIME("one_time")`, `RECURRING("recurring")`.
- `api.enums.RecurringInterval` — `DAY("day")`, `MONTH("month")`.

## Where to look

`api/` contract + response + enums · `model/` entity · `dto/` requests · `event/` payload · `exception/` not-found + validation · `repository/` Spring Data JPA · `service/` implementation