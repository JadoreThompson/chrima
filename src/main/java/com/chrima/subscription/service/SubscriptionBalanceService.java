package com.chrima.subscription.service;

import com.chrima.events.api.IEventService;
import com.chrima.price.api.enums.RecurringInterval;
import com.chrima.subscription.api.ISubscriptionService;
import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.event.SubscriptionCancelledEvent;
import com.chrima.subscription.exception.SubscriptionBalanceAlreadyCancelledException;
import com.chrima.subscription.exception.SubscriptionBalanceNotFoundException;
import com.chrima.subscription.exception.SubscriptionBalanceValidationException;
import com.chrima.subscription.model.SubscriptionBalance;
import com.chrima.subscription.repository.SubscriptionBalanceRepository;
import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class SubscriptionBalanceService implements ISubscriptionService {

  private static final int DAY_SECONDS = 86400;
  private static final int MONTH_SECONDS = 2592000;

  private final SubscriptionBalanceRepository subscriptionBalanceRepository;
  private final IEventService eventService;

  @Override
  @Transactional(readOnly = true)
  public SubscriptionBalanceResponse get(String externalId, String platformUserId, UUID productId) {
    SubscriptionBalance balance = findBalance(externalId, platformUserId, productId);
    return SubscriptionBalanceResponse.from(balance);
  }

  @Override
  @Transactional(readOnly = true)
  public SubscriptionBalanceResponse getById(UUID subscriptionBalanceId) {
    SubscriptionBalance balance =
        subscriptionBalanceRepository
            .findById(subscriptionBalanceId)
            .orElseThrow(
                () -> {
                  log.warn("Subscription balance not found id={}", subscriptionBalanceId);
                  return new SubscriptionBalanceNotFoundException(subscriptionBalanceId);
                });
    return SubscriptionBalanceResponse.from(balance);
  }

  @Override
  @Transactional(readOnly = true)
  public List<SubscriptionBalanceResponse> listByUserGroup(long userId, long externalId) {
    return subscriptionBalanceRepository
        .findByPlatformUserIdAndExternalId(Long.toString(userId), Long.toString(externalId))
        .stream()
        .map(SubscriptionBalanceResponse::from)
        .toList();
  }

  @Override
  @Transactional
  public SubscriptionBalanceResponse create(
      String externalId,
      String platformUserId,
      UUID productId,
      double creditAmount,
      SubscriptionStatus status,
      Integer cycleStart,
      Integer cycleEnd,
      UUID lastProcessedTx) {
    log.info(
        "Creating subscription balance externalId={} platformUserId={} productId={} creditAmount={} status={}",
        externalId,
        platformUserId,
        productId,
        creditAmount,
        status);
    SubscriptionBalance balance =
        SubscriptionBalance.builder()
            .externalId(externalId)
            .platformUserId(platformUserId)
            .productId(productId)
            .creditAmount(creditAmount)
            .status(status)
            .cycleStart(cycleStart)
            .cycleEnd(cycleEnd)
            .lastProcessedTx(lastProcessedTx)
            .build();
    SubscriptionBalance saved = subscriptionBalanceRepository.saveAndFlush(balance);
    log.info("Subscription balance created id={} productId={}", saved.getId(), productId);
    return SubscriptionBalanceResponse.from(saved);
  }

  @Override
  @Transactional
  public SubscriptionBalanceResponse increaseBalance(
      String externalId, String platformUserId, UUID productId, double amount, UUID transactionId) {
    if (amount <= 0) {
      log.warn("Increase balance rejected - amount must be greater than zero amount={}", amount);
      throw new SubscriptionBalanceValidationException("Amount must be greater than zero");
    }
    if (transactionId == null) {
      log.warn("Increase balance rejected - transaction ID must be provided");
      throw new SubscriptionBalanceValidationException("Transaction ID must be provided");
    }

    SubscriptionBalance balance = findBalance(externalId, platformUserId, productId);
    balance.setCreditAmount(balance.getCreditAmount() + amount);
    balance.setLastProcessedTx(transactionId);
    SubscriptionBalance saved = subscriptionBalanceRepository.save(balance);
    log.info(
        "Subscription balance increased id={} amount={} creditAmount={}",
        saved.getId(),
        amount,
        saved.getCreditAmount());
    return SubscriptionBalanceResponse.from(saved);
  }

  @Override
  @Transactional
  public SubscriptionBalanceResponse processCycle(
      String externalId,
      String platformUserId,
      UUID productId,
      double amount,
      RecurringInterval recurringInterval,
      int recurringIntervalCount,
      UUID transactionId) {
    if (amount <= 0) {
      log.warn("Process cycle rejected - amount must be greater than zero amount={}", amount);
      throw new SubscriptionBalanceValidationException("Amount must be greater than zero");
    }
    if (transactionId == null) {
      log.warn("Process cycle rejected - transaction ID must be provided");
      throw new SubscriptionBalanceValidationException("Transaction ID must be provided");
    }

    SubscriptionBalance balance = findBalance(externalId, platformUserId, productId);
    balance.setCreditAmount(balance.getCreditAmount() - amount);
    long now = Instant.now().getEpochSecond();
    balance.setCycleStart((int) now);
    balance.setCycleEnd(computeCycleEnd(now, recurringInterval, recurringIntervalCount));
    balance.setLastProcessedTx(transactionId);
    SubscriptionBalance saved = subscriptionBalanceRepository.save(balance);
    log.info(
        "Subscription cycle processed id={} amount={} creditAmount={} cycleStart={} cycleEnd={}",
        saved.getId(),
        amount,
        saved.getCreditAmount(),
        saved.getCycleStart(),
        saved.getCycleEnd());
    return SubscriptionBalanceResponse.from(saved);
  }

  @Override
  @Transactional
  public SubscriptionBalanceResponse cancel(UUID subscriptionBalanceId) {
    SubscriptionBalance balance =
        subscriptionBalanceRepository
            .findById(subscriptionBalanceId)
            .orElseThrow(
                () -> {
                  log.warn(
                      "Subscription balance not found for cancel id={}", subscriptionBalanceId);
                  return new SubscriptionBalanceNotFoundException(subscriptionBalanceId);
                });
    if (balance.getStatus() == SubscriptionStatus.CANCELLED) {
      log.warn("Subscription balance already cancelled id={}", subscriptionBalanceId);
      throw new SubscriptionBalanceAlreadyCancelledException(subscriptionBalanceId);
    }

    balance.setStatus(SubscriptionStatus.CANCELLED);
    SubscriptionBalance saved = subscriptionBalanceRepository.save(balance);
    publishSubscriptionCancelled(saved);
    log.info("Subscription balance cancelled id={}", subscriptionBalanceId);
    return SubscriptionBalanceResponse.from(saved);
  }

  private SubscriptionBalance findBalance(
      String externalId, String platformUserId, UUID productId) {
    return subscriptionBalanceRepository
        .findByExternalIdAndPlatformUserIdAndProductId(externalId, platformUserId, productId)
        .orElseThrow(
            () -> {
              log.warn(
                  "Subscription balance not found externalId={} platformUserId={} productId={}",
                  externalId,
                  platformUserId,
                  productId);
              return new SubscriptionBalanceNotFoundException(
                  externalId, platformUserId, productId);
            });
  }

  private int computeCycleEnd(
      long start, RecurringInterval recurringInterval, int recurringIntervalCount) {
    return switch (recurringInterval) {
      case DAY -> (int) (start + DAY_SECONDS * recurringIntervalCount);
      case MONTH -> (int) (start + MONTH_SECONDS * recurringIntervalCount);
    };
  }

  private void publishSubscriptionCancelled(SubscriptionBalance balance) {
    try {
      eventService.publish(
          SubscriptionCancelledEvent.EVENT_TYPE,
          SubscriptionCancelledEvent.builder()
              .subscriptionBalanceId(balance.getId())
              .externalId(balance.getExternalId())
              .platformUserId(balance.getPlatformUserId())
              .productId(balance.getProductId())
              .build(),
          UUID.randomUUID().toString());
    } catch (IOException e) {
      log.error(
          "Failed to publish SubscriptionCancelledEvent subscriptionBalanceId={}",
          balance.getId(),
          e);
      throw new IllegalStateException("Failed to publish SubscriptionCancelledEvent", e);
    }
  }
}
