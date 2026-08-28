package com.chrima.discord.client;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.LinkedHashMap;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

/** Small JSON utilities for the Discord API client. */
@Component
@RequiredArgsConstructor
public class JsonUtil {

  private static final TypeReference<LinkedHashMap<String, Object>> MAP_TYPE =
      new TypeReference<LinkedHashMap<String, Object>>() {};

  private final ObjectMapper objectMapper;

  public Map<String, Object> toMap(JsonNode node) {
    return objectMapper.convertValue(node, MAP_TYPE);
  }
}
