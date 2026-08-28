package com.chrima.price.controller;

import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.JwtPayload;
import com.chrima.price.api.IPriceService;
import com.chrima.price.api.dto.PriceResponse;
import com.chrima.price.dto.CreatePriceRequest;
import com.chrima.price.dto.UpdatePriceRequest;
import com.chrima.product.api.IProductService;
import com.chrima.workspace.api.IWorkspaceService;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Price controller exposing price-scoped endpoints. */
@Slf4j
@RestController
@RequestMapping("/prices")
@RequiredArgsConstructor
public class PriceController {

  private final IPriceService priceService;
  private final IProductService productService;
  private final IWorkspaceService workspaceService;
  private final IJwtService jwtService;

  @PostMapping
  public ResponseEntity<PriceResponse> createPrice(
      @RequestBody CreatePriceRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    workspaceService.get(body.getWorkspaceId(), payload.getSubject());
    PriceResponse price =
        priceService.create(
            body.getWorkspaceId(),
            body.getProductId(),
            body.getType(),
            body.getCurrency(),
            body.getAmount(),
            body.getRecurringInterval(),
            body.getRecurringIntervalCount(),
            body.getTrialPeriodDays());
    return ResponseEntity.status(HttpStatus.CREATED).body(price);
  }

  @GetMapping("/{priceId}")
  public ResponseEntity<PriceResponse> getPrice(@PathVariable UUID priceId) {
    return ResponseEntity.ok(priceService.getById(priceId));
  }

  @GetMapping
  public ResponseEntity<Page<PriceResponse>> listPrices(
      @RequestParam UUID productId,
      @RequestParam(defaultValue = "1") int page,
      @RequestParam(defaultValue = "10") int limit) {
    productService.getById(productId);
    return ResponseEntity.ok(priceService.listByProduct(productId, page, limit));
  }

  @PatchMapping("/{priceId}")
  public ResponseEntity<PriceResponse> updatePrice(
      @PathVariable UUID priceId,
      @RequestBody UpdatePriceRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    PriceResponse price = priceService.getById(priceId);
    workspaceService.get(price.getWorkspaceId(), payload.getSubject());
    PriceResponse updated =
        priceService.update(
            priceId,
            price.getWorkspaceId(),
            body.getCurrency(),
            body.getAmount(),
            body.getRecurringInterval(),
            body.getRecurringIntervalCount(),
            body.getTrialPeriodDays());
    return ResponseEntity.ok(updated);
  }

  @DeleteMapping("/{priceId}")
  public ResponseEntity<Void> deletePrice(
      @PathVariable UUID priceId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    PriceResponse price = priceService.getById(priceId);
    workspaceService.get(price.getWorkspaceId(), payload.getSubject());
    priceService.delete(priceId, price.getWorkspaceId());
    return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
  }
}
