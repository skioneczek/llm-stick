"""Secure configuration helpers using PIN-derived keys."""
from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _derive_key(pin: str) -> bytes:
    if not pin:
        raise ValueError("PIN required for key derivation")
    return hashlib.sha256(pin.encode("utf-8")).digest()


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


def encrypt_text(pin: str, plaintext: str) -> str:
    key = _derive_key(pin)
    data = plaintext.encode("utf-8")
    payload = _xor_bytes(data, key)
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decrypt_text(pin: str, ciphertext: str) -> str:
    key = _derive_key(pin)
    raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    data = _xor_bytes(raw, key)
    return data.decode("utf-8")


@dataclass
class SecureConfig:
    """Lightweight PIN-scoped configuration storage."""

    root: Path

    def _path(self, key: str) -> Path:
        return self.root / f"{key}.json.enc"

    def write(self, key: str, pin: str, payload: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        encoded = encrypt_text(pin, json_dumps(payload))
        self._path(key).write_text(encoded, encoding="utf-8")

    def read(self, key: str, pin: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            decoded = decrypt_text(pin, path.read_text(encoding="utf-8"))
            return json_loads(decoded)
        except Exception:
            return None


# Local JSON helpers avoid importing json at module import time (for packaging speed).

def json_dumps(value: dict[str, Any]) -> str:
    import json

    return json.dumps(value, indent=2, sort_keys=True)


def json_loads(data: str) -> dict[str, Any]:
    import json

    return json.loads(data)
