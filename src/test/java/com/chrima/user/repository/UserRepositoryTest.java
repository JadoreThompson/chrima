package com.chrima.user.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.user.model.User;
import com.chrima.user.model.enums.Tier;

import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataJpaTest
@Testcontainers
class UserRepositoryTest {

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

    @Autowired
    private UserRepository userRepository;

    @AfterEach
    void tearDown() {
        try {
            userRepository.deleteAll();
        } catch (Exception ignored) {
            // transaction may be aborted after constraint violation test; rollback will clean up
        }
    }

    private User saveUser(String username, String email, String password) {
        User user =
                User.builder().username(username).email(email).password(password).tier(Tier.FREE).build();
        return userRepository.save(user);
    }

    @Test
    void shouldSaveAndFindByEmail() {
        User saved = saveUser("alice", "alice@example.com", "hashed");

        Optional<User> found = userRepository.findByEmail("alice@example.com");

        assertThat(found).isPresent();
        assertThat(found.get().getId()).isEqualTo(saved.getId());
        assertThat(found.get().getUsername()).isEqualTo("alice");
    }

    @Test
    void findByEmailShouldReturnEmptyWhenNotFound() {
        saveUser("bob", "bob@example.com", "pass");

        Optional<User> found = userRepository.findByEmail("nonexistent@example.com");

        assertThat(found).isEmpty();
    }

    @Test
    void findByUsernameShouldReturnUserWhenExists() {
        User saved = saveUser("charlie", "charlie@example.com", "pass");

        Optional<User> found = userRepository.findByUsername("charlie");

        assertThat(found).isPresent();
        assertThat(found.get().getId()).isEqualTo(saved.getId());
    }

    @Test
    void findByUsernameShouldReturnEmptyWhenNotFound() {
        saveUser("dave", "dave@example.com", "pass");

        assertThat(userRepository.findByUsername("unknown")).isEmpty();
    }

    @Test
    void existsByUsernameShouldWork() {
        saveUser("eve", "eve@example.com", "pass");

        assertThat(userRepository.existsByUsername("eve")).isTrue();
        assertThat(userRepository.existsByUsername("nonexistent")).isFalse();
    }

    @Test
    void existsByEmailShouldWork() {
        saveUser("frank", "frank@example.com", "pass");

        assertThat(userRepository.existsByEmail("frank@example.com")).isTrue();
        assertThat(userRepository.existsByEmail("other@example.com")).isFalse();
    }

    @Test
    void existsByUsernameAndIdNotShouldDetectDuplicateForOtherUser() {
        User first = saveUser("user1", "user1@example.com", "pass");
        User second = saveUser("user2", "user2@example.com", "pass");

        assertThat(userRepository.existsByUsernameAndIdNot("user1", second.getId())).isTrue();
        assertThat(userRepository.existsByUsernameAndIdNot("user1", first.getId())).isFalse();
        assertThat(userRepository.existsByUsernameAndIdNot("nonexistent", first.getId())).isFalse();
    }

    @Test
    void existsByEmailAndIdNotShouldDetectDuplicateForOtherUser() {
        User first = saveUser("a1", "a1@example.com", "pass");
        User second = saveUser("a2", "a2@example.com", "pass");

        assertThat(userRepository.existsByEmailAndIdNot("a1@example.com", second.getId())).isTrue();
        assertThat(userRepository.existsByEmailAndIdNot("a1@example.com", first.getId())).isFalse();
        assertThat(userRepository.existsByEmailAndIdNot("unknown@example.com", first.getId()))
                .isFalse();
    }

    @Test
    void shouldPersistTierAndTimestamps() {
        User saved = saveUser("tiertest", "tier@example.com", "pass");
        userRepository.flush();

        assertThat(saved.getId()).isNotNull();
        assertThat(saved.getTier()).isEqualTo(Tier.FREE);
        assertThat(saved.getCreatedAt()).isNotNull();
        assertThat(saved.getUpdatedAt()).isNotNull();

        User fetched = userRepository.findById(saved.getId()).orElseThrow();
        assertThat(fetched.getCreatedAt()).isNotNull();
        assertThat(fetched.getUpdatedAt()).isNotNull();
    }

    @Test
    void shouldPersistJwtTokenNullByDefault() {
        User saved = saveUser("jwttest", "jwt@example.com", "pass");

        assertThat(saved.getJwtToken()).isNull();
        User fetched = userRepository.findById(saved.getId()).orElseThrow();
        assertThat(fetched.getJwtToken()).isNull();
    }

    @Test
    void shouldUpdateJwtToken() {
        User saved = saveUser("jwt2", "jwt2@example.com", "pass");
        saved.setJwtToken("my-token");
        userRepository.save(saved);

        User fetched = userRepository.findById(saved.getId()).orElseThrow();
        assertThat(fetched.getJwtToken()).isEqualTo("my-token");
    }

    @Test
    void shouldEnforceUniqueUsernameAtDatabaseLevel() {
        saveUser("uniqueUser", "first@example.com", "pass");
        userRepository.flush();

        User duplicate =
                User.builder().username("uniqueUser").email("second@example.com").password("pass").build();
        org.assertj.core.api.Assertions.assertThatThrownBy(() -> userRepository.saveAndFlush(duplicate))
                .isInstanceOf(Exception.class);
    }

    @Test
    void shouldEnforceUniqueEmailAtDatabaseLevel() {
        saveUser("userA", "dup@example.com", "pass");
        userRepository.flush();

        User duplicate =
                User.builder().username("userB").email("dup@example.com").password("pass").build();
        org.assertj.core.api.Assertions.assertThatThrownBy(() -> userRepository.saveAndFlush(duplicate))
                .isInstanceOf(Exception.class);
    }

    @Test
    void findByIdShouldReturnEmptyForUnknownId() {
        Optional<User> found = userRepository.findById(UUID.randomUUID());
        assertThat(found).isEmpty();
    }
}
