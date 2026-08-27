package com.chrima.price.dto;

import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.RecurringInterval;
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
}
