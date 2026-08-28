package com.chrima.user.api;

import com.chrima.user.api.dto.UserDto;
import com.chrima.user.api.enums.Tier;
import java.util.UUID;

public interface IUserService {

  UserDto create(String username, String email, String password);

  void ensureExists(UUID userId);

  UserDto getById(UUID userId);

  UserDto findByEmail(String email);

  String getJwtToken(UUID userId);

  void setJwtToken(UUID userId, String jwtToken);

  void setTier(UUID userId, Tier tier);

  UserDto changeUsername(UUID userId, String newUsername);

  UserDto changePassword(UUID userId, String oldPassword, String newPassword);

  UserDto changeEmail(UUID userId, String newEmail);

  String getPasswordHashByEmail(String email);
}
