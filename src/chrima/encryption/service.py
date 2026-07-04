import base64
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import ENCRYPTION_IV_LEN, ENCRYPTION_KEY
from .exception import IncorrectAADException


class EncryptionService:
    """Provides AES-GCM encryption and decryption utilities."""

    def __init__(self, key: str = ENCRYPTION_KEY, iv_len: int = ENCRYPTION_IV_LEN):
        self.key = key
        self.iv_len = iv_len

    def encrypt(self, payload: dict[str, Any], aad: str = "") -> str:
        """Encrypts a JSON-serializable payload using AES-GCM.

        Args:
            payload: The data to encrypt.
            aad: Optional additional authenticated data (AAD).

        Returns:
            Base64-encoded string containing the encrypted payload, IV, and metadata.
        """
        aesgcm = AESGCM(self.key.encode())
        iv = os.urandom(self.iv_len)
        plaintext = json.dumps(payload).encode("utf-8")
        aad_bytes = aad.encode("utf-8") if aad else None
        ct = aesgcm.encrypt(iv, plaintext, aad_bytes)
        result = {
            "version": "v1",
            "iv": base64.b64encode(iv).decode("ascii"),
            "ct": base64.b64encode(ct).decode("ascii"),
            "aad": aad,
        }
        return base64.b64encode(json.dumps(result).encode("utf-8")).decode("ascii")

    def decrypt(self, blob_b64: str, expected_aad: str = "") -> dict[str, Any]:
        """Decrypts a Base64-encoded AES-GCM payload.

        Args:
            blob_b64: The Base64-encoded ciphertext produced by `encrypt()`.
            expected_aad: Optional AAD value to verify against the encrypted data.

        Returns:
            The decrypted payload as a dictionary.

        Raises:
            EncryptionException: If AAD verification fails or decryption fails.
        """
        raw = base64.b64decode(blob_b64)
        obj = json.loads(raw.decode("utf-8"))

        if obj.get("aad", "") != expected_aad:
            raise IncorrectAADException(expected_aad, obj.get("aad", ""))

        iv = base64.b64decode(obj["iv"])
        ct = base64.b64decode(obj["ct"])
        aad_bytes = expected_aad.encode("utf-8") if expected_aad else None

        aesgcm = AESGCM(self.key.encode())
        pt = aesgcm.decrypt(iv, ct, aad_bytes)
        return json.loads(pt.decode("utf-8"))
