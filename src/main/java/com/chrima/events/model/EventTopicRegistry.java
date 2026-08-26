package com.chrima.events.model;

import com.chrima.events.api.EventType;
import java.util.HashMap;
import java.util.Map;
import org.springframework.beans.factory.config.BeanDefinition;
import org.springframework.context.annotation.ClassPathScanningCandidateComponentProvider;
import org.springframework.core.type.filter.AnnotationTypeFilter;
import org.springframework.stereotype.Component;

@Component
public class EventTopicRegistry {

  private final Map<String, String> topicByEventType;

  public EventTopicRegistry() {
    this.topicByEventType = buildRegistry();
  }

  public EventTopicRegistry(Map<String, String> topicByEventType) {
    this.topicByEventType = Map.copyOf(topicByEventType);
  }

  public void register(String eventType, String topic) {
    if (eventType == null || eventType.isBlank() || topic == null || topic.isBlank()) {
      throw new IllegalArgumentException("event type and topic must not be null or empty");
    }
    topicByEventType.put(eventType, topic);
  }

  public String getTopic(String eventType) {
    String topic = topicByEventType.get(eventType);
    if (topic == null) {
      throw new IllegalArgumentException("No topic registered for event type " + eventType);
    }
    return topic;
  }

  public boolean contains(String eventType) {
    return topicByEventType.containsKey(eventType);
  }

  private static Map<String, String> buildRegistry() {
    ClassPathScanningCandidateComponentProvider scanner =
        new ClassPathScanningCandidateComponentProvider(false);
    scanner.addIncludeFilter(new AnnotationTypeFilter(EventType.class));
    Map<String, String> map = new HashMap<>();

    for (BeanDefinition bd : scanner.findCandidateComponents("com.chrima")) {
      try {
        Class<?> clazz = Class.forName(bd.getBeanClassName());
        EventType annotation = clazz.getAnnotation(EventType.class);
        if (annotation == null) {
          continue;
        }
        String eventType = annotation.value();
        String topic = annotation.topic();
        if (eventType == null || eventType.isBlank() || topic == null || topic.isBlank()) {
          continue;
        }
        if (map.containsKey(eventType)) {
          throw new IllegalStateException("Duplicate event type: " + eventType);
        }
        map.put(eventType, topic);
      } catch (ClassNotFoundException e) {
        throw new IllegalStateException(
            "Failed to load event type class " + bd.getBeanClassName(), e);
      }
    }

    return map;
  }
}
