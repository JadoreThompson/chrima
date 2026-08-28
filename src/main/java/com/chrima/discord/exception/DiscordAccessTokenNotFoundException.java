package com.chrima.discord.exception;

public class DiscordAccessTokenNotFoundException extends RuntimeException {
  public DiscordAccessTokenNotFoundException(long discordUserId) {
    super(String.format("Access token for Discord user %d not found", discordUserId));
  }
}
