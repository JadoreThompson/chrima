package com.chrima.subscription.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.model.SubscriptionBalance;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

class SubscriptionServiceCreateTest extends AbstractSubscriptionServiceIntegrationBase {

  @Test
  void shouldCreateBalanceAndPersist() {
    SubscriptionBalanceResponse created =
        createBalance("guild-1", "user-1", UUID.randomUUID(), 100.0, SubscriptionStatus.ACTIVE);

    assertThat(created.getId()).isNotNull();
    assertThat(created.getExternalId()).isEqualTo("guild-1");
    assertThat(created.getPlatformUserId()).isEqualTo("user-1");
    assertThat(created.getCreditAmount()).isEqualTo(100.0);
    assertThat(created.getStatus()).isEqualTo(SubscriptionStatus.ACTIVE);
    assertThat(created.getCycleStart()).isNull();
    assertThat(created.getCycleEnd()).isNull();
    assertThat(created.getLastProcessedTx()).isNull();
    assertThat(created.getAttemptCount()).isZero();
    assertThat(created.getLastNotifiedAt()).isNull();
    assertThat(created.getUpdatedAt()).isNotNull();

    SubscriptionBalance row = subscriptionBalanceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getExternalId()).isEqualTo("guild-1");
    assertThat(row.getPlatformUserId()).isEqualTo("user-1");
    assertThat(row.getCreditAmount()).isEqualTo(100.0);
    assertThat(row.getStatus()).isEqualTo(SubscriptionStatus.ACTIVE);
    assertThat(row.getAttemptCount()).isZero();
  }

  @Test
  void shouldCreateIncompleteBalance() {
    SubscriptionBalanceResponse created =
        createBalance("guild-1", "user-1", UUID.randomUUID(), 0.0, SubscriptionStatus.INCOMPLETE);

    assertThat(created.getStatus()).isEqualTo(SubscriptionStatus.INCOMPLETE);
    assertThat(created.getCreditAmount()).isZero();
  }

  @Test
  @Transactional(propagation = Propagation.NOT_SUPPORTED)
  void shouldThrowWhenDuplicateGroupAlreadyExists() {
    UUID productId = UUID.randomUUID();
    createBalance("guild-1", "user-1", productId, 50.0, SubscriptionStatus.ACTIVE);

    assertThatThrownBy(
            () -> createBalance("guild-1", "user-1", productId, 50.0, SubscriptionStatus.ACTIVE))
        .isInstanceOf(RuntimeException.class);
  }
}
