# Memory Ledger (Day 1)

## What We Store
- Short, stable conclusions keyed by client and topic (e.g., `open_questions`, `milestones`).
- Each entry captures timestamp, client label, key, and truncated value (<=500 chars).
- Ledger path: `Data/memory_ledger.json` (created on first write, encrypted volume recommended).

## CLI Hooks
- Retriever command accepts `--client "<name>" --remember "key=value"` to append a note after answering.
- Entries default to neutral placeholders until real data is ingested.

## Listing & Pruning
- Use `services.memory.ledger.list_client("Client A")` to read stable facts for a client.
- `services.memory.ledger.prune("Client A", "open_questions")` removes a specific key for that client.

## Privacy Stance
- Ledger runs fully offline; no cloud sync or telemetry.
- Store summaries only—never raw PII, transcripts, or long excerpts.
- Notes should be redact-friendly and replaceable; pruning is supported to honor user overwrite requests.
