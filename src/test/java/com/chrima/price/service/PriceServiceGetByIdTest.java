package com.chrima.price.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.price.api.dto.PriceResponse;
import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.api.enums.RecurringInterval;
import com.chrima.price.exception.PriceNotFoundException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class PriceServiceGetByIdTest extends AbstractPriceServiceIntegrationBase {

  @Test
  void shouldGetById() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId,
            productId,
            PriceType.RECURRING,
            Currency.USD,
            12.5,
            RecurringInterval.DAY,
            1,
            null);

    PriceResponse fetched = priceService.getById(created.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getWorkspaceId()).isEqualTo(workspaceId);
    assertThat(fetched.getProductId()).isEqualTo(productId);
    assertThat(fetched.getType()).isEqualTo(PriceType.RECURRING);
    assertThat(fetched.getCurrency()).isEqualTo(Currency.USD);
    assertThat(fetched.getAmount()).isEqualTo(12.5);
    assertThat(fetched.getRecurringInterval()).isEqualTo(RecurringInterval.DAY);
    assertThat(fetched.getRecurringIntervalCount()).isEqualTo(1);
  }

  @Test
  void shouldThrowWhenGetByIdNotFound() {
    assertThatThrownBy(() -> priceService.getById(UUID.randomUUID()))
        .isInstanceOf(PriceNotFoundException.class);
  }
}
