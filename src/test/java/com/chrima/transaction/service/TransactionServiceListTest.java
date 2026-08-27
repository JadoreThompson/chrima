package com.chrima.transaction.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.transaction.api.dto.TransactionResponse;
import com.chrima.transaction.api.enums.TransactionStatus;
import com.chrima.transaction.exception.TransactionFilterException;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;

class TransactionServiceListTest extends AbstractTransactionServiceIntegrationBase {

  @Test
  void shouldThrowWhenNoFilterProvided() {
    assertThatThrownBy(() -> transactionService.list(null, null, null, null, 1, 10))
        .isInstanceOf(TransactionFilterException.class);
  }

  @Test
  void shouldListByWorkspace() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = UUID.randomUUID();
    UUID priceId = createPrice(workspaceId, productId);
    UUID older =
        createTransaction(productId, priceId, "0xsender", 10.0, TransactionStatus.COMPLETE, 100);
    UUID newer =
        createTransaction(productId, priceId, "0xsender", 20.0, TransactionStatus.COMPLETE, 200);
    UUID otherWorkspaceId = UUID.randomUUID();
    UUID otherPriceId = createPrice(otherWorkspaceId, UUID.randomUUID());
    createTransaction(
        UUID.randomUUID(), otherPriceId, "0xother", 30.0, TransactionStatus.COMPLETE, 300);

    Page<TransactionResponse> page = transactionService.list(workspaceId, null, null, null, 1, 10);

    assertThat(page.getContent()).hasSize(2);
    assertThat(page.getContent().get(0).getId()).isEqualTo(newer);
    assertThat(page.getContent().get(1).getId()).isEqualTo(older);
  }

  @Test
  void shouldCombineProductPriceAndSenderFilters() {
    UUID productId = UUID.randomUUID();
    UUID priceId = createPrice(UUID.randomUUID(), productId);
    UUID matching =
        createTransaction(productId, priceId, "0xsender", 10.0, TransactionStatus.COMPLETE, 100);
    createTransaction(productId, priceId, "0xother", 20.0, TransactionStatus.COMPLETE, 200);
    createTransaction(
        productId, UUID.randomUUID(), "0xsender", 30.0, TransactionStatus.COMPLETE, 300);

    Page<TransactionResponse> page =
        transactionService.list(null, productId, priceId, "0xsender", 1, 10);

    assertThat(page.getContent()).hasSize(1);
    assertThat(page.getContent().get(0).getId()).isEqualTo(matching);
  }

  @Test
  void shouldListBySender() {
    UUID productId = UUID.randomUUID();
    UUID priceId = createPrice(UUID.randomUUID(), productId);
    createTransaction(productId, priceId, "0xsender", 10.0, TransactionStatus.COMPLETE, 100);
    createTransaction(productId, priceId, "0xother", 20.0, TransactionStatus.COMPLETE, 200);

    Page<TransactionResponse> page = transactionService.list(null, null, null, "0xsender", 1, 10);

    assertThat(page.getContent()).hasSize(1);
    assertThat(page.getContent().get(0).getSender()).isEqualTo("0xsender");
  }

  @Test
  void shouldReturnEmptyPageWhenNoTransactionMatchesFilters() {
    UUID productId = UUID.randomUUID();
    UUID priceId = createPrice(UUID.randomUUID(), productId);
    createTransaction(productId, priceId, "0xsender", 10.0, TransactionStatus.COMPLETE, 100);

    Page<TransactionResponse> page =
        transactionService.list(null, productId, null, "0xnobody", 1, 10);

    assertThat(page.getContent()).isEmpty();
  }
}
