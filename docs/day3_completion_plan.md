# Day-3 Completion & Hardening Plan

## 1. Offline LLM bring-up and streaming delivery
- Finish the core invocation helper that `core.llm.wrap` and the retriever can share (`core/llm/invoke.py`), capturing stdout/stderr into `Data/logs/llm.log` and staging prompts under `Data/tmp/` per the runtime contract. Hook it into the launcher so non-CLI surfaces stop bypassing the wrapper when llama.cpp assets exist.
- Flesh out `core/llm/profiles.json` with footprint metadata, default flags, and checksum keys, then extend `core.llm.wrap` to report missing manifests as hard failures once Day-3 packaging lands. Surface friendly remediation text when binaries or GGUFs are absent to satisfy the TODO in the runtime README.
- Drive end-to-end streaming from the web UI by updating the ask flow to request LLM output via `answer_llm` instead of the retriever stub, storing the streamed transcript back into thread history, and documenting the browser SSE contract. Capture acceptance evidence for Standard/Hardened runs per Scenario 8/9 in `docs/Acceptance_Script.md`.

## 2. Ingest/registry pipeline closure
- Replace the `{{ ... }}` placeholder in `services/ingest/worker.py` with chunk writers, OCR gating, and source guard hooks so HOST_LOCAL and STICK_ENCRYPTED jobs walk files safely. Persist per-client manifests and audit lines back into the registry.
- Implement the remaining queue/worker plumbing (job acknowledgements, temp cleanup, crypto error handling) and exercise the Day 2.5 ingest flow end-to-end, logging results under `tests/e2e/artifacts/ingest/`.
- Update documentation and the status board once ingest acceptance passes, noting how to hotswap client slugs without cross-contamination, and add a Day-2.5 acceptance section to `docs/Acceptance_Script.md`.

## 3. Packaging and checksum enforcement
- Generate the Day-3 checksum manifest (`packaging/checksums/manifest.json`) alongside individual `.sha256` files using `make_manifest.py`, covering llama binaries, GGUF models, web bundles, and packaging outputs.
- Gate launcher startup and wrapper execution on checksum verification so offline assets fail closed when hashes drift, matching Scenario 7 in the Day-3 acceptance script.
- Document platform-specific packaging steps in `packaging/*.md` with the new validation flow, and add regression checks to CI to regenerate the manifest when assets change.

## 4. Evidence and risk retirement
- Backfill Day-3 e2e transcripts (LLM wrapper CLI, streaming UI, Paranoid CLI fallback) in `tests/e2e/day3.md`, referencing acceptance script scenarios 6–10.
- Update `docs/STATUS_BOARD.md` to mark Day 3 milestones and Day 2.5 ingest as completed once evidence lands.
- Drive the open risk items in `docs/Risk_Register.md` to closure by documenting mitigations: adapter enforcement after Paranoid cutover, ingest bleed prevention with registry checks, PDF engine decision with checksum coverage, and thread compaction roadmap.

## 5. Follow-on guardrails
- Expand automated probes so `python -m apps.launcher.main --probe` validates checksum manifests, ingest registry health, and SSE endpoints before reporting success.
- Capture the updated workflow in the README “Milestones” and “Known limitations” sections, replacing Day-3 TODO language once the features ship.
