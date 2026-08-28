package com.chrima.discord.exception;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Exception handler for discord-domain exceptions.
 *
 * <p>Mirrors {@code chrima-backend/src/chrima/api/middleware/exception_handler.py} mappings for the
 * discord module:
 *
 * <ul>
 *   <li>{@link DiscordAccessTokenNotFoundException} -> 403
 *   <li>{@link UserDiscordAccessTokenNotFoundException} -> 403
 *   <li>{@link DiscordUserNotFoundException}, {@link DiscordGuildNotFoundException}, {@link
 *       DiscordChannelNotFoundException}, {@link DiscordRoleNotFoundException} -> 404
 *   <li>{@link DiscordApiException} (upstream Discord API failure) -> 502
 * </ul>
 */
@Slf4j
@RestControllerAdvice
public class DiscordExceptionHandler {

  @ExceptionHandler({
    DiscordAccessTokenNotFoundException.class,
    UserDiscordAccessTokenNotFoundException.class
  })
  public ResponseEntity<Void> handleTokenNotFound(Exception ex) {
    log.warn("Discord access token not found: {}", ex.getMessage());
    return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
  }

  @ExceptionHandler({
    DiscordUserNotFoundException.class,
    DiscordGuildNotFoundException.class,
    DiscordChannelNotFoundException.class,
    DiscordRoleNotFoundException.class
  })
  public ResponseEntity<Void> handleNotFound(Exception ex) {
    log.warn("Discord resource not found: {}", ex.getMessage());
    return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
  }

  @ExceptionHandler(DiscordApiException.class)
  public ResponseEntity<Void> handleDiscordApi(DiscordApiException ex) {
    log.error("Discord upstream API failure: {}", ex.getMessage());
    return ResponseEntity.status(HttpStatus.BAD_GATEWAY).build();
  }
}
