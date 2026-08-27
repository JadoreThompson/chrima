package com.chrima.price.api.dto;

import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.api.enums.RecurringInterval;
import com.chrima.price.model.Price;
import java.time.Instant;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class PriceResponse {
  UUID id;
  UUID workspaceId;
  UUID productId;
  PriceType type;
  Currency currency;
  double amount;
  RecurringInterval recurringInterval;
  Integer recurringIntervalCount;
  Integer trialPeriodDays;
  Instant createdAt;
  Instant updatedAt;

  public static PriceResponse from(Price price) {
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
