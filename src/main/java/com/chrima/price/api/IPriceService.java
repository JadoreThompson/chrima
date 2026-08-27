package com.chrima.price.api;

import com.chrima.price.api.dto.PriceResponse;
import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.api.enums.RecurringInterval;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

public interface IPriceService {

  PriceResponse create(
      UUID workspaceId,
      UUID productId,
      PriceType type,
      Currency currency,
      double amount,
      RecurringInterval recurringInterval,
      Integer recurringIntervalCount,
      Integer trialPeriodDays);

  PriceResponse getById(UUID priceId);

  PriceResponse get(UUID priceId, UUID workspaceId);

  Page<PriceResponse> listByProduct(UUID productId, Pageable pageable);

  default Page<PriceResponse> listByProduct(UUID productId, int page, int limit) {
    return listByProduct(productId, PageRequest.of(page - 1, limit));
  }

  PriceResponse update(
      UUID priceId,
      UUID workspaceId,
      Currency currency,
      Double amount,
      RecurringInterval recurringInterval,
      Integer recurringIntervalCount,
      Integer trialPeriodDays);

  void delete(UUID priceId, UUID workspaceId);
}
