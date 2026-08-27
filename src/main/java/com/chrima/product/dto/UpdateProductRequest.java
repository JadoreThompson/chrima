package com.chrima.product.dto;

import com.chrima.product.model.Product;
import java.util.List;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class UpdateProductRequest {
  String name;
  String description;
  UUID walletId;
  List<String> roles;
  String externalUrl;

  public static UpdateProductRequest from(Product product) {
    return UpdateProductRequest.builder()
        .name(product.getName())
        .description(product.getDescription())
        .walletId(product.getWalletId())
        .roles(product.getRoles())
        .externalUrl(product.getExternalUrl())
        .build();
  }
}
