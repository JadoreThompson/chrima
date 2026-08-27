# product — workspace-scoped sellable products

A `product` belongs to a `workspace` and references a `wallet` for on-chain payouts / fulfilment.
Mirrors `chrima.product` from the Python backend.

## Entry point

`api.IProductService` — `OPEN` module (`api._PackageInfo`). Methods mirror `chrima.product.service`.

## Service

- `create(workspaceId, name, description, walletId, fulfilmentType, externalUrl, roles)` — validates workspace via `workspace.api.IWorkspaceService.getById` and wallet via `wallet.api.IWalletService.getById` (unknown ids → `WorkspaceNotFoundException` / `WalletNotFoundException`), persists `Product`.
- `getById(productId)` — throws `ProductNotFoundException` when missing.
- `get(productId, workspaceId)` — scoped by `workspaceId` (wrong workspace → not found); uses `findByIdAndWorkspaceId`.
- `listByWorkspace(workspaceId, pageable)` — Spring `Page<ProductResponse>` via `Pageable` (`PageRequest.of(page, size)`), delegates to `ProductRepository.findByWorkspaceId(workspaceId, pageable)`; legacy overload `listByWorkspace(workspaceId, page, limit)` maps `page-1` to `Pageable` for backward compatibility.
- `update(productId, workspaceId, name, description, walletId, roles, externalUrl)` — scoped by workspace; updates non-null fields only, validates new `walletId` when changed.
- `delete(productId, workspaceId)` — scoped by workspace.

## Model

- `model.Product` — JPA `@Entity` (`products`), `UUID id`, `workspaceId` (column `workspace_id`, FK `fk_products_workspace_id` `CASCADE`), `name`, `description` (length 256), `walletId` (column `wallet_id`, FK `fk_products_wallet_id`), `fulfilmentType` (`FulfilmentType.INVITE` / `ROLE` as `VARCHAR`), `externalUrl`, `roles` (`jsonb` `List<String>` via `@JdbcTypeCode(SqlTypes.JSON)`), `createdAt` (`@CreationTimestamp`) / `updatedAt` (`@UpdateTimestamp`).
- `api.enums.FulfilmentType` — `INVITE`, `ROLE` persisted via `@Enumerated(EnumType.STRING)`.

## Where to look

`api/` contract + response + enums · `model/` entity · `dto/` requests · `service/` implementation · `exception/` not-found · `repository/` Spring Data JPA
