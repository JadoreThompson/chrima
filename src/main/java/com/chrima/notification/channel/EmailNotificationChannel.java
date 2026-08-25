package com.chrima.notification.channel;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.EmailNotificationContent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import software.amazon.awssdk.services.ses.SesClient;
import software.amazon.awssdk.services.ses.model.Body;
import software.amazon.awssdk.services.ses.model.Content;
import software.amazon.awssdk.services.ses.model.Destination;
import software.amazon.awssdk.services.ses.model.Message;
import software.amazon.awssdk.services.ses.model.SendEmailRequest;

@Slf4j
@Component
public class EmailNotificationChannel implements INotificationChannel<EmailNotificationContent> {

  private final SesClient sesClient;
  private final String fromAddress;

  public EmailNotificationChannel(
      SesClient sesClient, @Value("${aws.ses.from:no-reply@chrima.local}") String fromAddress) {
    this.sesClient = sesClient;
    this.fromAddress = fromAddress;
  }

  @Override
  public boolean supports(ChannelType channelType) {
    return channelType == ChannelType.EMAIL;
  }

  @Override
  public void dispatch(String recipient, EmailNotificationContent content) {
    log.info(
        "Sending email via SES recipient={} subject='{}' from={}",
        recipient,
        content.subject(),
        fromAddress);
    try {
      SendEmailRequest request =
          SendEmailRequest.builder()
              .source(fromAddress)
              .destination(Destination.builder().toAddresses(recipient).build())
              .message(
                  Message.builder()
                      .subject(Content.builder().data(content.subject()).build())
                      .body(
                          Body.builder()
                              .text(Content.builder().data(content.body()).build())
                              .build())
                      .build())
              .build();
      sesClient.sendEmail(request);
      log.info("Email dispatched via SES recipient={} subject='{}'", recipient, content.subject());
    } catch (Exception e) {
      log.error(
          "Failed to send email via SES recipient={} subject='{}'",
          recipient,
          content.subject(),
          e);
      throw e;
    }
  }
}
