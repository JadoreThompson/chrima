package com.chrima.user.exception;

public class IncorrectPasswordException extends RuntimeException {

  public IncorrectPasswordException() {
    super("Incorrect password.");
  }
}
