package com.chrima.product.controller;

import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.JwtPayload;
import com.chrima.product.api.IProductService;
import com.chrima.product.api.dto.ProductResponse;
import com.chrima.product.dto.CreateProductRequest;
import com.chrima.product.dto.UpdateProductRequest;
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

/**
 * Product controller exposing product-scoped endpoints.
 *
 * <p>Mirrors {@code chrima-backend/src/chrima/product/router.py}.
 */
@Slf4j
@RestController
@RequestMapping("/products")
@RequiredArgsConstructor
public class ProductController {

  private final IProductService productService;
  private final IWorkspaceService workspaceService;
  private final IJwtService jwtService;

  @PostMapping
  public ResponseEntity<ProductResponse> createProduct(
      @RequestBody CreateProductRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    workspaceService.get(body.getWorkspaceId(), payload.getSubject());
    ProductResponse product =
        productService.create(
            body.getWorkspaceId(),
            body.getName(),
            body.getDescription(),
            body.getWalletId(),
            body.getExternalUrl(),
            body.getRoles(),
            body.getFulfilmentType());
    return ResponseEntity.status(HttpStatus.CREATED).body(product);
  }

  @GetMapping("/{productId}")
  public ResponseEntity<ProductResponse> getProduct(@PathVariable UUID productId) {
    return ResponseEntity.ok(productService.getById(productId));
  }

  @GetMapping
  public ResponseEntity<Page<ProductResponse>> listProducts(
      @RequestParam UUID workspaceId,
      @RequestParam(defaultValue = "1") int page,
      @RequestParam(defaultValue = "10") int limit) {
    workspaceService.getById(workspaceId);
    return ResponseEntity.ok(productService.listByWorkspace(workspaceId, page, limit));
  }

  @PatchMapping("/{productId}")
  public ResponseEntity<ProductResponse> updateProduct(
      @PathVariable UUID productId,
      @RequestBody UpdateProductRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    ProductResponse product = productService.getById(productId);
    workspaceService.get(product.getWorkspaceId(), payload.getSubject());
    ProductResponse updated =
        productService.update(
            productId,
            product.getWorkspaceId(),
            body.getName(),
            body.getDescription(),
            body.getWalletId(),
            body.getRoles(),
            body.getExternalUrl());
    return ResponseEntity.ok(updated);
  }

  @DeleteMapping("/{productId}")
  public ResponseEntity<Void> deleteProduct(
      @PathVariable UUID productId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    ProductResponse product = productService.getById(productId);
    workspaceService.get(product.getWorkspaceId(), payload.getSubject());
    productService.delete(productId, product.getWorkspaceId());
    return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
  }
}
