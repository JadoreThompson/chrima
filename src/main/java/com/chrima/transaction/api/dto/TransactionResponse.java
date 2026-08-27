package com.chrima.transaction.api.dto;

import com.chrima.transaction.api.enums.TransactionStatus;
import com.chrima.transaction.model.Transaction;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class TransactionResponse {
  UUID id;
  UUID productId;
  UUID priceId;
  String sender;
  String address;
  double amount;
  TransactionStatus status;
  int timestamp;

  public static TransactionResponse from(Transaction transaction) {
    return TransactionResponse.builder()
        .id(transaction.getId())
        .productId(transaction.getProductId())
        .priceId(transaction.getPriceId())
        .sender(transaction.getSender())
        .address(transaction.getAddress())
        .amount(transaction.getAmount())
        .status(transaction.getStatus())
        .timestamp(transaction.getTimestamp())
        .build();
  }
}
