"""AES-256-CBC field codec for DataBaseCompiled.

Wire format of each field: base64( marker[8] + iv[16] + ciphertext ).
The marker and key are the values already documented for this game.
"""

from __future__ import annotations

import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

AES_KEY: bytes = b"09234237536700238099172758697347"
MARKER: bytes = b"fhk3s0g3"


def aes_decrypt(blob_b64: str) -> bytes:
    """Decrypt one field. Raises ValueError when the marker is missing."""
    raw = base64.b64decode(blob_b64)
    if raw[:8] != MARKER:
        raise ValueError(f"missing marker (got {raw[:8]!r})")
    cipher = AES.new(AES_KEY, AES.MODE_CBC, raw[8:24])
    return unpad(cipher.decrypt(raw[24:]), 16)


def aes_encrypt(plaintext: bytes) -> str:
    """Encrypt plaintext with a fresh IV and return the base64 wire value."""
    iv = get_random_bytes(16)
    ciphertext = AES.new(AES_KEY, AES.MODE_CBC, iv).encrypt(pad(plaintext, 16))
    return base64.b64encode(MARKER + iv + ciphertext).decode("ascii")


def has_marker(blob_b64: str) -> bool:
    try:
        raw = base64.b64decode(blob_b64, validate=True)
    except Exception:
        return False
    return raw[:8] == MARKER
