package com.chrima.wallet.controller;

import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.JwtPayload;
import com.chrima.wallet.api.IWalletService;
import com.chrima.wallet.api.dto.WalletResponse;
import com.chrima.wallet.dto.CreateWalletRequest;
import com.chrima.workspace.api.IWorkspaceService;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Wallet controller exposing wallet-scoped endpoints.
 *
 * <p>Mirrors {@code chrima-backend/src/chrima/wallet/router.py}.
 */
@Slf4j
@RestController
@RequestMapping("/wallets")
@RequiredArgsConstructor
public class WalletController {

  private final IWalletService walletService;
  private final IWorkspaceService workspaceService;
  private final IJwtService jwtService;

  @PostMapping
  public ResponseEntity<WalletResponse> createWallet(
      @RequestBody CreateWalletRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    workspaceService.get(body.getWorkspaceId(), payload.getSubject());
    WalletResponse wallet =
        walletService.create(body.getWorkspaceId(), body.getName(), body.getWalletAddress());
    return ResponseEntity.status(HttpStatus.CREATED).body(wallet);
  }

  @GetMapping("/{walletId}")
  public ResponseEntity<WalletResponse> getWallet(
      @PathVariable UUID walletId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    jwtService.validate(token);
    return ResponseEntity.ok(walletService.getById(walletId));
  }

  @GetMapping
  public ResponseEntity<Page<WalletResponse>> listWallets(
      @RequestParam UUID workspaceId,
      @RequestParam(defaultValue = "1") int page,
      @RequestParam(defaultValue = "10") int limit,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    workspaceService.get(workspaceId, payload.getSubject());
    return ResponseEntity.ok(walletService.listByWorkspace(workspaceId, page, limit));
  }

  @DeleteMapping("/{walletId}")
  public ResponseEntity<Void> deleteWallet(
      @PathVariable UUID walletId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    WalletResponse wallet = walletService.getById(walletId);
    workspaceService.get(wallet.getWorkspaceId(), payload.getSubject());
    walletService.delete(walletId, wallet.getWorkspaceId());
    return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
  }
}
