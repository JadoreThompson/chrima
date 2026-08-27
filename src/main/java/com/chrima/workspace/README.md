# workspace

A `workspace` is a message-platform group/server (Discord, Telegram) owned by a platform user and used as the
delivery target for subscription notifications. The module provides user-scoped CRUD over these workspaces.

## Entry point

`api.IWorkspaceService` — `OPEN` module (`api` is marked `ApplicationModule.Type.OPEN`).

## Dependencies

- `user.api.IUserService` — validates that the owning user exists before a workspace is created.