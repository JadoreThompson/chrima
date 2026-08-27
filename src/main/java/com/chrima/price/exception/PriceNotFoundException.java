package com.chrima.price.exception;

import java.util.UUID;

public class PriceNotFoundException extends RuntimeException {

  private final UUID priceId;

  public PriceNotFoundException(UUID priceId) {
    super("Price not found");
    this.priceId = priceId;
  }

  public UUID getPriceId() {
    return priceId;
  }
}
