package com.chrima.discord.exception;

public class DiscordGuildNotFoundException extends RuntimeException {
  public DiscordGuildNotFoundException(String guildId) {
    super(String.format("Guild %s not found", guildId));
  }
}
