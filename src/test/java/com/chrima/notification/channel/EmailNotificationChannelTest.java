package com.chrima.notification.channel;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentCaptor.forClass;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.EmailNotificationContent;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import software.amazon.awssdk.services.ses.SesClient;
import software.amazon.awssdk.services.ses.model.SendEmailRequest;
import software.amazon.awssdk.services.ses.model.SesException;

@ExtendWith(MockitoExtension.class)
class EmailNotificationChannelTest {

  @Mock private SesClient sesClient;

  private EmailNotificationChannel channel;

  private static final String FROM = "no-reply@chrima.local";

  @BeforeEach
  void setUp() {
    channel = new EmailNotificationChannel(sesClient, FROM);
  }

  @Test
  void dispatchShouldSendEmailViaSesWithCorrectFields() {
    EmailNotificationContent content = new EmailNotificationContent("Subject", "Hello body");
    String recipient = "user@example.com";

    channel.dispatch(recipient, content);

    ArgumentCaptor<SendEmailRequest> captor = forClass(SendEmailRequest.class);
    verify(sesClient).sendEmail(captor.capture());

    SendEmailRequest request = captor.getValue();
    assertEquals(FROM, request.source());
    assertEquals(recipient, request.destination().toAddresses().get(0));
    assertEquals("Subject", request.message().subject().data());
    assertEquals("Hello body", request.message().body().text().data());
  }

  @Test
  void supportsShouldReturnTrueOnlyForEmail() {
    assertTrue(channel.supports(ChannelType.EMAIL));
  }

  @Test
  void dispatchShouldPropagateSesException() {
    EmailNotificationContent content = new EmailNotificationContent("Sub", "Body");
    when(sesClient.sendEmail(org.mockito.ArgumentMatchers.any(SendEmailRequest.class)))
        .thenThrow(SesException.builder().message("SES failure").build());

    assertThrows(SesException.class, () -> channel.dispatch("user@example.com", content));
  }
}
