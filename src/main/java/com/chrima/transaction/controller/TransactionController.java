package com.chrima.transaction.controller;

import com.chrima.jwt.api.IJwtService;
import com.chrima.transaction.api.ITransactionService;
import com.chrima.transaction.api.dto.TransactionResponse;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Transaction controller exposing transaction-scoped endpoints.
 *
 * <p>Mirrors {@code chrima-backend/src/chrima/transaction/router.py}.
 */
@Slf4j
@RestController
@RequestMapping("/transactions")
@RequiredArgsConstructor
public class TransactionController {

  private final ITransactionService transactionService;
  private final IJwtService jwtService;

  @GetMapping("/{transactionId}")
  public ResponseEntity<TransactionResponse> getTransaction(
      @PathVariable UUID transactionId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    jwtService.validate(token);
    return ResponseEntity.ok(transactionService.getById(transactionId));
  }

  @GetMapping
  public ResponseEntity<Page<TransactionResponse>> listTransactions(
      @RequestParam(required = false) UUID workspaceId,
      @RequestParam(required = false) String sender,
      @RequestParam(required = false) UUID productId,
      @RequestParam(required = false) UUID priceId,
      @RequestParam(defaultValue = "1") int page,
      @RequestParam(defaultValue = "10") int limit,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    jwtService.validate(token);
    Page<TransactionResponse> result =
        transactionService.list(workspaceId, productId, priceId, sender, page, limit);
    return ResponseEntity.ok(result);
  }
}
