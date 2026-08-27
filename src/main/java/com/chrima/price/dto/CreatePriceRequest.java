package com.chrima.price.dto;

import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.api.enums.RecurringInterval;
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
}
