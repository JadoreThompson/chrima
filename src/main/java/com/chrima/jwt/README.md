# jwt

Stateless JWT handling for authentication. Encodes/decodes tokens containing user identity (`sub`, `em`,
`workspace_id`, `exp`) signed with HS256, manages HTTP-only cookies, and validates tokens against the
persisted user record.

## Entry point

`api.IJwtService` — `OPEN` module (`api` is marked `ApplicationModule.Type.OPEN`).

## Dependencies

- `user.api.IUserService` — validates that the JWT belongs to an existing user and matches the stored
  token during `validate`.
