package com.chrima.product.api.dto;

import com.chrima.product.api.enums.FulfilmentType;
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
}
