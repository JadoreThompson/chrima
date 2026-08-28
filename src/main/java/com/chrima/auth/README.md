# auth

Authentication and account-management facade over `user`, `jwt` and `workspace`. Provides registration,
login with password hashing, workspace selection (issuing workspace-scoped JWTs), logout, and profile
mutations (username/email/password) while refreshing the JWT cookie.

## Entry point

`api.IAuthService` — `OPEN` module (`api` is marked `ApplicationModule.Type.OPEN`).
`controller.AuthController` exposes `/auth` REST endpoints.

## Dependencies

- `user.api.IUserService` — user CRUD, password and JWT-token persistence.
- `jwt.api.IJwtService` — JWT encode/decode and cookie handling.
- `workspace.api.IWorkspaceService` — validates workspace existence for `select-workspace` and
  enriches `UserProfile` with workspace metas.
