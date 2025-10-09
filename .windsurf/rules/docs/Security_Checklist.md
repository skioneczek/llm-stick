---
trigger: manual
---

# Security Preflight & Audits

## Preflight (ordered)
1) Mount check: confirm stick structure (App/, Data/, Docs/, Samples/).
2) PIN gate: prompt pad (no auto-speech). On success, unlock key and mount encrypted Data/.
3) Mode read: Standard (default) | Hardened | Paranoid.
4) Network guard:
   - Standard/Hardened: apply outbound-deny + DNS-deny; run socket/DNS self-tests; if guard fails → internal hard ban.
   - Paranoid: verify no active adapters; if any active → fail with guidance.
5) Host folder binding: locate read-only path (or prompt once); confirm read-only mount.
6) Logging policy: local only; integrity hash; show “Clear logs” control.
7) Ready signal: enable UI; if Voice Mode ON, play a short confirmation line.

## 1–2 Line Audit Strings
- Standard (pass): `Mode: Standard — Outbound sockets blocked; DNS blocked; adapters detected; proceeding.`
- Hardened (pass): `Mode: Hardened — Outbound+DNS blocked; limited privileges; adapters detected; proceeding.`
- Paranoid (fail): `Mode: Paranoid — Adapters detected; please disable Wi-Fi/unplug Ethernet.`
- Paranoid (pass): `Mode: Paranoid — No adapters detected; sandbox active; proceeding.`

## Acceptance (security slice)
- Standard/Hardened must pass self-tests with adapters active.
- Paranoid must hard-fail until adapters are off; then pass.
- Any failure must either auto-correct or revert with a clear message.
