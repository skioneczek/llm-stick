# Crypto Provider Policy

## Overview
- Default provider: `ProviderNone` (plaintext pass-through). Emits audit `Crypto provider NONE — unencrypted pass-through copy completed.` and is always available offline.
- Optional providers:
  - `ProviderCryptography` — AES-GCM implementation shipped via drop-in wheel (offline install). Until wheel present, audits `Crypto provider Cryptography (AES-GCM) — NOT INSTALLED.`
  - `ProviderDPAPI` — Windows DPAPI wrapper. Until native module present, audits `Crypto provider DPAPI (Windows) — NOT INSTALLED.`
- Provider registry lives in `services/security/crypto_provider.py`. Drop-in packages must expose the same class names and methods to replace stubs.

## Enabling AES-GCM Offline
1. Build or obtain an offline wheel providing `ProviderCryptography` with AES-GCM support (must depend only on bundled libraries).
2. Copy wheel to the stick and install into the isolated environment (no network). Verify import succeeds.
3. Confirm `get_provider("cryptography")` returns an operational provider by running the self-test snippet below.
4. Never exfiltrate keys: key material must be generated/stored within encrypted `Data/security/` volumes and never written to host paths.

```python
from pathlib import Path
from services.security.crypto_provider import get_provider

test_provider = get_provider("cryptography")
ok, msg = test_provider.encrypt_file(Path("Data/tmp/plain.txt"), Path("Data/tmp/plain.txt.enc"))
print(ok, msg)
```

## DPAPI Notes (Windows Only)
- The `ProviderDPAPI` placeholder audits `NOT INSTALLED` until a native binding is provided.
- Any DPAPI implementation must store the protected blob under `Data/encrypted_indexes/` and avoid writing to host paths.

## Operational Policy
- `IngestDestination.HOST_LOCAL` uses `ProviderNone` (plaintext) but still records audits for traceability.
- `IngestDestination.STICK_ENCRYPTED` requires a crypto provider; until one is installed the flow should refuse with the provider’s audit message.
- All ingest actions log:
  - `Ingest job queued: <client> dest=<HOST_LOCAL|STICK_ENCRYPTED>`
  - `Ingest job complete: <client> (files X, size Y MB, chunks Z) [encrypted|plaintext]`
- Hotswap between clients must emit `Hotswap activated: <client>` after source validation succeeds.

## Self-Check After Provider Changes
1. Run `python -m services.indexer.ingest --self-test` (future Day-3 hook) or manual snippet above.
2. Ensure `Data/tmp/` wiped after testing.
3. Record audit outcome in acceptance logs.
