package com.chrima;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class ChrimaApplication {

  public static void main(String[] args) {
    SpringApplication.run(ChrimaApplication.class, args);
  }
}
