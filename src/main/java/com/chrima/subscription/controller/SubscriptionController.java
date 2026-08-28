package com.chrima.subscription.controller;

import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.JwtPayload;
import com.chrima.product.api.IProductService;
import com.chrima.product.api.dto.ProductResponse;
import com.chrima.subscription.api.ISubscriptionService;
import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.workspace.api.IWorkspaceService;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Subscription controller exposing subscription-scoped endpoints.
 *
 * <p>Mirrors {@code chrima-backend/src/chrima/subscription/router.py}.
 */
@Slf4j
@RestController
@RequestMapping("/subscriptions")
@RequiredArgsConstructor
public class SubscriptionController {

  private final ISubscriptionService subscriptionService;
  private final IProductService productService;
  private final IWorkspaceService workspaceService;
  private final IJwtService jwtService;

  @PostMapping("/{subscriptionBalanceId}/cancel")
  public ResponseEntity<SubscriptionBalanceResponse> cancelSubscription(
      @PathVariable UUID subscriptionBalanceId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    SubscriptionBalanceResponse sub = subscriptionService.getById(subscriptionBalanceId);
    ProductResponse product = productService.getById(sub.getProductId());
    workspaceService.get(product.getWorkspaceId(), payload.getSubject());
    SubscriptionBalanceResponse cancelled = subscriptionService.cancel(subscriptionBalanceId);
    return ResponseEntity.ok(cancelled);
  }
}
