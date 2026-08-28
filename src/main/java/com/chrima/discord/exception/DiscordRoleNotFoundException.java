package com.chrima.discord.exception;

public class DiscordRoleNotFoundException extends RuntimeException {
  public DiscordRoleNotFoundException(String roleId) {
    super(String.format("Role %s not found", roleId));
  }
}
