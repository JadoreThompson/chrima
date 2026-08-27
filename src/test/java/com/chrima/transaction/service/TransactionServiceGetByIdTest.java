package com.chrima.transaction.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.transaction.api.dto.TransactionResponse;
import com.chrima.transaction.api.enums.TransactionStatus;
import com.chrima.transaction.exception.TransactionNotFoundException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class TransactionServiceGetByIdTest extends AbstractTransactionServiceIntegrationBase {

  @Test
  void shouldGetById() {
    UUID productId = UUID.randomUUID();
    UUID priceId = UUID.randomUUID();
    UUID id =
        createTransaction(
            productId, priceId, "0xsender", 100.0, TransactionStatus.COMPLETE, 1700000000);

    TransactionResponse fetched = transactionService.getById(id);

    assertThat(fetched.getId()).isEqualTo(id);
    assertThat(fetched.getProductId()).isEqualTo(productId);
    assertThat(fetched.getPriceId()).isEqualTo(priceId);
    assertThat(fetched.getSender()).isEqualTo("0xsender");
    assertThat(fetched.getAddress()).isEqualTo("0xsender");
    assertThat(fetched.getAmount()).isEqualTo(100.0);
    assertThat(fetched.getStatus()).isEqualTo(TransactionStatus.COMPLETE);
    assertThat(fetched.getTimestamp()).isEqualTo(1700000000);
  }

  @Test
  void shouldThrowWhenGetByIdNotFound() {
    assertThatThrownBy(() -> transactionService.getById(UUID.randomUUID()))
        .isInstanceOf(TransactionNotFoundException.class);
  }
}
