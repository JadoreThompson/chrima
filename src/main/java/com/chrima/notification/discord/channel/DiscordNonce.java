package com.chrima.notification.discord.channel;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

public final class DiscordNonce {

  private static final int MAX_LENGTH = 25;

  private DiscordNonce() {}

  public static String from(String idempotencyKey) {
    return sha256(idempotencyKey).substring(0, MAX_LENGTH);
  }

  private static String sha256(String value) {
    try {
      MessageDigest digest = MessageDigest.getInstance("SHA-256");
      return HexFormat.of().formatHex(digest.digest(value.getBytes(StandardCharsets.UTF_8)));
    } catch (NoSuchAlgorithmException e) {
      throw new IllegalStateException("SHA-256 not available", e);
    }
  }
}
