"""Crypto provider interfaces for offline ingestion storage."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Protocol, Tuple, Type

Audit = Tuple[bool, str]


class CryptoProvider(Protocol):
    """Interface for encrypting/decrypting files within the stick."""

    name: str

    def encrypt_file(self, src: Path, dst: Path) -> Audit:
        ...

    def decrypt_file(self, src: Path, dst: Path) -> Audit:
        ...


@dataclass
class ProviderNone:
    name: str = "ProviderNone"

    def encrypt_file(self, src: Path, dst: Path) -> Audit:
        """Pass-through copy with audit noting lack of encryption."""
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        except OSError as exc:
            return False, f"Crypto provider NONE failed (unencrypted copy error: {exc})"
        return True, "Crypto provider NONE — unencrypted pass-through copy completed."

    def decrypt_file(self, src: Path, dst: Path) -> Audit:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        except OSError as exc:
            return False, f"Crypto provider NONE failed (unencrypted copy error: {exc})"
        return True, "Crypto provider NONE — unencrypted pass-through restore completed."


@dataclass
class ProviderCryptography:
    name: str = "ProviderCryptography"

    def encrypt_file(self, src: Path, dst: Path) -> Audit:
        return False, "Crypto provider Cryptography (AES-GCM) — NOT INSTALLED."

    def decrypt_file(self, src: Path, dst: Path) -> Audit:
        return False, "Crypto provider Cryptography (AES-GCM) — NOT INSTALLED."


@dataclass
class ProviderDPAPI:
    name: str = "ProviderDPAPI"

    def encrypt_file(self, src: Path, dst: Path) -> Audit:
        return False, "Crypto provider DPAPI (Windows) — NOT INSTALLED."

    def decrypt_file(self, src: Path, dst: Path) -> Audit:
        return False, "Crypto provider DPAPI (Windows) — NOT INSTALLED."


REGISTRY: Dict[str, Type[CryptoProvider]] = {
    "none": ProviderNone,
    "cryptography": ProviderCryptography,
    "dpapi": ProviderDPAPI,
}


def get_provider(name: str | None) -> CryptoProvider:
    key = (name or "none").lower()
    provider_cls = REGISTRY.get(key)
    if provider_cls is None:
        return ProviderNone()
    return provider_cls()
