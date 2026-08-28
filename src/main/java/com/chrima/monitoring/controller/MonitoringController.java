package com.chrima.monitoring.controller;

import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Monitoring controller exposing health endpoints. */
@Slf4j
@RestController
@RequestMapping("/monitoring")
public class MonitoringController {

  @GetMapping("/health")
  public ResponseEntity<Map<String, String>> getHealth() {
    return ResponseEntity.ok(Map.of("status", "ok"));
  }
}
