package com.chrima.user.exception;

import com.chrima.exception.GlobalExceptionHandler;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Exception handler for user-domain exceptions.
 *
 * <p>Mirrors {@code chrima-backend/src/chrima/api/middleware/exception_handler.py} mappings for the
 * user module:
 *
 * <ul>
 *   <li>{@link UserNotFoundException} -> 404
 *   <li>{@link UserValidationException} -> 422
 *   <li>{@link IncorrectPasswordException} -> 401
 * </ul>
 *
 * <p>Registered with highest precedence so that these typed handlers take priority over {@link
 * GlobalExceptionHandler}'s generic {@code Exception} handler.
 */
@Slf4j
@RestControllerAdvice
public class UserExceptionHandler {

  /**
   * Handles {@link UserNotFoundException} as 404 Not Found.
   *
   * @param ex the exception
   * @return 404 response
   */
  @ExceptionHandler(UserNotFoundException.class)
  public ResponseEntity<Void> handleUserNotFound(UserNotFoundException ex) {
    log.warn("User not found: {}", ex.getMessage());
    return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
  }

  /**
   * Handles {@link UserValidationException} as 422 Unprocessable Entity.
   *
   * @param ex the exception
   * @return 422 response
   */
  @ExceptionHandler(UserValidationException.class)
  public ResponseEntity<Void> handleUserValidation(UserValidationException ex) {
    String msg = ex.getMessage() != null ? ex.getMessage() : "User validation failed";
    log.warn("User validation error: {}", msg);
    return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).build();
  }

  /**
   * Handles {@link IncorrectPasswordException} as 401 Unauthorized.
   *
   * @param ex the exception
   * @return 401 response
   */
  @ExceptionHandler(IncorrectPasswordException.class)
  public ResponseEntity<Void> handleIncorrectPassword(IncorrectPasswordException ex) {
    log.warn("Incorrect password: {}", ex.getMessage());
    return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
  }
}
