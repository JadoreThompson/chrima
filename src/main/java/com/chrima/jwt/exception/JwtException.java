package com.chrima.jwt.exception;

public class JwtException extends RuntimeException {

  public JwtException(String message) {
    super(message);
  }

  public JwtException(String message, Throwable cause) {
    super(message, cause);
  }
}
