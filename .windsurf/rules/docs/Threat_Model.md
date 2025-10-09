---
trigger: manual
---

# Threat Model — LLM Stick (Air-Gapped, PIN-Gated)

## Assets
- Encrypted data on stick: indexes, memory, settings, logs, Samples.
- User queries and answers (ephemeral temps).
- Host file paths (read-only alias only).

## Trust Boundaries
- Stick process ↔ host OS (read-only access to a chosen folder).
- Stick process ↔ network (must be blocked: Standard/Hardened internally, Paranoid by adapters off).
- User input/output (Voice Mode optional; no auto-speech on launch).

## Assumptions
- Host may be online, misconfigured, or monitored.
- No installers; portable binaries only.
- No cloud calls; no telemetry; no auto-updates.

## Primary Risks & Controls
1) **Network exfiltration** — block all outbound sockets + DNS (Standard/Hardened); require adapters off (Paranoid).
2) **Host writes** — never write to host; all writes to encrypted Data/.
3) **Key exposure** — 6-digit PIN unlock; 12-word recovery phrase to reset; lockouts.
4) **PII spill to audio/UI** — Voice Mode OFF by default; sources only on explicit ask; logs local only; one-tap purge.
5) **Parser abuse** — parse text formats only; OCR toggle off by default; size/time limits.

## Mode Enforcement (summary)
- **Standard**: internal outbound-deny + DNS deny; adapters may be up.
- **Hardened**: Standard + reduced privileges + tighter temps.
- **Paranoid**: adapters must be down or refuse to run.

## Validation
After any setting change: run self-tests and print a 1–2 line audit. On failure: auto-correct or revert and report.
