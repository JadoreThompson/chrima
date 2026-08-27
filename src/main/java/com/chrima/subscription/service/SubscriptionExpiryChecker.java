package com.chrima.subscription.service;

import com.chrima.notification.discord.api.IDiscordNotificationContent;
import com.chrima.notification.discord.api.IDiscordNotificationService;
import com.chrima.product.api.IProductService;
import com.chrima.product.api.dto.ProductResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.config.SubscriptionExpiryProperties;
import com.chrima.subscription.model.SubscriptionBalance;
import com.chrima.subscription.notification.SubscriptionExpiredNotificationContent;
import com.chrima.subscription.notification.SubscriptionExpiringNotificationContent;
import com.chrima.subscription.repository.SubscriptionBalanceRepository;
import com.chrima.workspace.api.IWorkspaceService;
import com.chrima.workspace.api.dto.WorkspaceResponse;
import java.time.Instant;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(
    name = "subscription.expiry.enabled",
    havingValue = "true",
    matchIfMissing = true)
public class SubscriptionExpiryChecker {

  private final SubscriptionBalanceRepository subscriptionBalanceRepository;
  private final IProductService productService;
  private final IWorkspaceService workspaceService;
  private final IDiscordNotificationService discordNotificationService;
  private final SubscriptionExpiryProperties properties;

  @Scheduled(
      fixedDelayString = "${subscription.expiry.fixed-delay}",
      initialDelayString = "${subscription.expiry.initial-delay}")
  @Transactional
  public void checkExpirations() {
    long now = Instant.now().getEpochSecond();
    long windowEnd = now + properties.getExpiryWindow();
    long cooldownBefore = now - properties.getNotificationCooldown();
    List<SubscriptionBalance> balances =
        subscriptionBalanceRepository.findDueForExpiryCheck(
            properties.getMaxAttempts(),
            windowEnd,
            now,
            cooldownBefore,
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELLED);

    if (balances.isEmpty()) {
      log.debug(
          "Subscription expiry checker - no balances due for expiry window={} cooldown={} maxAttempts={}",
          properties.getExpiryWindow(),
          properties.getNotificationCooldown(),
          properties.getMaxAttempts());
      return;
    }

    log.info(
        "Subscription expiry checker - processing balances size={} maxAttempts={}",
        balances.size(),
        properties.getMaxAttempts());

    for (SubscriptionBalance balance : balances) {
      processExpiry(balance, now);
    }

    log.info("Subscription expiry checker - batch completed processed={}", balances.size());
  }

  private void processExpiry(SubscriptionBalance balance, long now) {
    ProductResponse product;
    try {
      product = productService.getById(balance.getProductId());
    } catch (RuntimeException e) {
      log.warn(
          "Product {} not found, skipping expiry for subscription balance id={}",
          balance.getProductId(),
          balance.getId(),
          e);
      return;
    }

    WorkspaceResponse workspace;
    try {
      workspace = workspaceService.getById(product.getWorkspaceId());
    } catch (RuntimeException e) {
      log.warn(
          "Workspace for product {} not found, skipping expiry for subscription balance id={}",
          product.getId(),
          balance.getId(),
          e);
      return;
    }

    boolean expired = balance.getCycleEnd() < now;
    IDiscordNotificationContent content =
        expired
            ? new SubscriptionExpiredNotificationContent(
                workspace.getExternalId(),
                workspace.getNotificationChannelId(),
                balance.getPlatformUserId(),
                balance.getProductId(),
                product.getName(),
                balance.getCycleEnd())
            : new SubscriptionExpiringNotificationContent(
                workspace.getExternalId(),
                workspace.getNotificationChannelId(),
                balance.getPlatformUserId(),
                balance.getProductId(),
                product.getName(),
                balance.getCycleEnd());

    String type =
        expired
            ? SubscriptionExpiredNotificationContent.TYPE
            : SubscriptionExpiringNotificationContent.TYPE;
    String idempotencyKey =
        "subscription-expiry:"
            + balance.getId()
            + ":"
            + (expired ? "expired" : "expiring")
            + ":"
            + balance.getCycleEnd();

    discordNotificationService.publish(
        Long.valueOf(workspace.getExternalId()),
        Long.valueOf(workspace.getNotificationChannelId()),
        type,
        content,
        idempotencyKey);

    if (expired) {
      balance.setStatus(SubscriptionStatus.EXPIRED);
    }
    balance.setAttemptCount(balance.getAttemptCount() + 1);
    balance.setLastNotifiedAt((int) now);
    subscriptionBalanceRepository.save(balance);
    log.info(
        "Subscription expiry notified id={} productId={} expired={} attemptCount={}",
        balance.getId(),
        balance.getProductId(),
        expired,
        balance.getAttemptCount());
  }
}
