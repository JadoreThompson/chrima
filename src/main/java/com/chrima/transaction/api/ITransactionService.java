package com.chrima.transaction.api;

import com.chrima.transaction.api.dto.TransactionResponse;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

public interface ITransactionService {

  TransactionResponse getById(UUID transactionId);

  Page<TransactionResponse> listBySender(String sender, Pageable pageable);

  default Page<TransactionResponse> listBySender(String sender, int page, int limit) {
    return listBySender(sender, PageRequest.of(page - 1, limit));
  }

  Page<TransactionResponse> listByProduct(UUID productId, Pageable pageable);

  default Page<TransactionResponse> listByProduct(UUID productId, int page, int limit) {
    return listByProduct(productId, PageRequest.of(page - 1, limit));
  }

  Page<TransactionResponse> listByPrice(UUID priceId, Pageable pageable);

  default Page<TransactionResponse> listByPrice(UUID priceId, int page, int limit) {
    return listByPrice(priceId, PageRequest.of(page - 1, limit));
  }

  Page<TransactionResponse> list(
      UUID workspaceId, UUID productId, UUID priceId, String sender, Pageable pageable);

  default Page<TransactionResponse> list(
      UUID workspaceId, UUID productId, UUID priceId, String sender, int page, int limit) {
    return list(workspaceId, productId, priceId, sender, PageRequest.of(page - 1, limit));
  }
}
