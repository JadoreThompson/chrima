package com.chrima.notification.config;

import java.net.URI;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.ses.SesClient;

@Configuration
public class AwsSesConfig {

  @Bean
  public SesClient sesClient(
      @Value("${aws.ses.endpoint:http://localhost:4566}") String endpoint,
      @Value("${aws.region:us-east-1}") String region,
      @Value("${aws.access-key:test}") String accessKey,
      @Value("${aws.secret-key:test}") String secretKey) {
    return SesClient.builder()
        .endpointOverride(URI.create(endpoint))
        .region(Region.of(region))
        .credentialsProvider(
            StaticCredentialsProvider.create(AwsBasicCredentials.create(accessKey, secretKey)))
        .build();
  }
}
