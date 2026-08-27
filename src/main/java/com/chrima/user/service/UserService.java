package com.chrima.user.service;

import com.chrima.user.api.IUserService;
import com.chrima.user.api.dto.UserDto;
import com.chrima.user.api.enums.Tier;
import com.chrima.user.exception.IncorrectPasswordException;
import com.chrima.user.exception.UserNotFoundException;
import com.chrima.user.exception.UserValidationException;
import com.chrima.user.model.User;
import com.chrima.user.repository.UserRepository;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserService implements IUserService {

  private final UserRepository userRepository;
  private final PasswordEncoder passwordEncoder;

  @Override
  @Transactional
  public UserDto create(String username, String email, String password) {
    log.info("Creating user username={} email={}", username, email);
    if (userRepository.existsByUsername(username)) {
      log.warn("User creation rejected - username already exists username={}", username);
      throw new UserValidationException("User with username '" + username + "' already exists");
    }
    if (userRepository.existsByEmail(email)) {
      log.warn("User creation rejected - email already exists email={}", email);
      throw new UserValidationException("User with email '" + email + "' already exists");
    }
    User user = User.builder().username(username).email(email).password(password).build();
    User saved = userRepository.save(user);
    log.info("User created id={} username={}", saved.getId(), username);
    return toDto(saved);
  }

  @Override
  @Transactional(readOnly = true)
  public void ensureExists(UUID userId) {
    getUserOrThrow(userId);
  }

  @Override
  @Transactional(readOnly = true)
  public UserDto getById(UUID userId) {
    User user = getUserOrThrow(userId);
    return toDto(user);
  }

  @Override
  @Transactional(readOnly = true)
  public UserDto findByEmail(String email) {
    User user =
        userRepository
            .findByEmail(email)
            .orElseThrow(
                () -> {
                  log.warn("User not found by email email={}", email);
                  return new UserNotFoundException();
                });
    return toDto(user);
  }

  @Override
  @Transactional(readOnly = true)
  public String getJwtToken(UUID userId) {
    User user = getUserOrThrow(userId);
    return user.getJwtToken();
  }

  @Override
  @Transactional
  public void setJwtToken(UUID userId, String jwtToken) {
    User user = getUserOrThrow(userId);
    user.setJwtToken(jwtToken);
    userRepository.save(user);
    log.info("JWT token updated for user id={}", userId);
  }

  @Override
  @Transactional
  public void setTier(UUID userId, Tier tier) {
    User user = getUserOrThrow(userId);
    user.setTier(tier);
    userRepository.save(user);
    log.info("Tier updated for user id={} tier={}", userId, tier);
  }

  @Override
  @Transactional
  public UserDto changeUsername(UUID userId, String newUsername) {
    User user = getUserOrThrow(userId);
    if (userRepository.existsByUsernameAndIdNot(newUsername, userId)) {
      log.warn("Username change rejected - username already taken newUsername={}", newUsername);
      throw new UserValidationException("Username '" + newUsername + "' already taken");
    }
    user.setUsername(newUsername);
    User saved = userRepository.save(user);
    log.info("Username changed for user id={} newUsername={}", userId, newUsername);
    return toDto(saved);
  }

  @Override
  @Transactional
  public UserDto changePassword(UUID userId, String oldPassword, String newPassword) {
    User user = getUserOrThrow(userId);
    if (!passwordEncoder.matches(oldPassword, user.getPassword())) {
      log.warn("Password change rejected - incorrect old password userId={}", userId);
      throw new IncorrectPasswordException();
    }
    user.setPassword(passwordEncoder.encode(newPassword));
    User saved = userRepository.save(user);
    log.info("Password changed for user id={}", userId);
    return toDto(saved);
  }

  @Override
  @Transactional
  public UserDto changeEmail(UUID userId, String newEmail) {
    User user = getUserOrThrow(userId);
    if (userRepository.existsByEmailAndIdNot(newEmail, userId)) {
      log.warn("Email change rejected - email already taken newEmail={}", newEmail);
      throw new UserValidationException("Email '" + newEmail + "' already taken");
    }
    user.setEmail(newEmail);
    User saved = userRepository.save(user);
    log.info("Email changed for user id={} newEmail={}", userId, newEmail);
    return toDto(saved);
  }

  private User getUserOrThrow(UUID userId) {
    return userRepository
        .findById(userId)
        .orElseThrow(
            () -> {
              log.warn("User not found id={}", userId);
              return new UserNotFoundException();
            });
  }

  private UserDto toDto(User user) {
    return UserDto.builder()
        .id(user.getId())
        .username(user.getUsername())
        .email(user.getEmail())
        .createdAt(user.getCreatedAt())
        .updatedAt(user.getUpdatedAt())
        .build();
  }
}
