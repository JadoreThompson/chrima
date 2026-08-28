# Discord

Port of `chrima-backend/src/chrima/discord`. Handles Discord OAuth for workspace owners and
product subscribers, plus read-only queries against the Discord REST API (guilds, channels, roles).

## Contents

- `api.IDiscordService` — public service contract (`api` is marked `ApplicationModule.Type.OPEN`).
- `client.DiscordApiClient` — synchronous HTTP client wrapping the Discord REST API
  (`/oauth2/token`, `/users/@me`, `/guilds/{id}/channels|roles`).
- `encryption.EncryptionService` — AES-GCM encrypt/decrypt of OAuth payloads (base64 JSON envelope,
  AAD = Discord user id).
- `model` — `DiscordAccessToken` (customer OAuth rows keyed by Discord snowflake) and
  `UserDiscordAccessToken` (workspace-owner OAuth rows keyed by Chrima user UUID).
- `repository` — Spring Data repositories for the token entities.
- `service.DiscordService` — OAuth code exchange, token storage/refresh, and guild/channel/role
  lookups.
- `controller.DiscordController` — REST endpoints under `/discord`, mirroring
  `chrima-backend/src/chrima/discord/router.py`.

## Interacts with

- `jwt.api` — extracts the authenticated user from the JWT cookie.
- `user.api` / `workspace.api` (indirectly, via auth) — workspace-owner flows.
- `auth.controller.AuthController` — exposes the `/auth/discord/*` OAuth callbacks that call into
  this module.