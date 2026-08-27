package com.chrima.wallet.dto;

import java.util.List;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class PaginatedWalletResponse {
  int page;
  int size;
  boolean hasNext;
  List<WalletResponse> data;
}
