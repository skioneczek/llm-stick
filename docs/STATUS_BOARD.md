# STATUS BOARD — LLM Stick
_As of 2025-10-10 (ET). This file is authoritative. Each role must read this first._

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

## Day 2 Plan (Closed — 2025-10-09)
- **Security Lead (13:30 ET deliverable):** Ship encrypted PIN vault swap (`services/security/pin_gate.py`, `services/security/keystore.py`) and validate hardened sandbox telemetry (`services/security/sandbox_check.py`).
- **Designer & Accessibility Lead (17:00 ET deliverable):** Update `apps/ui/voice_script.md` / `apps/ui/states.md` with Set Data Folder confirmation messaging and UI reader presets.
- **Data Lead (18:30 ET deliverable):** Integrate Set Data Folder workflow, rebuild index via `services/indexer/build_index.py`, log provenance inside `Data/index.json`, and honour performance warnings.
- **Integrator Lead (20:00 ET deliverable):** Execute full Set Data Folder E2E (including `tests/e2e/day2.md`), post logs under `tests/e2e/artifacts/`, and signal acceptance window open (Standard/Hardened web UI walkthrough at 20:30 ET after setting `LLM_STICK_ALLOWED_SOURCE`).
- **Program Manager (20:45 ET deliverable):** In a new shell set the Samples allowance (Windows: `setx LLM_STICK_ALLOWED_SOURCE Samples`; macOS/Linux: `export LLM_STICK_ALLOWED_SOURCE=Samples`), then run `docs/Acceptance_Script.md`, paste outputs, and confirm tonight’s cut-line (Standard/Hardened acceptance green, Paranoid fallback noted).
- **Web UI Squad (19:30 ET deliverable):** Ship loopback-only web UI server with bundled assets and strict CSP, record enforcement audit, and prep Standard/Hardened walkthrough script.

## Day 2.5 Acceptance (Completed — 2025-10-10)
- **Data Lead (complete):** Ingest worker now validates sources, chunks documents into a guarded temp area, and emits per-client manifests before indexing. HOST_LOCAL + STICK_ENCRYPTED storage paths both exercised on surrogate data.
- **Security Lead (complete):** OCR gate blocks PDF ingestion when binaries are absent; crypto provider failures abort jobs with ledger lines.
- **Integrator Lead (complete):** Registry captures manifest paths + job IDs for audit, and ledger entries reflect chunk counts for acceptance evidence.
- **Program Manager (complete):** Status board + registry updated after E2E confirmation; acceptance script references new ingest evidence set.

## Day 3 Timeline (Completed — 2025-10-10)
- **12:00 ET — LLM Wrapper & Registry:** Shared `core.llm.invoke` helper captures prompts/logs and enforces checksum manifests before launch; `core.llm.wrap` and retriever streaming reuse the runtime path.
- **15:30 ET — Streaming Web UI:** Flask UI exposes `/api/ask` SSE endpoint, streams llama.cpp tokens into threads, and persists assistant replies with citations. Updated bundle hashed in the checksum manifest.
- **17:30 ET — Paranoid Cutover:** Launcher now fails closed without manifests and surfaces checksum guidance; Paranoid CLI continues to fall back to offline answers without starting the UI.

## Day 3 Supporting Workstreams
- **Designer (12:30 ET):** Finalize large-print `@media print` styling and confirm `window.print()` flow in web UI.
- **Platform Lead (14:30 ET):** Stage offline PDF engine hashes and fallback messaging in `apps/webui/pdf_engine.py`.

## Acceptance — Web UI (Day 2)
- Standard/Hardened: Web UI server binds to 127.0.0.1, serves bundled assets, enforces CSP, and passes guarded probe script before sign-off.
- Paranoid: UI server stays disabled; verify fallback large-text launcher screens and guard logs before approval.

## Micro Update — 2025-10-10 (18:05 ET)
Done: LLM checksum manifest generated + enforced in launcher/wrapper; ingest worker writes manifests + encrypted indexes; web UI SSE streaming pushes llama.cpp output into thread history.
Next: Capture acceptance evidence for Standard/Hardened streaming runs and archive ingest artifacts under `tests/e2e/`.
Blockers: None; PDF engine still optional with documented fallback.

## Micro Update — 2025-10-09 (20:20 ET)
Done: Logged export fallback handling decision + R-008 mitigation (`docs/Decision_Log.md`, `docs/Risk_Register.md`); Day-3 PDF engine vendor task staged.
Next: Integrator to finish Set Data Folder + web UI walkthrough; Program Manager to set `LLM_STICK_ALLOWED_SOURCE` (Win: `setx ...`; macOS/Linux: `export ...`), run `docs/Acceptance_Script.md`, paste outputs, and declare cut-line once Standard/Hardened pass.
Blockers: PDF engine bundle pending Day-3 packaging; thread compaction tooling pending R-007 prototype.

## Micro Update — 2025-10-09 (18:55 ET)
Done: Voice stub fixed to use structured RAG API; Hardened probe + voice ask returns spoken first line and sources.
Next: Day-3 LLM bring-up (llama.cpp wrapper, model profiles, checksum audit) and wire answers to Web UI streaming.
Blockers: None (PDF engine still optional; fallback active).
