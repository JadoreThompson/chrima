package com.chrima.wallet.service;

import com.chrima.wallet.api.IWalletService;
import com.chrima.wallet.dto.WalletResponse;
import com.chrima.wallet.exception.WalletNotFoundException;
import com.chrima.wallet.model.Wallet;
import com.chrima.wallet.repository.WalletRepository;
import com.chrima.workspace.api.IWorkspaceService;
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
public class WalletService implements IWalletService {

  private final WalletRepository walletRepository;
  private final IWorkspaceService workspaceService;

  @Override
  @Transactional
  public WalletResponse create(UUID workspaceId, String name, String walletAddress) {
    log.info("Creating wallet workspaceId={} name={}", workspaceId, name);
    workspaceService.getById(workspaceId);
    Wallet wallet =
        Wallet.builder().workspaceId(workspaceId).name(name).walletAddress(walletAddress).build();
    Wallet saved = walletRepository.saveAndFlush(wallet);
    log.info("Wallet created id={} workspaceId={}", saved.getId(), workspaceId);
    return toResponse(saved);
  }

  @Override
  @Transactional(readOnly = true)
  public WalletResponse getById(UUID walletId) {
    Wallet wallet =
        walletRepository
            .findById(walletId)
            .orElseThrow(
                () -> {
                  log.warn("Wallet not found id={}", walletId);
                  return new WalletNotFoundException(walletId);
                });
    return toResponse(wallet);
  }

  @Override
  @Transactional(readOnly = true)
  public WalletResponse get(UUID walletId, UUID workspaceId) {
    Wallet wallet =
        walletRepository
            .findByIdAndWorkspaceId(walletId, workspaceId)
            .orElseThrow(
                () -> {
                  log.warn("Wallet not found id={} workspaceId={}", walletId, workspaceId);
                  return new WalletNotFoundException(walletId);
                });
    return toResponse(wallet);
  }

  @Override
  @Transactional(readOnly = true)
  public Page<WalletResponse> listByWorkspace(UUID workspaceId, Pageable pageable) {
    return walletRepository.findByWorkspaceId(workspaceId, pageable).map(this::toResponse);
  }

  @Override
  @Transactional
  public void delete(UUID walletId, UUID workspaceId) {
    Wallet wallet = walletRepository.findById(walletId).orElse(null);
    if (wallet == null || !wallet.getWorkspaceId().equals(workspaceId)) {
      log.warn("Wallet not found for delete id={} workspaceId={}", walletId, workspaceId);
      throw new WalletNotFoundException(walletId);
    }
    // Product in-use check is not enforced yet because product module is not present.
    // When product entity exists, uncomment the check below via injected ProductRepository.
    walletRepository.delete(wallet);
    log.info("Wallet deleted id={} workspaceId={}", walletId, workspaceId);
  }

  private WalletResponse toResponse(Wallet wallet) {
    return WalletResponse.builder()
        .id(wallet.getId())
        .workspaceId(wallet.getWorkspaceId())
        .name(wallet.getName())
        .walletAddress(wallet.getWalletAddress())
        .createdAt(wallet.getCreatedAt())
        .build();
  }
}
