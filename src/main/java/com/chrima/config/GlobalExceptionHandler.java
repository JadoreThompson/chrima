package com.chrima.config;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingRequestCookieException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

  @ExceptionHandler(MissingRequestCookieException.class)
  public ResponseEntity<Void> handleMissingCookie(MissingRequestCookieException ex) {
    return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
  }

  @ExceptionHandler(IllegalArgumentException.class)
  public ResponseEntity<Void> handleIllegalArg(IllegalArgumentException ex) {
    return ResponseEntity.status(HttpStatus.BAD_REQUEST).build();
  }

  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<Void> handleValidationException(MethodArgumentNotValidException ex) {
    return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).build();
  }

  @ExceptionHandler(Exception.class)
  public ResponseEntity<Void> handleGeneric(Exception ex) {
    String cn = ex.getClass().getName();
    if (cn.equals("com.chrima.jwt.exception.JwtException")
        || cn.equals("com.chrima.auth.exception.InvalidLoginCredentialsException")
        || cn.equals("com.chrima.user.exception.IncorrectPasswordException")) {
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
    }
    if (cn.equals("com.chrima.user.exception.UserValidationException")) {
      return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).build();
    }
    if (cn.equals("com.chrima.workspace.exception.WorkspaceNotFoundException")
        || cn.equals("com.chrima.user.exception.UserNotFoundException")) {
      return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
    }
    // Unknown exception: propagate as 500
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
  }
}
