# Chrima Backend

Spring Boot 3.5 / Spring Modulith notification service. Single Gradle module whose `build.gradle` declares only the
`java` and `spotless` plugins.

## Commands

- `./gradlew build` — compile, run all tests, and Spotless check (wired into `check`).
- `./gradlew test` — JUnit 5 tests only. Requires a running Docker daemon (see Tests).
- `./gradlew spotlessApply` — format (Google Java Format, 2-space indent) and remove unused imports. Run this before
  committing; `spotlessCheck` fails otherwise.
- Requires JDK 17+ (no Gradle toolchain configured; the JDK running Gradle is used).

## Tests

- `NotificationPollerIntegrationTest` and `NotificationRepositoryTest` use Testcontainers with `postgres:16-alpine` —
  Docker must be running. `EmailNotificationChannelTest` is a pure Mockito unit test.
- The integration test sets `notification.polling.delay` very high so the `@Scheduled` poller cannot race the test body;
  do the same when adding scheduled-code tests.

## Conventions

- DB entities must NOT have `of()` methods — use Lombok `@Builder` instead. The established entity pattern is
  `@Getter` + `@Builder` + `@AllArgsConstructor(access = AccessLevel.PACKAGE)` + a `protected` no-arg constructor for
  JPA (see `Notification`, `DiscordNotification`).
- Use Lombok/JPA annotations (`@RequiredArgsConstructor`, `@Slf4j`, `@Entity`, etc.) to minimize boilerplate like
  constructors, getters and setters.
