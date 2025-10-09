# Decision Log

- **2025-10-08** PIN pad gates all launch surfaces. Owner: Security Lead. Deadline: 2025-10-09 ET. Rationale: Keep PIN mandatory before any UI renders.
- **2025-10-08** Security slider defaults to Standard, enforces Hardened parity, requires adapter-off check in Paranoid. Owner: Platform Lead. Deadline: 2025-10-10 ET. Rationale: Align air-gap behavior with policy tiers.
- **2025-10-08** Voice Mode ships as manual toggle with audit trail; default OFF. Owner: Accessibility Lead. Deadline: 2025-10-11 ET. Rationale: Respect large-text-first workflow and avoid auto-speech.
- **2025-10-08** Host data exposed via `bind_host_path()` read-only alias only. Owner: Systems Lead. Deadline: 2025-10-09 ET. Rationale: Prevent accidental host writes while enabling offline access.
- **2025-10-08** Adopt shared audit surface (`services/preflight/audit.py`). Owners: Security (PIN/mode), Integrator (host alias), Designer (voice). Due EOD.
- **2025-10-08** Capture Standard/Hardened `--probe`+`--ask` transcripts in `tests/e2e/smoke.md` as acceptance evidence. Owner: Integrator Lead. Deadline: 2025-10-08 ET. Rationale: Prove offline enforcement and citation flow on Samples corpus.
- **2025-10-09** PIN lifecycle files staged under `Data/security/` with lockout counters and recovery rotation workflow. Owner: Security Lead. Deadline: 2025-10-09 ET. Rationale: Support PIN change/reset policy before crypto integration.
- **2025-10-09** Day 2 execution plan locked. Owner: Program Manager. Deadline: 2025-10-09 ET. Rationale: Coordinate cross-team deliverables for second-day goals.
  - 10:30 ET  Security Lead: Replace `services/security/pin_gate.py` stub with encrypted Data vault handshake and refresh audits.
  - 13:00 ET  Designer & Accessibility Lead: Finalize Voice Mode enable/disable confirmations in `apps/ui/voice_script.md` and `apps/ui/states.md`.
  - 15:30 ET  Data Lead: Re-run Samples index rebuild (`services/indexer/build_index.py`) and attach metadata notes to `Data/index.json`.
  - 17:00 ET  Integrator Lead: Smoke-test all Start-* launchers post-changes and archive logs under `tests/e2e/`.
