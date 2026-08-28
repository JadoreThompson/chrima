package com.chrima.discord.encryption;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.Map;
import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * Provides AES-GCM encryption and decryption utilities mirroring {@code
 * chrima-backend/src/chrima/encryption/service.py}.
 *
 * <p>Encrypted blobs are Base64-encoded JSON envelopes: {@code {"version":"v1","iv":..., "ct":...,
 * "aad":...}}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class EncryptionService {

  private static final String TRANSFORMATION = "AES/GCM/NoPadding";
  private static final String ALGORITHM = "AES";
  private static final int IV_LENGTH = 12;
  private static final int TAG_LENGTH_BITS = 128;

  private final ObjectMapper objectMapper;

  @Value("${encryption.key:0123456789abcdef0123456789abcdef}")
  private String key;

  public String encrypt(Map<String, Object> payload, String aad) {
    try {
      byte[] keyBytes = getKey();
      Cipher cipher = Cipher.getInstance(TRANSFORMATION);
      byte[] iv = new byte[IV_LENGTH];
      new SecureRandom().nextBytes(iv);
      GCMParameterSpec spec = new GCMParameterSpec(TAG_LENGTH_BITS, iv);
      cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(keyBytes, ALGORITHM), spec);
      if (aad != null && !aad.isEmpty()) {
        cipher.updateAAD(aad.getBytes(StandardCharsets.UTF_8));
      }
      byte[] ct = cipher.doFinal(objectMapper.writeValueAsBytes(payload));

      ObjectNode envelope = objectMapper.createObjectNode();
      envelope.put("version", "v1");
      envelope.put("iv", Base64.getEncoder().encodeToString(iv));
      envelope.put("ct", Base64.getEncoder().encodeToString(ct));
      envelope.put("aad", aad);
      return Base64.getEncoder().encodeToString(objectMapper.writeValueAsBytes(envelope));
    } catch (Exception e) {
      log.error("Failed to encrypt payload", e);
      throw new IllegalStateException("Failed to encrypt payload", e);
    }
  }

  public Map<String, Object> decrypt(String blobB64, String expectedAad) {
    try {
      byte[] raw = Base64.getDecoder().decode(blobB64);
      JsonNode obj = objectMapper.readTree(raw);
      String aad = obj.path("aad").asText("");
      if (!aad.equals(expectedAad)) {
        throw new IllegalStateException(
            String.format("Incorrect AAD: expected=%s actual=%s", expectedAad, aad));
      }
      byte[] iv = Base64.getDecoder().decode(obj.get("iv").asText());
      byte[] ct = Base64.getDecoder().decode(obj.get("ct").asText());

      Cipher cipher = Cipher.getInstance(TRANSFORMATION);
      GCMParameterSpec spec = new GCMParameterSpec(TAG_LENGTH_BITS, iv);
      cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(getKey(), ALGORITHM), spec);
      if (expectedAad != null && !expectedAad.isEmpty()) {
        cipher.updateAAD(expectedAad.getBytes(StandardCharsets.UTF_8));
      }
      byte[] plain = cipher.doFinal(ct);
      return objectMapper.readValue(plain, new TypeReference<Map<String, Object>>() {});
    } catch (Exception e) {
      log.error("Failed to decrypt payload", e);
      throw new IllegalStateException("Failed to decrypt payload", e);
    }
  }

  private byte[] getKey() {
    return key.getBytes(StandardCharsets.UTF_8);
  }
}
