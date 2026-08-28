package com.chrima.discord.exception;

public class DiscordChannelNotFoundException extends RuntimeException {
  public DiscordChannelNotFoundException(String channelId) {
    super(String.format("Channel %s not found", channelId));
  }
}
