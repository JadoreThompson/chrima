package com.chrima.product.dto;

import com.chrima.product.model.enums.FulfilmentType;
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
}
