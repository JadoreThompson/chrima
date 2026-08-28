package com.chrima.discord.exception;

import java.util.UUID;

public class UserDiscordAccessTokenNotFoundException extends RuntimeException {
  public UserDiscordAccessTokenNotFoundException(UUID userId) {
    super(String.format("Discord access token for user not found (user_id=%s)", userId));
  }
}
