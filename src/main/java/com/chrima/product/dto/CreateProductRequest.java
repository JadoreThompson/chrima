package com.chrima.product.dto;

import com.chrima.product.api.enums.FulfilmentType;
import com.chrima.product.model.Product;
import java.util.List;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class CreateProductRequest {
  UUID workspaceId;
  String name;
  String description;
  UUID walletId;
  FulfilmentType fulfilmentType;
  String externalUrl;
  List<String> roles;

  public static CreateProductRequest from(Product product) {
    return CreateProductRequest.builder()
        .workspaceId(product.getWorkspaceId())
        .name(product.getName())
        .description(product.getDescription())
        .walletId(product.getWalletId())
        .fulfilmentType(product.getFulfilmentType())
        .externalUrl(product.getExternalUrl())
        .roles(product.getRoles())
        .build();
  }
}
