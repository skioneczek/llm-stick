# STATUS BOARD — LLM Stick
_As of 2025-10-09 (ET). This file is authoritative. Each role must read this first._

## Completed (Day 1)
- Planner: Decisions logged in [docs/Decision_Log.md](docs/Decision_Log.md); R-001 tracked in [docs/Risk_Register.md](docs/Risk_Register.md) with probe evidence note. (Commit links pending initial git history.)
- Designer: Large-text quick start + voice/UI specs published in [docs/QuickStart_card.md](docs/QuickStart_card.md) and [apps/ui/voice_script.md](../apps/ui/voice_script.md), [apps/ui/states.md](../apps/ui/states.md); Voice Mode confirmations captured.
- Security: Preflight checklist and audit strings documented in [docs/Security_Checklist.md](docs/Security_Checklist.md); live interfaces enumerated in [services/preflight/README.md](../services/preflight/README.md).
- Data: Prompt templates with plan → answer → sources flow documented in [docs/prompt_templates.md](docs/prompt_templates.md); retriever confirmed offline-only on Samples corpus.
- Integrator: Standard/Hardened `--probe`/`--ask` outputs recorded with commands and environment info in [tests/e2e/smoke.md](../tests/e2e/smoke.md).
- Platform: Repo skeleton, Samples corpus, indexer/retriever pipeline, host alias audit, memory ledger stub all landed; launcher wired to local index.

## Acceptance (Day 1)
- Standard & Hardened: audits print; inline probe says `DNS: BLOCKED (ok)` / `SOCKET: BLOCKED (ok)`; `--ask` works on Samples with sources.
- Paranoid: fails with adapters on; passes with adapters off.

## Links / Files to read first
- `docs/Decision_Log.md`, `docs/Risk_Register.md`, `docs/Security_Checklist.md`, `docs/QuickStart_card.md`, `docs/prompt_templates.md`, `tests/e2e/smoke.md`

## Day 2 Plan (In Progress — 2025-10-09)
- **Security Lead (13:30 ET deliverable):** Ship encrypted PIN vault swap (`services/security/pin_gate.py`, `services/security/keystore.py`) and validate hardened sandbox telemetry (`services/security/sandbox_check.py`).
- **Designer & Accessibility Lead (17:00 ET deliverable):** Update `apps/ui/voice_script.md` / `apps/ui/states.md` with Set Data Folder confirmation messaging and UI reader presets.
- **Data Lead (18:30 ET deliverable):** Integrate Set Data Folder workflow, rebuild index via `services/indexer/build_index.py`, log provenance inside `Data/index.json`, and honour performance warnings.
- **Integrator Lead (20:00 ET deliverable):** Execute full Set Data Folder E2E (including `tests/e2e/day2.md`), post logs under `tests/e2e/artifacts/`, and signal acceptance window open.
- **Program Manager (post Integrator signal):** Launch Day-2 acceptance run per `docs/Acceptance_Script.md`; document results and update risk posture (R-001/R-002).
- **Web UI Squad (19:30 ET deliverable):** Ship loopback-only web UI server with bundled assets and strict CSP, record enforcement audit, and prep Standard/Hardened walkthrough script.

## Day 2.5 Plan (Queued — Ingest E2E)
- **Platform Lead (prep by 2025-10-10 12:00 ET):** Finalize ingest mode toggle (HOST_LOCAL default, STICK_ENCRYPTED behind provider check) and surface audit lines in launcher.
- **Data Lead (prep by 2025-10-10 15:00 ET):** Extend ingest pipeline to honour per-client registry + source slugs, run dry-run ingest using `Samples/` surrogate corpus, and log provenance in `Data/index.json`.
- **Security Lead (prep by 2025-10-10 17:00 ET):** Validate source guard + registry integration, ensure ingestion aborts on cross-client paths, and capture audit traces.
- **Integrator Lead (acceptance window 2025-10-10 18:00–20:00 ET):** Execute Ingest E2E script (temporary `Samples/` inputs until production client path assigned), archive logs in `tests/e2e/artifacts/ingest/`, and signal ready.
- **Program Manager (post Integrator signal):** Confirm Day-2.5 acceptance gate: successful ingest run on `Samples/` surrogate, ledger/index tagged by source slug, and Program Manager sign-off before enabling real client folders.

## Acceptance — Web UI (Day 2)
- Standard/Hardened: Web UI server binds to 127.0.0.1, serves bundled assets, enforces CSP, and passes guarded probe script before sign-off.
- Paranoid: UI server stays disabled; verify fallback large-text launcher screens and guard logs before approval.

## Micro Update — 2025-10-09 (15:23 ET)
Done: Logged Local Web UI decision + R-005 loopback risk (`docs/Decision_Log.md`, `docs/Risk_Register.md`); Web UI squad queued for Day-2 E2E.
Next: Await Integrator’s Set Data Folder package, then execute Standard/Hardened Web UI walkthrough before opening acceptance, followed by Day-2.5 ingest dry-run.
Blockers: Crypto/OCR providers pending; Paranoid mode uses launcher fallback until hardened web UI reviewed.
