# Smoke Test — Day 1
Environment: Windows (PowerShell 5.1), offline air-gapped workstation.

1) Launch `Start-*` → wrappers set `LLM_STICK_ROOT`; PIN pad displays in large-text mode, Voice Mode off by default.
2) Enter the 6-digit PIN → preflight runs; Standard mode audit prints “proceeding” line in `Data/logs/audits.log`.
3) Accept default host alias (`C:\OCRC_READONLY\` on Windows, `~/OCRC_READONLY/` elsewhere) or pick once; verify alias stored under `Data/config/host_alias.json.enc`.
4) On watcher prompt “Found N new files. Index now?” respond “No”; confirm no indexing occurs without consent.
6) Toggle Paranoid → adapters detected audit triggers; mode reverts to Hardened automatically.

PS C:\Users\eric\OneDrive\Documents\R-Team> python -m services.indexer.build_index --src Samples --out Data/index.json
Indexed 3 chunks from 3 files into Data\index.json
PS C:\Users\eric\OneDrive\Documents\R-Team> python -m apps.launcher.main --mode standard --probe --ask "List any open questions for Client A" --index Data/index.json
PIN accepted.
Mode: Standard — Outbound sockets blocked; DNS blocked; adapters detected; proceeding.
Host folder bound read-only: C:\OCRC_READONLY
Voice Mode disabled.
DNS: BLOCKED (ok)
SOCKET: BLOCKED (ok)
Here’s what I found:
- purpose and overview this illustrative family trust is designed to steward multi asset wealth for two generations while preserving flexibility for changing circumstances it is a neutral sample set for testing an offline ai workflow not advice the trust aims …
- crut charitable remainder unitrust that pays a percentage to noncharitable beneficiaries with the remainder to charity grat grantor retained annuity trust that returns an annuity to the grantor for a term remainder to beneficiaries fmv fair market value the price …

Sources:
- Client_A\Trust_Structure_Overview.txt (modified 2025-10-08)
- Shared\Glossary.md (modified 2025-10-08)
PS C:\Users\eric\OneDrive\Documents\R-Team> python -m apps.launcher.main --mode hardened --probe --ask "What is the distribution policy and liquidity target?" --index Data/index.json
PIN accepted.
Mode: Hardened — Outbound+DNS blocked; limited privileges; adapters detected; proceeding.
Host folder bound read-only: C:\OCRC_READONLY
Voice Mode disabled.
DNS: BLOCKED (ok)
SOCKET: BLOCKED (ok)
Here’s what I found:
- purpose and overview this illustrative family trust is designed to steward multi asset wealth for two generations while preserving flexibility for changing circumstances it is a neutral sample set for testing an offline ai workflow not advice the trust aims …
- crut charitable remainder unitrust that pays a percentage to noncharitable beneficiaries with the remainder to charity grat grantor retained annuity trust that returns an annuity to the grantor for a term remainder to beneficiaries fmv fair market value the price …

Sources:
- Client_A\Trust_Structure_Overview.txt (modified 2025-10-08)
- Shared\Glossary.md (modified 2025-10-08)