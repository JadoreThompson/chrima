package com.chrima.user.exception;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

class UserExceptionHandlerTest {

  private final UserExceptionHandler handler = new UserExceptionHandler();

  @Test
  void shouldMapUserNotFoundTo404() {
    ResponseEntity<Void> response = handler.handleUserNotFound(new UserNotFoundException());

    assertThat(response.getStatusCode().value()).isEqualTo(HttpStatus.NOT_FOUND.value());
  }

  @Test
  void shouldMapUserNotFoundWithMessageTo404() {
    ResponseEntity<Void> response =
        handler.handleUserNotFound(new UserNotFoundException("custom message"));

    assertThat(response.getStatusCode().value()).isEqualTo(HttpStatus.NOT_FOUND.value());
  }

  @Test
  void shouldMapUserValidationTo422() {
    ResponseEntity<Void> response =
        handler.handleUserValidation(new UserValidationException("duplicate username"));

    assertThat(response.getStatusCode().value()).isEqualTo(HttpStatus.UNPROCESSABLE_ENTITY.value());
  }

  @Test
  void shouldMapUserValidationWithoutMessageTo422() {
    ResponseEntity<Void> response = handler.handleUserValidation(new UserValidationException());

    assertThat(response.getStatusCode().value()).isEqualTo(HttpStatus.UNPROCESSABLE_ENTITY.value());
  }

  @Test
  void shouldMapIncorrectPasswordTo401() {
    ResponseEntity<Void> response =
        handler.handleIncorrectPassword(new IncorrectPasswordException());

    assertThat(response.getStatusCode().value()).isEqualTo(HttpStatus.UNAUTHORIZED.value());
  }
}
