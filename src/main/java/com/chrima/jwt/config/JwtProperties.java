package com.chrima.jwt.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Getter
@Setter
@Configuration
@ConfigurationProperties(prefix = "jwt")
public class JwtProperties {

  /** HS256 secret; must be at least 32 bytes for HS256. */
  private String secret = "mega-super-duper-uper-secret-key";

  private String algo = "HS256";

  private long expirySecs = 100000000L;

  private String cookieAlias = "chrima-cookie";

  private boolean secure = false;
}
