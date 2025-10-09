# Retriever API

## Overview
- **Mode**: Offline-only; operates on local FAISS index built by `services/indexer/`.
- **Security**: Requires prior PIN unlock, rebuilds outbound network block before every query, logs audit line (`proceed`/`revert`).
- **Memory ledger**: Read-only access to stable conclusions; no raw chunk text persisted.

## Query Flow
1. **`search(query: str, k: int = 8) -> List[Hit]`**
   - Applies keyword prefilter (BM25 over neutral placeholders) to prune corpus.
   - Performs ANN lookup via FAISS (bge-small-en or nomic embeddings).
   - Combines results with **recency bias**: score += `λ * freshness_decay(modified_time)` where λ default `0.1`.
   - Returns top `k` raw hits with metadata `{chunk_id, filename, path, client_tag, modified_time, mime, page_span, ann_score, keyword_score}`.
2. **`rerank(hits: List[Hit]) -> List[Hit]`**
   - Normalizes ANN L2 scores and BM25 scores to `[0,1]`.
   - Final score = `0.6 * ann_norm + 0.3 * bm25_norm + 0.1 * recency_norm`.
   - Truncates to top 4 hits, preserving metadata and adds `final_score` field.
3. **`answer(hits: List[Hit], prompt: PromptBundle) -> Answer`**
   - Crafts response with plan → answer → cite structure.
   - Citations include filename + modified date from metadata; format: `filename (modified YYYY-MM-DD)`.
   - Returns `{ text, citations: [{ file, modified_time, chunk_id, page_span }] }`.

## Recency Bias Details
- Freshness computed via exponential decay: `recency_norm = exp(-Δt / τ)` with default horizon `τ = 30 days`.
- When `security_slider = Paranoid`, recency term is disabled to avoid clock drift reliance; fallback to ANN+keyword average.

## Error Handling
- If ANN store unavailable, returns `revert:{reason}` audit and refuses to answer.
- Empty results trigger neutral response recommending manual review, with zero citations.

## Extensibility
- Supports plugging alternative embedding models if exported locally.
- Keyword layer accepts additional synonym dictionaries via `config/keywords.yaml` (placeholders only until ingestion).
