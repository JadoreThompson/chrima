package com.chrima.product.service;

import com.chrima.product.api.IProductService;
import com.chrima.product.api.dto.ProductResponse;
import com.chrima.product.api.enums.FulfilmentType;
import com.chrima.product.exception.ProductNotFoundException;
import com.chrima.product.model.Product;
import com.chrima.product.repository.ProductRepository;
import com.chrima.wallet.api.IWalletService;
import com.chrima.workspace.api.IWorkspaceService;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class ProductService implements IProductService {

  private final ProductRepository productRepository;
  private final IWorkspaceService workspaceService;
  private final IWalletService walletService;

  @Override
  @Transactional
  public ProductResponse create(
      UUID workspaceId,
      String name,
      String description,
      UUID walletId,
      FulfilmentType fulfilmentType,
      String externalUrl,
      List<String> roles) {
    log.info(
        "Creating product workspaceId={} name={} fulfilmentType={}",
        workspaceId,
        name,
        fulfilmentType);
    workspaceService.getById(workspaceId);
    walletService.getById(walletId);
    Product product =
        Product.builder()
            .workspaceId(workspaceId)
            .name(name)
            .description(description)
            .walletId(walletId)
            .fulfilmentType(fulfilmentType)
            .externalUrl(externalUrl)
            .roles(roles)
            .build();
    Product saved = productRepository.saveAndFlush(product);
    log.info("Product created id={} workspaceId={}", saved.getId(), workspaceId);
    return toResponse(saved);
  }

  @Override
  @Transactional(readOnly = true)
  public ProductResponse getById(UUID productId) {
    Product product =
        productRepository
            .findById(productId)
            .orElseThrow(
                () -> {
                  log.warn("Product not found id={}", productId);
                  return new ProductNotFoundException(productId);
                });
    return toResponse(product);
  }

  @Override
  @Transactional(readOnly = true)
  public ProductResponse get(UUID productId, UUID workspaceId) {
    Product product =
        productRepository
            .findByIdAndWorkspaceId(productId, workspaceId)
            .orElseThrow(
                () -> {
                  log.warn("Product not found id={} workspaceId={}", productId, workspaceId);
                  return new ProductNotFoundException(productId);
                });
    return toResponse(product);
  }

  @Override
  @Transactional(readOnly = true)
  public Page<ProductResponse> listByWorkspace(UUID workspaceId, Pageable pageable) {
    return productRepository.findByWorkspaceId(workspaceId, pageable).map(this::toResponse);
  }

  @Override
  @Transactional
  public ProductResponse update(
      UUID productId,
      UUID workspaceId,
      String name,
      String description,
      UUID walletId,
      List<String> roles,
      String externalUrl) {
    Product product =
        productRepository
            .findByIdAndWorkspaceId(productId, workspaceId)
            .orElseThrow(
                () -> {
                  log.warn(
                      "Product not found for update id={} workspaceId={}", productId, workspaceId);
                  return new ProductNotFoundException(productId);
                });
    if (name != null) {
      product.setName(name);
    }
    if (description != null) {
      product.setDescription(description);
    }
    if (walletId != null && !walletId.equals(product.getWalletId())) {
      walletService.getById(walletId);
      product.setWalletId(walletId);
    }
    if (roles != null) {
      product.setRoles(roles);
    }
    if (externalUrl != null) {
      product.setExternalUrl(externalUrl);
    }
    Product saved = productRepository.save(product);
    log.info("Product updated id={} workspaceId={}", productId, workspaceId);
    return toResponse(saved);
  }

  @Override
  @Transactional
  public void delete(UUID productId, UUID workspaceId) {
    Product product =
        productRepository
            .findByIdAndWorkspaceId(productId, workspaceId)
            .orElseThrow(
                () -> {
                  log.warn(
                      "Product not found for delete id={} workspaceId={}", productId, workspaceId);
                  return new ProductNotFoundException(productId);
                });
    productRepository.delete(product);
    log.info("Product deleted id={} workspaceId={}", productId, workspaceId);
  }

  private ProductResponse toResponse(Product product) {
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
