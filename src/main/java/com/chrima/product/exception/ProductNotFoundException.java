package com.chrima.product.exception;

import java.util.UUID;

public class ProductNotFoundException extends RuntimeException {

  private final UUID productId;

  public ProductNotFoundException(UUID productId) {
    super("Product not found");
    this.productId = productId;
  }

  public UUID getProductId() {
    return productId;
  }
}
