package com.chrima.product.api.dto;

import com.chrima.product.api.enums.FulfilmentType;
import com.chrima.product.model.Product;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class ProductResponse {
  UUID id;
  UUID workspaceId;
  String name;
  String description;
  UUID walletId;
  FulfilmentType fulfilmentType;
  String externalUrl;
  List<String> roles;
  Instant createdAt;
  Instant updatedAt;

  public static ProductResponse from(Product product) {
    return ProductResponse.builder()
        .id(product.getId())
        .workspaceId(product.getWorkspaceId())
        .name(product.getName())
        .description(product.getDescription())
        .walletId(product.getWalletId())
        .fulfilmentType(product.getFulfilmentType())
        .externalUrl(product.getExternalUrl())
        .roles(product.getRoles())
        .createdAt(product.getCreatedAt())
        .updatedAt(product.getUpdatedAt())
        .build();
  }
}
