package com.chrima.auth.exception;

public class InvalidLoginCredentialsException extends RuntimeException {

  public InvalidLoginCredentialsException() {
    super("Invalid login credentials.");
  }
}
