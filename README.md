LLM Stick — Air-Gapped, Voice-Optional USB Assistant








Status: Day 2 accepted — see the live board → docs/STATUS_BOARD.md

Quick Start: docs/QuickStart_card.md
 · Security Checklist: docs/Security_Checklist.md

What is this?

An offline, air-gapped “LLM Stick” you can plug into any machine and talk to about local files. No cloud. PIN-gated. Voice optional. Ships with a loopback-only Web UI and a CLI so a nearly-blind user can choose large text or speech.

Day-2 Highlights

Security modes with audits

Standard / Hardened / Paranoid; outbound sockets & DNS blocked; adapter checks; temp sandbox verified.

Paranoid disables the Web UI and falls back to large-text launcher messaging.

Loopback Web UI (127.0.0.1 only)

Bundled static assets, strict CSP, no external fonts/CDNs.

Threads view with composer, sources panel, archive/search.

Print (Large Text) works via local CSS; Export PDF uses local engine if present, otherwise falls back to browser “Print to PDF”.

“Set Source” (per-session)

Pick a read-only folder; selection is validated (validate_source) and indexed offline.

CLI: --set-source, --list-source, with clear audit lines. Supports an allow-list root via LLM_STICK_ALLOWED_SOURCE.

Voice stub (single-turn)

“TTS> Ready.” prompt, then offline retrieval; prints filenames/dates as sources.

Offline RAG plumbing

Indexer/retriever over the Samples corpus; thread store + memory ledger scoped by source/client slugs.

Quick Start (Day-2)

You can use the CLI alone, or launch the guarded Web UI and drive it in a browser (loopback only).

(Optional) allow Samples path for validation

Windows (current shell):

$env:LLM_STICK_ALLOWED_SOURCE = "C:\Users\<you>\...\R-Team\Samples"


(Or persist for new shells: setx LLM_STICK_ALLOWED_SOURCE C:\path\to\Samples)

macOS/Linux:

export LLM_STICK_ALLOWED_SOURCE="$HOME/R-Team/Samples"


Build an index

python -m services.indexer.build_index --source Samples


Launch (Hardened) with Web UI

python -m apps.launcher.main --mode hardened --ui standard --probe


Watch for audits like:

Temp sandbox — verified (...)
DNS: BLOCKED (ok)
SOCKET: BLOCKED (ok)
Loopback allowed (UI server only).
UI: http://127.0.0.1:xxxxx


Ask in the CLI (optional)

python -m apps.launcher.main --mode hardened --probe --ask "Summarize Client A trust highlights"


Voice (single-turn)

python -m apps.launcher.main --mode hardened --voice --probe --ask "List open questions for Client A"


Change the data source (validated + reindex)

python -m apps.launcher.main --set-source "C:\OCRC_READONLY\Client_A"
python -m apps.launcher.main --list-source

Security posture (current)

Air-gap by policy and probe: outbound sockets & DNS blocked; adapters audited; temp workspace confined under Data/tmp.

Web UI bound to 127.0.0.1/::1 with strict CSP and no external assets.

Paranoid mode disables the Web UI and logs the audit line; launcher continues in large-text fallback.

Every sensitive action emits a 1-line audit (PIN accepted, loopback allowed, source validated/invalid, print/PDF invoked, etc.).

Milestones

v0.1-day1 (done): audits + offline retriever + launcher --ask + docs.

v0.2-day2 (done): loopback Web UI + strict CSP; Set Source (+validation & reindex); voice stub; large-print; PDF fallback; probes & acceptance logs.

v0.3-day3 (in progress):

Bring-up offline LLM (llama.cpp wrapper, model profiles & checksums, streaming answers in Web UI).

Ingest Mode E2E (HOST_LOCAL default; STICK_ENCRYPTED when provider installed), per-client registry & hotswap.

Packaging scripts for Win/macOS/Linux; thread compaction; optional local PDF engine bundle.

Follow progress

Decisions: docs/Decision_Log.md

Risks: docs/Risk_Register.md

Day-1 smoke outputs: tests/e2e/smoke.md

Day-2 acceptance & UI probes: tests/e2e/day2.md

Acceptance script: docs/Acceptance_Script.md

Known Day-2 limitations

Answers in the Web UI use the retriever stub (short “plan + key lines”) until the Day-3 LLM is wired; PDF export falls back unless a local engine is present.

“Open” in the Threads list opens the thread; Set Source is controlled via the Controls panel or CLI.

Paranoid mode disables the Web UI by design.
