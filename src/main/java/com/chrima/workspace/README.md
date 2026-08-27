# workspace — user-owned message-platform workspaces

A `workspace` is a server/group (discord, telegram) that a user owns and where subscription notifications are delivered.

## Entry point

`api.IWorkspaceService` — `OPEN` module (`api._PackageInfo`). Methods mirror `chrima.workspace.service` from the
Python backend.

## Service

- `create(userId, name, platform, externalId, notificationChannelId)` — validates the owner through
  `user.api.IUserService.ensureExists(userId)` (unknown `userId` → `UserNotFoundException`), persists `Workspace`
  referencing the user by id.
- `getById(workspaceId)` / `getByExternalId(externalId)` / `get(workspaceId, userId)` — throw
  `WorkspaceNotFoundException` when missing; `get` scopes by `userId` (wrong owner → not found).
- `getByUser(userId, pageable)` — Spring `Page<WorkspaceResponse>` via `Pageable` (`PageRequest.of(page, size)`), delegates to `WorkspaceRepository.findByUserId(userId, pageable)`; legacy overload `getByUser(userId, page, limit)` maps `page-1` to `Pageable` for backward compatibility.
- `update(workspaceId, userId, name, notificationChannelId)` — requires at least one field non-null
  (`IllegalArgumentException` otherwise), updates `name` / `notificationChannelId` only.
- `delete(workspaceId, userId)` — scoped by owner.

## Model

- `model.Workspace` — JPA `@Entity` (`workspaces`), `UUID id`, `userId` (column `user_id`, ownership by id — no
  cross-module entity reference), `platform` (`MessagePlatformType.DISCORD` as `VARCHAR`), `externalId`,
  `notificationChannelId`, `name`, `createdAt`/`updatedAt` (`@PrePersist`/`@PreUpdate`).
- `model.enums.MessagePlatformType` — persisted via `@Enumerated(EnumType.STRING)`.

## Where to look

`api/` contract · `model/` entity+enum · `dto/` request/response + pagination · `service/` implementation ·
`exception/` not-found
