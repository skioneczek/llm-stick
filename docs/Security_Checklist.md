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

## PIN Lifecycle
- **Storage layout:** `Data/security/pin.txt` holds the 6-digit PIN; `Data/security/recovery_phrase.txt` stores the 12-word phrase (comment header + single line payload) until crypto wraps arrive.
- **Unlock:** `unlock_with_pin()` enforces digit-length validation, 5-attempt lock (15 minutes), and 10-attempt replug requirement before clearing counters.
- **Change:** `change_pin(current, new, confirm)` requires current PIN success, matching confirmation, and writes the new PIN to `pin.txt` while resetting attempts.
- **Reset:** `reset_with_phrase(words, new, confirm, replacement)` matches the stored phrase, sets a fresh PIN, optionally rotates the phrase, and clears lockout state.
- **Recovery maintenance:** `set_recovery_phrase()` bootstraps or replaces the phrase; operators must ensure words are lowercase ASCII and policy-compliant before import.

## Auxiliary Controls
- **Clear logs — completed; local only.** Triggered when `clear_logs()` removes `Data/*.log`; memory ledger stays intact unless panic escalation explicitly requests ledger wipe (future Day-3 work).
- **Temp sandbox — verified (paths under Data/tmp).** `verify_temp_sandbox()` ensures `TMPDIR`, `TMP`, and `TEMP` all resolve inside `Data/tmp` after Hardened guard activation.
- **Temp sandbox — failed; reverting.** Emitted when any env var missing/unresolvable or pointing outside `Data/tmp`; Hardened must roll back to Standard until resolved.
- **Panic semantics.** Voice panic wipes temps via `wipe_temps()` and exits but does **not** clear `Data/memory_ledger.json` by default; a “panic-and-forget” pathway will handle ledger purge in Day-3 scope.

## Mode Enforcement Reference
- **Standard**: Adapters may remain active; must prove outbound sockets blocked internally and log result using `STANDARD_AUDIT` when proceeding.
- **Hardened**: Same as Standard plus DNS resolver disabled and privileges reduced; emit `HARDENED_AUDIT` confirming clamps with adapters noted.
- **Paranoid (pass)**: Require all adapters down before proceeding; sandbox networking (`unshare -n`, PF, WFP) and log via `PARANOID_PASS_AUDIT`.
- **Paranoid (fail)**: If any adapter detected, abort immediately and emit `PARANOID_BLOCK_AUDIT`.
