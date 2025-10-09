# Indexer CLI (offline)

## Overview
- **Mode**: Fully offline, operates on neutral placeholder corpus under `Samples/`.
- **Access control**: CLI requires successful 6-digit PIN unlock prior to any command execution.
- **Networking**: All commands enforce outbound network block and log enforcement status before exit.

## Commands
- **`indexer parse --input {PATH} --client-tag {TAG}`**
  - Loads supported files, emits normalized `DocChunk` stream.
  - Optional `--enable-ocr` activates offline Tesseract bridge (default OFF).
- **`indexer chunk --input {DOC_STREAM} --size 1000 --overlap 120`**
  - Applies token-based windowing (adaptive 800–1200 tokens, 10–15% overlap) per document.
- **`indexer embed --input {CHUNK_STREAM} --model bge-small-en`**
  - Uses local embedding model (switchable to `nomic-embed-text`).
- **`indexer build-index --chunks {CHUNK_STREAM} --meta {META_STREAM}`**
  - Produces FAISS index persisted to `services/indexer/store/` with integrity hash ledger.

Each command runs a post-action enforcement self-check and prints a one-line audit: either `proceed:{timestamp}` or `revert:{error}`.

## Parser Configuration
| Format | Parser ID | Notes | OCR | Output Units |
| --- | --- | --- | --- | --- |
| PDF (text layer) | `parser_pdf_text` | Extracts text layer only; respects page order. | Toggle (OFF) | Pages |
| PDF (image) | `parser_pdf_ocr` | Invoked only when `--enable-ocr`; uses offline Tesseract profile `TESS_DEFAULT`. | ON | Pages |
| DOCX | `parser_docx` | Text + paragraph style markers. | N/A | Paragraph blocks |
| PPTX | `parser_pptx` | Slide titles + bullet text. | N/A | Slides |
| XLSX | `parser_xlsx_values` | Cell value grid; formulas excluded. | N/A | Sheets |
| TXT/MD | `parser_text` | UTF-8 plain/markdown; preserves headings. | N/A | Logical sections |
| EML | `parser_eml` | Headers + body + attachments (text only). | N/A | Mime parts |

## Chunking & Metadata
- **Chunk span**: 800–1200 tokens adaptive, 10–15% overlap based on structural cues.
- **Metadata schema** per chunk:
  - `filename`
  - `path`
  - `client_tag` (placeholder such as `CLIENT_TAG_TBD`)
  - `modified_time` (UTC ISO8601)
  - `mime`
  - `page_span` (start–end within source)
- **Ledger note**: Stable conclusions extracted during indexing are appended to the memory ledger; raw PII and long-form notes are excluded.

## Outputs
- **Chunk artifacts**: Stored as `.jsonl` under `services/indexer/output/chunks/`.
- **Embeddings**: `.npy` matrices aligned with chunk IDs.
- **FAISS index**: `services/indexer/store/faiss_index.bin` with companion `meta.json` for schema.
