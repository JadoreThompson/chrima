package com.chrima.discord.exception;

public class DiscordUserNotInGuildException extends RuntimeException {
  public DiscordUserNotInGuildException(long userId, long guildId) {
    super(String.format("User %d is not a member of guild %d", userId, guildId));
  }
}
