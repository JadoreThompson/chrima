package com.chrima.price.service;

import com.chrima.events.api.IEventService;
import com.chrima.price.api.IPriceService;
import com.chrima.price.api.dto.PriceResponse;
import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.api.enums.RecurringInterval;
import com.chrima.price.event.PriceUpdatedEvent;
import com.chrima.price.exception.PriceNotFoundException;
import com.chrima.price.exception.PriceValidationException;
import com.chrima.price.model.Price;
import com.chrima.price.repository.PriceRepository;
import com.chrima.product.api.IProductService;
import com.chrima.workspace.api.IWorkspaceService;
import java.io.IOException;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class PriceService implements IPriceService {

  private final PriceRepository priceRepository;
  private final IWorkspaceService workspaceService;
  private final IProductService productService;
  private final IEventService eventService;

  @Override
  @Transactional
  public PriceResponse create(
      UUID workspaceId,
      UUID productId,
      PriceType type,
      Currency currency,
      double amount,
      RecurringInterval recurringInterval,
      Integer recurringIntervalCount,
      Integer trialPeriodDays) {
    log.info(
        "Creating price workspaceId={} productId={} type={} currency={} amount={}",
        workspaceId,
        productId,
        type,
        currency,
        amount);
    if (amount <= 0) {
      log.warn("Price create rejected - amount must be greater than zero amount={}", amount);
      throw new PriceValidationException("Amount must be greater than zero");
    }
    workspaceService.getById(workspaceId);
    productService.getById(productId);
    Price price =
        Price.builder()
            .workspaceId(workspaceId)
            .productId(productId)
            .type(type)
            .currency(currency)
            .amount(amount)
            .recurringInterval(recurringInterval)
            .recurringIntervalCount(recurringIntervalCount)
            .trialPeriodDays(trialPeriodDays)
            .build();
    Price saved = priceRepository.saveAndFlush(price);
    publishPriceUpdated(saved);
    log.info("Price created id={} productId={} amount={}", saved.getId(), productId, amount);
    return toResponse(saved);
  }

  @Override
  @Transactional(readOnly = true)
  public PriceResponse getById(UUID priceId) {
    Price price =
        priceRepository
            .findById(priceId)
            .orElseThrow(
                () -> {
                  log.warn("Price not found id={}", priceId);
                  return new PriceNotFoundException(priceId);
                });
    return toResponse(price);
  }

  @Override
  @Transactional(readOnly = true)
  public PriceResponse get(UUID priceId, UUID workspaceId) {
    Price price =
        priceRepository
            .findByIdAndWorkspaceId(priceId, workspaceId)
            .orElseThrow(
                () -> {
                  log.warn("Price not found id={} workspaceId={}", priceId, workspaceId);
                  return new PriceNotFoundException(priceId);
                });
    return toResponse(price);
  }

  @Override
  @Transactional(readOnly = true)
  public Page<PriceResponse> listByProduct(UUID productId, Pageable pageable) {
    productService.getById(productId);
    return priceRepository.findByProductId(productId, pageable).map(this::toResponse);
  }

  @Override
  @Transactional
  public PriceResponse update(
      UUID priceId,
      UUID workspaceId,
      Currency currency,
      Double amount,
      RecurringInterval recurringInterval,
      Integer recurringIntervalCount,
      Integer trialPeriodDays) {
    Price price =
        priceRepository
            .findByIdAndWorkspaceId(priceId, workspaceId)
            .orElseThrow(
                () -> {
                  log.warn("Price not found for update id={} workspaceId={}", priceId, workspaceId);
                  return new PriceNotFoundException(priceId);
                });
    if (amount != null && amount <= 0) {
      log.warn("Price update rejected - amount must be greater than zero amount={}", amount);
      throw new PriceValidationException("Amount must be greater than zero");
    }
    if (currency != null) {
      price.setCurrency(currency);
    }
    if (amount != null) {
      price.setAmount(amount);
    }
    if (recurringInterval != null) {
      price.setRecurringInterval(recurringInterval);
    }
    if (recurringIntervalCount != null) {
      price.setRecurringIntervalCount(recurringIntervalCount);
    }
    if (trialPeriodDays != null) {
      price.setTrialPeriodDays(trialPeriodDays);
    }
    Price saved = priceRepository.save(price);
    publishPriceUpdated(saved);
    log.info(
        "Price updated id={} workspaceId={} amount={}", priceId, workspaceId, saved.getAmount());
    return toResponse(saved);
  }

  @Override
  @Transactional
  public void delete(UUID priceId, UUID workspaceId) {
    Price price =
        priceRepository
            .findByIdAndWorkspaceId(priceId, workspaceId)
            .orElseThrow(
                () -> {
                  log.warn("Price not found for delete id={} workspaceId={}", priceId, workspaceId);
                  return new PriceNotFoundException(priceId);
                });
    priceRepository.delete(price);
    log.info("Price deleted id={} workspaceId={}", priceId, workspaceId);
  }

  private void publishPriceUpdated(Price price) {
    try {
      eventService.publish(
          PriceUpdatedEvent.EVENT_TYPE,
          PriceUpdatedEvent.builder().priceId(price.getId()).amount(price.getAmount()).build(),
          UUID.randomUUID().toString());
    } catch (IOException e) {
      log.error("Failed to publish PriceUpdatedEvent priceId={}", price.getId(), e);
      throw new IllegalStateException("Failed to publish PriceUpdatedEvent", e);
    }
  }

  private PriceResponse toResponse(Price price) {
    return PriceResponse.builder()
        .id(price.getId())
        .workspaceId(price.getWorkspaceId())
        .productId(price.getProductId())
        .type(price.getType())
        .currency(price.getCurrency())
        .amount(price.getAmount())
        .recurringInterval(price.getRecurringInterval())
        .recurringIntervalCount(price.getRecurringIntervalCount())
        .trialPeriodDays(price.getTrialPeriodDays())
        .createdAt(price.getCreatedAt())
        .updatedAt(price.getUpdatedAt())
        .build();
  }
}
