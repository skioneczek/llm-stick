"""Ingestion orchestration with source guard validation and crypto providers."""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Union

from services.indexer.build_index import build_index
from services.indexer.source import index_path_for_source, slug_for_source
from services.security import source_guard
from services.security.crypto_provider import CryptoProvider, ProviderNone

BYTES_PER_MB = 1024 * 1024
ENCRYPTED_DIR = Path("Data") / "encrypted_indexes"


class IngestDestination(str, Enum):
    HOST_LOCAL = "HOST_LOCAL"
    STICK_ENCRYPTED = "STICK_ENCRYPTED"


@dataclass
class IngestResult:
    ok: bool
    status: str
    audit: str
    metrics: Optional[Dict[str, Union[int, str]]] = None
    encryption: str = "plaintext"
    extra: Optional[Dict[str, str]] = None


def _destination_provider(destination: IngestDestination, provider: Optional[CryptoProvider]) -> CryptoProvider:
    if destination == IngestDestination.STICK_ENCRYPTED:
        return provider or ProviderNone()
    return provider or ProviderNone()


def queue_ingest(
    client: str,
    source: Path | str,
    destination: IngestDestination,
    *,
    provider: Optional[CryptoProvider] = None,
    force: bool = False,
) -> IngestResult:
    """Validate source and synchronously build index for ingestion."""
    source_path = Path(source).expanduser().resolve()

    ok, audit_line = source_guard.validate_source(str(source_path), force=force)
    if not ok:
        status = "confirm" if audit_line.startswith("Data source requires confirm") else "refused"
        print(audit_line)
        return IngestResult(ok=False, status=status, audit=audit_line)

    print(audit_line)
    print(f"Ingest job queued: {client} dest={destination.value}")

    index_path = index_path_for_source(source_path)
    metrics = build_index(source_path, index_path)

    size_mb = (metrics.get("size_bytes", 0) or 0) / BYTES_PER_MB if metrics else 0.0
    encryption_state = "plaintext"
    extra: Dict[str, str] = {"index_path": str(metrics.get("index_path", ""))} if metrics else {}

    provider_impl = _destination_provider(destination, provider)
    if destination == IngestDestination.STICK_ENCRYPTED:
        ENCRYPTED_DIR.mkdir(parents=True, exist_ok=True)
        encrypted_path = ENCRYPTED_DIR / f"index_{slug_for_source(source_path)}.bin"
        prov_ok, prov_audit = provider_impl.encrypt_file(Path(str(metrics.get("index_path", index_path))), encrypted_path)
        print(prov_audit)
        if not prov_ok:
            return IngestResult(ok=False, status="crypto-error", audit=prov_audit, metrics=metrics, encryption=encryption_state)
        extra["encrypted_path"] = str(encrypted_path)
        encryption_state = "encrypted" if "unencrypted" not in prov_audit.lower() else "plaintext"

    print(
        "Ingest job complete: "
        f"{client} (files {metrics['files']}, size {size_mb:.1f} MB, chunks {metrics['chunks']}) "
        f"[{encryption_state}]"
    )

    return IngestResult(
        ok=True,
        status="completed",
        audit=audit_line,
        metrics=metrics,
        encryption=encryption_state,
        extra=extra,
    )
