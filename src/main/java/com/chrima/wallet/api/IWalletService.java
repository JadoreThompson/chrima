package com.chrima.wallet.api;

import com.chrima.wallet.dto.PaginatedWalletResponse;
import com.chrima.wallet.dto.WalletResponse;
import java.util.UUID;

public interface IWalletService {

  WalletResponse create(UUID workspaceId, String name, String walletAddress);

  WalletResponse getById(UUID walletId);

  WalletResponse get(UUID walletId, UUID workspaceId);

  PaginatedWalletResponse listByWorkspace(UUID workspaceId, int page, int limit);

  void delete(UUID walletId, UUID workspaceId);
}
