package com.chrima.user.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.user.config.PasswordEncoderConfig;
import com.chrima.user.dto.UserDto;
import com.chrima.user.exception.IncorrectPasswordException;
import com.chrima.user.exception.UserNotFoundException;
import com.chrima.user.exception.UserValidationException;
import com.chrima.user.model.User;
import com.chrima.user.model.enums.Tier;
import com.chrima.user.repository.UserRepository;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataJpaTest
@Testcontainers
@Import({UserService.class, PasswordEncoderConfig.class})
class UserServiceIntegrationTest {

  @Container
  static PostgreSQLContainer<?> postgres =
      new PostgreSQLContainer<>("postgres:16-alpine")
          .withDatabaseName("chrima")
          .withUsername("postgres")
          .withPassword("password");

  @DynamicPropertySource
  static void registerProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
    registry.add("spring.datasource.driver-class-name", postgres::getDriverClassName);
  }

  @Autowired private UserService userService;

  @Autowired private UserRepository userRepository;

  @Autowired private PasswordEncoder passwordEncoder;

  @AfterEach
  void tearDown() {
    userRepository.deleteAll();
  }

  // ---- create ----

  @Test
  void shouldCreateUserAndPersist() {
    User user = userService.create("testuser", "test@example.com", "secure_pass");

    assertThat(user.getId()).isNotNull();
    assertThat(user.getUsername()).isEqualTo("testuser");
    assertThat(user.getEmail()).isEqualTo("test@example.com");
    assertThat(user.getPassword()).isEqualTo("secure_pass");
    assertThat(user.getTier()).isEqualTo(Tier.FREE);

    userRepository.flush();
    User fetched = userRepository.findById(user.getId()).orElseThrow();
    assertThat(fetched.getUsername()).isEqualTo("testuser");
    assertThat(fetched.getCreatedAt()).isNotNull();
    assertThat(fetched.getUpdatedAt()).isNotNull();
  }

  @Test
  void shouldRejectDuplicateUsername() {
    userService.create("dupuser", "first@example.com", "pass");

    assertThatThrownBy(() -> userService.create("dupuser", "second@example.com", "pass"))
        .isInstanceOf(UserValidationException.class)
        .hasMessageContaining("dupuser");
  }

  @Test
  void shouldRejectDuplicateEmail() {
    userService.create("user_a", "dup@example.com", "pass");

    assertThatThrownBy(() -> userService.create("user_b", "dup@example.com", "pass"))
        .isInstanceOf(UserValidationException.class);
  }

  // ---- getById ----

  @Test
  void shouldGetByIdReturnDto() {
    User created = userService.create("getbyid", "get@example.com", "pass");
    userRepository.flush();

    UserDto fetched = userService.getById(created.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getUsername()).isEqualTo("getbyid");
    assertThat(fetched.getEmail()).isEqualTo("get@example.com");
    // timestamps are populated by Hibernate on flush; DTO should reflect them
    assertThat(fetched.getCreatedAt()).isNotNull();
    assertThat(fetched.getUpdatedAt()).isNotNull();
    // also verify via direct repository read
    User reloaded = userRepository.findById(created.getId()).orElseThrow();
    assertThat(reloaded.getCreatedAt()).isNotNull();
  }

  @Test
  void shouldThrowWhenGetByIdNotFound() {
    assertThatThrownBy(() -> userService.getById(UUID.randomUUID()))
        .isInstanceOf(UserNotFoundException.class);
  }

  // ---- findByEmail ----

  @Test
  void shouldFindByEmail() {
    User created = userService.create("findtest", "find@example.com", "pass");

    User found = userService.findByEmail("find@example.com");

    assertThat(found.getId()).isEqualTo(created.getId());
    assertThat(found.getUsername()).isEqualTo("findtest");
  }

  @Test
  void shouldThrowWhenFindByEmailNotFound() {
    assertThatThrownBy(() -> userService.findByEmail("nonexistent@example.com"))
        .isInstanceOf(UserNotFoundException.class);
  }

  // ---- jwt token ----

  @Test
  void shouldSetAndGetJwtToken() {
    User user = userService.create("jwttest", "jwt@example.com", "pass");

    assertThat(userService.getJwtToken(user.getId())).isNull();

    userService.setJwtToken(user.getId(), "my_token");

    assertThat(userService.getJwtToken(user.getId())).isEqualTo("my_token");
  }

  @Test
  void shouldClearJwtToken() {
    User user = userService.create("cleartoken", "clear@example.com", "pass");
    userService.setJwtToken(user.getId(), "some_token");
    userService.setJwtToken(user.getId(), null);

    assertThat(userService.getJwtToken(user.getId())).isNull();
  }

  @Test
  void shouldThrowWhenJwtTokenUserNotFound() {
    UUID unknown = UUID.randomUUID();
    assertThatThrownBy(() -> userService.getJwtToken(unknown))
        .isInstanceOf(UserNotFoundException.class);
    assertThatThrownBy(() -> userService.setJwtToken(unknown, "token"))
        .isInstanceOf(UserNotFoundException.class);
  }

  // ---- setTier ----

  @Test
  void shouldSetTier() {
    User user = userService.create("tierUser", "tier@example.com", "pass");
    assertThat(user.getTier()).isEqualTo(Tier.FREE);

    userService.setTier(user.getId(), Tier.PRO);

    UserDto dto = userService.getById(user.getId());
    User reloaded = userRepository.findById(user.getId()).orElseThrow();
    assertThat(reloaded.getTier()).isEqualTo(Tier.PRO);
  }

  @Test
  void shouldThrowWhenSetTierUserNotFound() {
    assertThatThrownBy(() -> userService.setTier(UUID.randomUUID(), Tier.PRO))
        .isInstanceOf(UserNotFoundException.class);
  }

  // ---- changeUsername ----

  @Test
  void shouldChangeUsername() {
    User user = userService.create("oldname", "test@example.com", "pass");

    UserDto updated = userService.changeUsername(user.getId(), "newname");

    assertThat(updated.getUsername()).isEqualTo("newname");
    assertThat(updated.getId()).isEqualTo(user.getId());
    User reloaded = userRepository.findById(user.getId()).orElseThrow();
    assertThat(reloaded.getUsername()).isEqualTo("newname");
  }

  @Test
  void shouldRejectDuplicateUsernameOnChange() {
    userService.create("taken", "a@example.com", "pass");
    User user = userService.create("original", "b@example.com", "pass");

    assertThatThrownBy(() -> userService.changeUsername(user.getId(), "taken"))
        .isInstanceOf(UserValidationException.class);
  }

  @Test
  void shouldThrowWhenChangeUsernameUserNotFound() {
    assertThatThrownBy(() -> userService.changeUsername(UUID.randomUUID(), "any"))
        .isInstanceOf(UserNotFoundException.class);
  }

  @Test
  void shouldAllowChangingToSameUsername() {
    User user = userService.create("sameName", "same@example.com", "pass");

    // changing to same name should not be considered duplicate
    UserDto updated = userService.changeUsername(user.getId(), "sameName");

    assertThat(updated.getUsername()).isEqualTo("sameName");
  }

  // ---- changePassword ----

  @Test
  void shouldChangePassword() {
    String oldHash = passwordEncoder.encode("old_pass");
    User user = userService.create("pwtest", "pw@example.com", oldHash);

    userService.changePassword(user.getId(), "old_pass", "new_pass");

    User reloaded = userRepository.findById(user.getId()).orElseThrow();
    assertThat(passwordEncoder.matches("new_pass", reloaded.getPassword())).isTrue();
    assertThat(passwordEncoder.matches("old_pass", reloaded.getPassword())).isFalse();
  }

  @Test
  void shouldThrowWhenOldPasswordIncorrect() {
    String hash = passwordEncoder.encode("old_pass");
    User user = userService.create("pwtest2", "pw2@example.com", hash);

    assertThatThrownBy(() -> userService.changePassword(user.getId(), "wrong_pass", "new_pass"))
        .isInstanceOf(IncorrectPasswordException.class);

    User reloaded = userRepository.findById(user.getId()).orElseThrow();
    assertThat(passwordEncoder.matches("old_pass", reloaded.getPassword())).isTrue();
  }

  @Test
  void shouldThrowWhenChangePasswordUserNotFound() {
    assertThatThrownBy(() -> userService.changePassword(UUID.randomUUID(), "old", "new"))
        .isInstanceOf(UserNotFoundException.class);
  }

  // ---- changeEmail ----

  @Test
  void shouldChangeEmail() {
    User user = userService.create("emailtest", "old@example.com", "pass");

    UserDto updated = userService.changeEmail(user.getId(), "new@example.com");

    assertThat(updated.getEmail()).isEqualTo("new@example.com");
    User reloaded = userRepository.findById(user.getId()).orElseThrow();
    assertThat(reloaded.getEmail()).isEqualTo("new@example.com");
  }

  @Test
  void shouldRejectDuplicateEmailOnChange() {
    userService.create("user_a", "taken@example.com", "pass");
    User user = userService.create("user_b", "original@example.com", "pass");

    assertThatThrownBy(() -> userService.changeEmail(user.getId(), "taken@example.com"))
        .isInstanceOf(UserValidationException.class);
  }

  @Test
  void shouldThrowWhenChangeEmailUserNotFound() {
    assertThatThrownBy(() -> userService.changeEmail(UUID.randomUUID(), "any@example.com"))
        .isInstanceOf(UserNotFoundException.class);
  }

  @Test
  void shouldAllowChangingToSameEmail() {
    User user = userService.create("sameEmailUser", "same@example.com", "pass");

    UserDto updated = userService.changeEmail(user.getId(), "same@example.com");

    assertThat(updated.getEmail()).isEqualTo("same@example.com");
  }
}
