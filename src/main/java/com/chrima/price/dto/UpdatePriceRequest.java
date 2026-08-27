package com.chrima.price.dto;

import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.RecurringInterval;
import com.chrima.price.model.Price;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class UpdatePriceRequest {
  Currency currency;
  Double amount;
  RecurringInterval recurringInterval;
  Integer recurringIntervalCount;
  Integer trialPeriodDays;

  public static UpdatePriceRequest from(Price price) {
    return UpdatePriceRequest.builder()
        .currency(price.getCurrency())
        .amount(price.getAmount())
        .recurringInterval(price.getRecurringInterval())
        .recurringIntervalCount(price.getRecurringIntervalCount())
        .trialPeriodDays(price.getTrialPeriodDays())
        .build();
  }
}
