# Day 3 Evidence Log

## Scenario 6 — LLM Wrapper CLI
- [ ] `python -m core.llm.wrap --list-profiles`
- [ ] `python -m core.llm.wrap --run --profile offline-balanced-q4 --prompt "Summarize Client A trust highlights."`

## Scenario 7 — Checksum Policy Enforcement
- [ ] `python packaging/checksums/make_manifest.py`
- [ ] `python -m apps.launcher.main --mode standard --pin 123456 --probe`

## Scenario 8 — Standard Streaming Web UI
- [ ] Capture browser Network log for `/api/stream/<sid>` showing incremental tokens.
- [ ] Save `Data/conversations/*.json` thread file with assistant message containing `mode: "index"` metadata.

## Scenario 9 — Hardened Streaming Parity
- [ ] `python -m apps.launcher.main --mode hardened --pin 123456 --probe --ui enhanced`
- [ ] Note `X-Audit` header from SSE response.

## Scenario 10 — Paranoid CLI Fallback
- [ ] `python -m apps.launcher.main --mode paranoid --pin 123456 --probe --ask "Confirm Paranoid fallback behaviour"`
- [ ] Record console output showing checksum guard + CLI answer.
