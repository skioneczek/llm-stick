# Preflight Interfaces (Day 1 stubs)

## Module Map
- **`services/preflight/audit.py`**: Defines `Mode` enum, `Audit` dataclass, and helper audits (`audit_pin`, `audit_mode`, `audit_voice`, `audit_host_alias`).
- **`services/preflight/mode_state.py`**: Persists current security mode, tracks adapter/guard state, and routes through `audit_mode` before committing updates.
- **`services/preflight/adapter_detect.py`**: Cross-platform adapter detection (PowerShell + netsh on Windows, `ifconfig` on macOS, `ip link`/`/sys` on Linux).
- **`services/preflight/host_alias.py`**: Resolves platform default read-only host folder and reports via `audit_host_alias`.
- **`services/security/net_guard.py`** (linked service): Applies process-local outbound and DNS guards plus hardened temp sandbox.
- **`services/security/pin_gate.py`** (linked service): In-memory PIN gate used by launcher preflight.

## Enforcement Flow (launcher integration)
1. Validate PIN through `unlock_with_pin()` and log result with `audit_pin()`.
2. Detect adapters via `adapter_detect.adapters_active()`; feed state into `mode_state.set_adapters_active()`.
3. Apply guards (`net_guard.apply_standard_guards()` / `apply_hardened_guards()`); report via `mode_state.set_guards_ok()`.
4. Call `mode_state.set_mode()` to emit the appropriate audit string and capture success/failure.
5. Bind host path using `host_alias.bind_host_path()` (read-only) and report audit line.
6. Confirm Voice Mode state through `audit_voice()` (default OFF).
7. Optional inline probe uses `net_guard.probe_text()` for DNS/socket verification.

## Audit Strings (exact output)
- **Standard**: `Mode: Standard — Outbound sockets blocked; DNS blocked; adapters detected; proceeding.`
- **Hardened**: `Mode: Hardened — Outbound+DNS blocked; limited privileges; adapters detected; proceeding.`
- **Paranoid (pass)**: `Mode: Paranoid — No adapters detected; sandbox active; proceeding.`
- **Paranoid (fail)**: `Mode: Paranoid — Adapters detected; please disable Wi-Fi/unplug Ethernet.`

`standard` and `hardened` operate with adapters present but enforce an internal outbound ban; `paranoid` requires adapters down before preflight can pass, otherwise launch aborts.
