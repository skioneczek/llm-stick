# LLM Stick — Air-Gapped, Voice-Optional USB Assistant

[![CI](https://img.shields.io/github/actions/workflow/status/officialerictm/llm-stick/ci.yml?branch=main)](../../actions)
![Tag](https://img.shields.io/github/v/tag/officialerictm/llm-stick)
![Issues](https://img.shields.io/github/issues/officialerictm/llm-stick)
![License](https://img.shields.io/badge/license-MIT-informational)

**Status:** **Day 3 timeline completed — offline wrapper, streaming Web UI, paranoid cutover landed.** See the live board → [`docs/STATUS_BOARD.md`](docs/STATUS_BOARD.md)
**Quick Start:** [`docs/QuickStart_card.md`](docs/QuickStart_card.md) · **Security Checklist:** [`docs/Security_Checklist.md`](docs/Security_Checklist.md)

## What is this?
An offline, air-gapped “LLM Stick” you can plug into any machine and talk to about local files. No cloud. PIN-gated. Voice optional. Ships with a loopback-only Web UI and a CLI so a nearly-blind user can choose large text or speech.

## Day-3 Highlights
- **Offline LLM wrapper with manifest enforcement**
  - `core.llm.invoke` / `core.llm.wrap` capture prompts, responses, and checksum manifests before llama.cpp starts.
  - Launcher fails closed without manifests; Paranoid mode keeps the CLI-only fallback online.
- **Streaming Web UI (loopback only)**
  - `/api/ask` exposes Server-Sent Events, streaming llama.cpp tokens directly into the thread history with citations.
  - Bundled assets stay hashed; large-print + print flows confirmed, with PDF export falling back to browser print when the optional engine is absent.
- **Ingest workflow with registry + ledger trails**
  - `--ingest` queues jobs per client slug, the worker writes manifests, and HOST_LOCAL vs STICK_ENCRYPTED storage both record audit lines.
  - Registry entries capture job IDs, manifest paths, and checksum guidance for hotswap + streaming retrieval.

## Quick Start (Day-3)
> Queue ingest, enforce manifests, and stream llama.cpp replies entirely offline.

1) **(Optional) allow Samples path for validation**
   - **Windows (current shell):**
     ```powershell
     $env:LLM_STICK_ALLOWED_SOURCE = "C:\Users\<you>\...\R-Team\Samples"
     ```
     Persist for new shells: `setx LLM_STICK_ALLOWED_SOURCE C:\path\to\Samples`
   - **macOS/Linux:**
     ```bash
     export LLM_STICK_ALLOWED_SOURCE="$HOME/R-Team/Samples"
     ```

2) **Queue an ingest job (writes manifest + registry entry)**
   ```bash
   python -m apps.launcher.main --mode standard --pin 123456 --ingest Samples --client client-a --dest HOST_LOCAL
   ```
   Expect the launcher to validate the source, log checksum manifest guidance, and print the completed registry entry (with job ID + manifest path). Use `--dest STICK_ENCRYPTED` when the crypto provider is staged.

3) **Launch hardened mode with streaming Web UI + offline LLM**
   ```bash
   python -m apps.launcher.main --mode hardened --ui standard --probe --llm --use-client client-a
   ```
   Watch for audits confirming sandbox, DNS/socket blocks, manifest verification, and the loopback-only UI URL. `/api/ask` streams llama.cpp tokens into the active thread with citations.

4) **Ask in the CLI using the same wrapper (optional)**
   ```bash
   python -m apps.launcher.main --mode hardened --probe --llm --use-client client-a --ask "Summarize ingest evidence for Client A"
   ```

5) **Hotswap or review ingest state**
   ```bash
   python -m apps.launcher.main --list-clients
   python -m apps.launcher.main --hotswap client-a --client client-a --mode standard
   ```
   Registry-backed hotswap keeps manifests attached; Paranoid mode continues to disable the UI and relies on the CLI prompts.

## Security posture (current)

* Air-gap by policy and probe: outbound sockets & DNS blocked; adapters audited; temp workspace confined under `Data/tmp`.
* Web UI bound to `127.0.0.1`/`::1` with strict CSP and no external assets.
* LLM wrapper and ingest worker require checksum manifests before jobs run; launcher fails closed without them.
* Paranoid mode disables the Web UI and logs the audit line; launcher continues in large-text fallback.
* Every sensitive action emits a **1-line audit** (PIN accepted, loopback allowed, source validated/invalid, print/PDF invoked, etc.).

## Milestones

* **v0.1-day1 (done):** audits + offline retriever + launcher `--ask` + docs.
* **v0.2-day2 (done):** loopback Web UI + strict CSP; Set Source (+validation & reindex); voice stub; large-print; PDF fallback; probes & acceptance logs.
* **v0.3-day3 (done):** Offline llama.cpp wrapper with manifest enforcement; streaming Web UI SSE endpoint; ingest workflow writing manifests + registry entries; paranoid cutover keeps CLI-only fallback.
* **v0.4 (next):** Capture Standard/Hardened streaming acceptance evidence, archive ingest artifacts under `tests/e2e/`, finish packaging/thread compaction, and decide on bundling the optional PDF engine.

## Follow progress

* Decisions: [`docs/Decision_Log.md`](docs/Decision_Log.md)
* Risks: [`docs/Risk_Register.md`](docs/Risk_Register.md)
* Day-1 smoke outputs: [`tests/e2e/smoke.md`](tests/e2e/smoke.md)
* Day-2 acceptance & UI probes: [`tests/e2e/day2.md`](tests/e2e/day2.md)
* Acceptance script: [`docs/Acceptance_Script.md`](docs/Acceptance_Script.md)

## Known Day-3 limitations

* Standard/Hardened streaming acceptance evidence is still being captured; expect new artifacts under `tests/e2e/`.
* PDF engine remains optional—the UI falls back to browser “Print to PDF” when binaries are missing, and ingest logs skipped PDFs when OCR is unavailable.
* Thread compaction tooling is still pending (R-007 roadmap); long-running conversations may grow until the follow-up lands.
* Paranoid mode continues to disable the Web UI by design while keeping CLI answers via the offline wrapper.
