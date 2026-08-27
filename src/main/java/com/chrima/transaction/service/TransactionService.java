package com.chrima.transaction.service;

import com.chrima.transaction.api.ITransactionService;
import com.chrima.transaction.api.dto.TransactionResponse;
import com.chrima.transaction.exception.TransactionFilterException;
import com.chrima.transaction.exception.TransactionNotFoundException;
import com.chrima.transaction.model.Transaction;
import com.chrima.transaction.repository.TransactionRepository;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class TransactionService implements ITransactionService {

  private final TransactionRepository transactionRepository;

  @Override
  @Transactional(readOnly = true)
  public TransactionResponse getById(UUID transactionId) {
    Transaction transaction =
        transactionRepository
            .findById(transactionId)
            .orElseThrow(
                () -> {
                  log.warn("Transaction not found id={}", transactionId);
                  return new TransactionNotFoundException(transactionId);
                });
    return TransactionResponse.from(transaction);
  }

  @Override
  @Transactional(readOnly = true)
  public Page<TransactionResponse> listBySender(String sender, Pageable pageable) {
    return transactionRepository
        .findBySenderOrderByTimestampDesc(sender, pageable)
        .map(TransactionResponse::from);
  }

  @Override
  @Transactional(readOnly = true)
  public Page<TransactionResponse> listByProduct(UUID productId, Pageable pageable) {
    return transactionRepository
        .findByProductIdOrderByTimestampDesc(productId, pageable)
        .map(TransactionResponse::from);
  }

  @Override
  @Transactional(readOnly = true)
  public Page<TransactionResponse> listByPrice(UUID priceId, Pageable pageable) {
    return transactionRepository
        .findByPriceIdOrderByTimestampDesc(priceId, pageable)
        .map(TransactionResponse::from);
  }

  @Override
  @Transactional(readOnly = true)
  public Page<TransactionResponse> list(
      UUID workspaceId, UUID productId, UUID priceId, String sender, Pageable pageable) {
    if (workspaceId == null && productId == null && priceId == null && sender == null) {
      log.warn("Transaction list rejected - at least one filter parameter is required");
      throw new TransactionFilterException();
    }
    return transactionRepository
        .findFiltered(workspaceId, productId, priceId, sender, pageable)
        .map(TransactionResponse::from);
  }
}
