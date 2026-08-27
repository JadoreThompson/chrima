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

- Use test containers for mocking application infrastructure. For example postgres:16-alpine for db
- Create a test class for each method within a class
- If multiple test classes within a domain or package have the same setup, use a shared
  `AbstractNameOfServiceIntegrationBase`
  class.

## Conventions

- DB entities must NOT have `of()` methods — use Lombok `@Builder` instead. The established entity pattern is
  `@Getter` + `@Builder` + `@AllArgsConstructor(access = AccessLevel.PACKAGE)` + a `protected` no-arg constructor for
  JPA (see `Notification`, `DiscordNotification`).
- Use Lombok/JPA annotations (`@RequiredArgsConstructor`, `@Slf4j`, `@Entity`, etc.) to minimize boilerplate like
  constructors, getters and setters.
- modules can only import from foreign module's api package
- Dto objects of db entities should have a static `from` method which constructs the dto object from the entity
- Each package should contain a `README.md` which is strictly a synopsis of the package, it's utility and how it
  interacts with those packages it depends on. It is not to contain details of methods. Method detailing is to be done
  with kdocs on the specific methods themselves.

# Extras

- When looking to gain an understanding of a package, check if it has a `README.md` you can read instead of reading
  files directly.
