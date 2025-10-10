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
- Loopback web UI launch prints `Loopback allowed (UI server only).` before the server URL; Paranoid mode prints `UI server disabled in Paranoid mode.` and skips launch.
- HTTP responses include the strict CSP header (`default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'`) with audit `CSP applied (offline assets only).`
- Print endpoint (`/_print/<thread_id>`) returns `X-Action-Audit: Print invoked (local assets only).`; PDF export returns either `X-Action-Audit: PDF export (engine weasyprint|wkhtml)` or `X-Action-Audit: PDF export fallback (engine missing)`, with audit log entries "UI export: PDF emitted (local engine)." or "UI export: PDF engine missing, used print fallback." as appropriate.

## PIN Lifecycle
- **Storage layout:** `Data/security/pin.txt` holds the 6-digit PIN; `Data/security/recovery_phrase.txt` stores the 12-word phrase (comment header + single line payload) until crypto wraps arrive.
- **Unlock:** `unlock_with_pin()` enforces digit-length validation, 5-attempt lock (15 minutes), and 10-attempt replug requirement before clearing counters.
- **Change:** `change_pin(current, new, confirm)` requires current PIN success, matching confirmation, and writes the new PIN to `pin.txt` while resetting attempts.
- **Reset:** `reset_with_phrase(words, new, confirm, replacement)` matches the stored phrase, sets a fresh PIN, optionally rotates the phrase, and clears lockout state.
- **Recovery maintenance:** `set_recovery_phrase()` bootstraps or replaces the phrase; operators must ensure words are lowercase ASCII and policy-compliant before import.
- **Source selection:** On "Set Data Folder" execute `validate_source(path)`; if it returns `Data source invalid: …` or `Data source requires confirm: …`, abort and keep the prior source until the user explicitly confirms. When validation succeeds, log `Data source validated: …`, then trigger index clear + rebuild under the guarded process before proceeding.


## Mode Enforcement Reference
- **Standard**: Adapters may remain active; must prove outbound sockets blocked internally and log result using `STANDARD_AUDIT` when proceeding.
- **Hardened**: Same as Standard plus DNS resolver disabled and privileges reduced; emit `HARDENED_AUDIT` confirming clamps with adapters noted.
- **Paranoid (pass)**: Require all adapters down before proceeding; sandbox networking (`unshare -n`, PF, WFP) and log via `PARANOID_PASS_AUDIT`.
