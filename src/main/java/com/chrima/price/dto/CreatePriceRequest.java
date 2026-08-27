package com.chrima.price.dto;

import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.api.enums.RecurringInterval;
import com.chrima.price.model.Price;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class CreatePriceRequest {
  UUID workspaceId;
  UUID productId;
  PriceType type;
  Currency currency;
  double amount;
  RecurringInterval recurringInterval;
  Integer recurringIntervalCount;
  Integer trialPeriodDays;

  public static CreatePriceRequest from(Price price) {
    return CreatePriceRequest.builder()
        .workspaceId(price.getWorkspaceId())
        .productId(price.getProductId())
        .type(price.getType())
        .currency(price.getCurrency())
        .amount(price.getAmount())
        .recurringInterval(price.getRecurringInterval())
        .recurringIntervalCount(price.getRecurringIntervalCount())
        .trialPeriodDays(price.getTrialPeriodDays())
        .build();
  }
}
