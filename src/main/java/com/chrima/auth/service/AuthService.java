package com.chrima.auth.service;

import com.chrima.auth.api.IAuthService;
import com.chrima.auth.api.dto.LoginRequest;
import com.chrima.auth.api.dto.RegisterRequest;
import com.chrima.auth.exception.InvalidLoginCredentialsException;
import com.chrima.user.api.IUserService;
import com.chrima.user.api.dto.UserDto;
import com.chrima.user.exception.UserNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService implements IAuthService {

  private final IUserService userService;
  private final PasswordEncoder passwordEncoder;

  @Override
  @Transactional
  public UserDto register(RegisterRequest request) {
    String hashed = passwordEncoder.encode(request.getPassword());
    return userService.create(request.getUsername(), request.getEmail(), hashed);
  }

  @Override
  @Transactional(readOnly = true)
  public UserDto verifyCredentials(LoginRequest request) {
    UserDto user;
    try {
      user = userService.findByEmail(request.getEmail());
    } catch (UserNotFoundException e) {
      log.warn("Login rejected - user not found email={}", request.getEmail());
      throw new InvalidLoginCredentialsException();
    }
    String hash;
    try {
      hash = userService.getPasswordHashByEmail(request.getEmail());
    } catch (UserNotFoundException e) {
      throw new InvalidLoginCredentialsException();
    }
    if (!passwordEncoder.matches(request.getPassword(), hash)) {
      log.warn("Login rejected - wrong password email={}", request.getEmail());
      throw new InvalidLoginCredentialsException();
    }
    return user;
  }
}
