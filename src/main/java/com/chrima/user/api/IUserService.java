package com.chrima.user.api;

import com.chrima.user.dto.UserDto;
import com.chrima.user.model.User;
import com.chrima.user.model.enums.Tier;
import java.util.UUID;

public interface IUserService {

  User create(String username, String email, String password);

  UserDto getById(UUID userId);

  User findByEmail(String email);

  String getJwtToken(UUID userId);

  void setJwtToken(UUID userId, String jwtToken);

  void setTier(UUID userId, Tier tier);

  UserDto changeUsername(UUID userId, String newUsername);

  UserDto changePassword(UUID userId, String oldPassword, String newPassword);

  UserDto changeEmail(UUID userId, String newEmail);
}
