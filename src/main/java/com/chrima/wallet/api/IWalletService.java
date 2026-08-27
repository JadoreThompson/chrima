package com.chrima.wallet.api;

import com.chrima.wallet.dto.WalletResponse;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

public interface IWalletService {

  WalletResponse create(UUID workspaceId, String name, String walletAddress);

  WalletResponse getById(UUID walletId);

  WalletResponse get(UUID walletId, UUID workspaceId);

  Page<WalletResponse> listByWorkspace(UUID workspaceId, Pageable pageable);

  default Page<WalletResponse> listByWorkspace(UUID workspaceId, int page, int limit) {
    return listByWorkspace(workspaceId, PageRequest.of(page - 1, limit));
  }

  void delete(UUID walletId, UUID workspaceId);
}
