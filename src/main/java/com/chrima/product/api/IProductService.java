package com.chrima.product.api;

import com.chrima.product.api.dto.ProductResponse;
import com.chrima.product.api.enums.FulfilmentType;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

public interface IProductService {

  ProductResponse create(
      UUID workspaceId,
      String name,
      String description,
      UUID walletId,
      FulfilmentType fulfilmentType,
      String externalUrl,
      List<String> roles);

  default ProductResponse create(
      UUID workspaceId,
      String name,
      String description,
      UUID walletId,
      String externalUrl,
      List<String> roles,
      FulfilmentType fulfilmentType) {
    return create(workspaceId, name, description, walletId, fulfilmentType, externalUrl, roles);
  }

  ProductResponse getById(UUID productId);

  ProductResponse get(UUID productId, UUID workspaceId);

  Page<ProductResponse> listByWorkspace(UUID workspaceId, Pageable pageable);

  default Page<ProductResponse> listByWorkspace(UUID workspaceId, int page, int limit) {
    return listByWorkspace(workspaceId, PageRequest.of(page - 1, limit));
  }

  ProductResponse update(
      UUID productId,
      UUID workspaceId,
      String name,
      String description,
      UUID walletId,
      List<String> roles,
      String externalUrl);

  default ProductResponse update(
      UUID productId, UUID workspaceId, String name, String description, UUID walletId) {
    return update(productId, workspaceId, name, description, walletId, null, null);
  }

  void delete(UUID productId, UUID workspaceId);
}
