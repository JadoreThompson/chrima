# wallet — workspace-scoped crypto wallets

A `wallet` belongs to a `workspace` and holds a name + on-chain address. Future product purchases reference a wallet for fulfillment / payouts.

## Entry point

`api.IWalletService` — `OPEN` module (`api._PackageInfo`). Methods mirror `chrima.wallet.service` from the Python backend.

## Service

- `create(workspaceId, name, walletAddress)` — validates the workspace via `workspace.api.IWorkspaceService.getById(workspaceId)` (unknown `workspaceId` → `WorkspaceNotFoundException`), persists `Wallet` referencing the workspace by id.
- `getById(walletId)` — throws `WalletNotFoundException` when missing.
- `get(walletId, workspaceId)` — scoped by `workspaceId` (wrong workspace → not found); uses `findByIdAndWorkspaceId`.
- `listByWorkspace(workspaceId, pageable)` — Spring `Page<WalletResponse>` via `Pageable` (`PageRequest.of(page, size)`), delegates to `WalletRepository.findByWorkspaceId(workspaceId, pageable)`; legacy overload `listByWorkspace(workspaceId, page, limit)` maps `page-1` to `Pageable` for backward compatibility.
- `delete(walletId, workspaceId)` — scoped by workspace; `WalletInUseException` is defined for future product-reference checks (currently deletion is allowed; product guard can be added when `product` module exists).

## Model

- `model.Wallet` — JPA `@Entity` (`wallets`), `UUID id`, `workspaceId` (column `workspace_id`, ownership by id — no cross-module entity reference), `name`, `walletAddress` (column `wallet_address`), `createdAt` (`@CreationTimestamp`).
- `model.WalletToken` + `model.WalletTokenId` — join table `wallet_tokens` (`wallet_id`, `token_id`) composite PK via `@IdClass`, mirrors Python `WalletTokens` (`repository.WalletTokenRepository.findTokenIdsByWalletId` corresponds to `service._fetch_token_ids`).
- `model.enums` — none; address validation is TODO (Python has `TODO: Add validation that the wallet address exists`).

## Where to look

`api/` contract + response · `model/` entity+join · `dto/` requests · `service/` implementation · `exception/` not-found / in-use · `repository/` Spring Data JPA
