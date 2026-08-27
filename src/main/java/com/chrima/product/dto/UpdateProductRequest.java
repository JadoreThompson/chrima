package com.chrima.product.dto;

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
}
