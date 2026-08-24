package com.chrima.notification.discord.model;

import com.chrima.notification.discord.api.DiscordNotificationType;
import com.chrima.notification.discord.api.IDiscordNotificationContent;
import java.util.HashMap;
import java.util.Map;
import org.springframework.beans.factory.config.BeanDefinition;
import org.springframework.context.annotation.ClassPathScanningCandidateComponentProvider;
import org.springframework.core.type.filter.AnnotationTypeFilter;
import org.springframework.stereotype.Component;

@Component
public class DiscordNotificationContentRegistry {

  private final Map<String, Class<? extends IDiscordNotificationContent>> registry;

  public DiscordNotificationContentRegistry() {
    this.registry = buildRegistry();
  }

  // Visible for testing
  public DiscordNotificationContentRegistry(
      Map<String, Class<? extends IDiscordNotificationContent>> registry) {
    this.registry = Map.copyOf(registry);
  }

  public Class<? extends IDiscordNotificationContent> get(String type) {
    Class<? extends IDiscordNotificationContent> clazz = registry.get(type);
    if (clazz == null) {
      throw new IllegalArgumentException(
          "No Discord notification content type registered for " + type);
    }
    return clazz;
  }

  public Map<String, Class<? extends IDiscordNotificationContent>> getAll() {
    return registry;
  }

  private static Map<String, Class<? extends IDiscordNotificationContent>> buildRegistry() {
    ClassPathScanningCandidateComponentProvider scanner =
        new ClassPathScanningCandidateComponentProvider(false);
    scanner.addIncludeFilter(new AnnotationTypeFilter(DiscordNotificationType.class));
    Map<String, Class<? extends IDiscordNotificationContent>> map = new HashMap<>();
    for (BeanDefinition bd : scanner.findCandidateComponents("com.chrima")) {
      try {
        Class<?> clazz = Class.forName(bd.getBeanClassName());
        if (!IDiscordNotificationContent.class.isAssignableFrom(clazz)) {
          continue;
        }
        @SuppressWarnings("unchecked")
        Class<? extends IDiscordNotificationContent> contentClass =
            (Class<? extends IDiscordNotificationContent>) clazz;
        DiscordNotificationType annotation = clazz.getAnnotation(DiscordNotificationType.class);
        if (annotation == null) {
          continue;
        }
        String type = annotation.value();
        if (map.containsKey(type)) {
          throw new IllegalStateException("Duplicate Discord notification type: " + type);
        }
        map.put(type, contentClass);
      } catch (ClassNotFoundException e) {
        throw new IllegalStateException(
            "Failed to load Discord notification content class " + bd.getBeanClassName(), e);
      }
    }
    return Map.copyOf(map);
  }
}
