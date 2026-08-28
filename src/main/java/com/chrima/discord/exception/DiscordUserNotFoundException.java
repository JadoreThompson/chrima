package com.chrima.discord.exception;

import java.util.UUID;

public class DiscordUserNotFoundException extends RuntimeException {
  public DiscordUserNotFoundException(UUID userId) {
    super(String.format("Discord user not found for Chrima user %s", userId));
  }

  public DiscordUserNotFoundException(long discordUserId) {
    super(String.format("Discord user %d not found", discordUserId));
  }
}
