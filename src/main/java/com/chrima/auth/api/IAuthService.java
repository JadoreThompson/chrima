package com.chrima.auth.api;

import com.chrima.auth.api.dto.LoginRequest;
import com.chrima.auth.api.dto.RegisterRequest;
import com.chrima.user.api.dto.UserDto;

public interface IAuthService {

  UserDto register(RegisterRequest request);

  UserDto verifyCredentials(LoginRequest request);
}
