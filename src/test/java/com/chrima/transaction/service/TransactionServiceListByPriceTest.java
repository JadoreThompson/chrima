package com.chrima.transaction.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.transaction.api.dto.TransactionResponse;
import com.chrima.transaction.api.enums.TransactionStatus;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;

class TransactionServiceListByPriceTest extends AbstractTransactionServiceIntegrationBase {

  @Test
  void shouldListByPriceOrderedByTimestampDesc() {
    UUID productId = UUID.randomUUID();
    UUID priceId = UUID.randomUUID();
    UUID older =
        createTransaction(productId, priceId, "0xsender", 10.0, TransactionStatus.COMPLETE, 100);
    UUID newer =
        createTransaction(productId, priceId, "0xsender", 20.0, TransactionStatus.COMPLETE, 200);
    createTransaction(
        productId, UUID.randomUUID(), "0xsender", 30.0, TransactionStatus.COMPLETE, 300);

    Page<TransactionResponse> page = transactionService.listByPrice(priceId, 1, 10);

    assertThat(page.getContent()).hasSize(2);
    assertThat(page.getContent().get(0).getId()).isEqualTo(newer);
    assertThat(page.getContent().get(1).getId()).isEqualTo(older);
  }

  @Test
  void shouldPaginateByPrice() {
    UUID productId = UUID.randomUUID();
    UUID priceId = UUID.randomUUID();
    createTransaction(productId, priceId, "0xsender", 10.0, TransactionStatus.COMPLETE, 100);
    createTransaction(productId, priceId, "0xsender", 20.0, TransactionStatus.COMPLETE, 200);
    createTransaction(productId, priceId, "0xsender", 30.0, TransactionStatus.COMPLETE, 300);

    Page<TransactionResponse> first = transactionService.listByPrice(priceId, 1, 2);

    assertThat(first.getContent()).hasSize(2);
    assertThat(first.hasNext()).isTrue();

    Page<TransactionResponse> second = transactionService.listByPrice(priceId, 2, 2);

    assertThat(second.getContent()).hasSize(1);
    assertThat(second.hasNext()).isFalse();
  }

  @Test
  void shouldReturnEmptyPageWhenPriceHasNoTransactions() {
    Page<TransactionResponse> page = transactionService.listByPrice(UUID.randomUUID(), 1, 10);

    assertThat(page.getContent()).isEmpty();
  }
}
