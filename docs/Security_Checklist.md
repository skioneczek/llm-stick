# Security Preflight Checklist

## Ordered Preflight
1. Mount encrypted `Data/` volume for internal writes; verify host alias bound read-only.
2. Prompt for and validate 6-digit PIN before unlocking any keys; enforce lockout (5 tries → 15-minute hold, 10 → replug).
3. Load security slider (`standard` default) and configure enforcement stack accordingly.
4. Apply outbound socket deny rules and run self-test; add DNS disable where required.
5. Evaluate adapter state: log presence for `standard`/`hardened`; require none for `paranoid` or abort.
6. Initialize integrity-checked logging, temp purge routines, and recovery phrase guardrails.
7. Arm "Panic" voice listener (opt-in voice mode) and confirm temporary areas wiped.
8. Emit the 1–2 line audit for the active mode, capturing enforcement outcome and proceed/abort state.

## Acceptance Criteria
- Mode switch enforces corresponding network, DNS, and privilege policies before proceeding.
- PIN services implement unlock, change, and recovery rewrap workflows with lockouts.
- Host scanning reads only from configured folder; all writes restricted to encrypted `Data/`.
- Logging operations produce human-readable entries plus hash note; single clear control.
- Voice panic command reliably wipes temps and exits irrespective of slider mode.
- Post-change audit renders 1–2 line status per mode with failure reasons when applicable.

## Mode Enforcement Reference
- **Standard**: Adapters may remain active; must prove outbound sockets blocked internally and log result using `STANDARD_AUDIT` when proceeding.
- **Hardened**: Same as Standard plus DNS resolver disabled and privileges reduced; emit `HARDENED_AUDIT` confirming clamps with adapters noted.
- **Paranoid (pass)**: Require all adapters down before proceeding; sandbox networking (`unshare -n`, PF, WFP) and log via `PARANOID_PASS_AUDIT`.
- **Paranoid (fail)**: If any adapter detected, abort immediately and emit `PARANOID_BLOCK_AUDIT`.
