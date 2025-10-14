# VSCode ChatGPT Plugin Instructions — Word/Excel Offline Support

These steps tell the ChatGPT VSCode extension (with plan-and-edit access) how to extend the stick so the local LLM can read Word (`.docx`) and Excel (`.xlsx`) files fully offline. Follow them in order; do not assume network access at any time.

## 1. Inventory current ingestion + packaging flow
1. Read `services/indexer/build_index.py` to understand how documents are discovered (`SUPPORTED`) and converted into text chunks.
2. Inspect the packaging scripts under `packaging/` to confirm how dependencies are vendored (offline `vendor/wheels` cache, PyInstaller/Nuitka builds, rsync into `App/`).
3. Check whether any documentation in `docs/` already references Office formats so that additions stay consistent.

## 2. Add offline Office dependencies to the packaging toolchain
1. Update the packaging docs (`packaging/README.md`) with a short bullet under **Prerequisites** listing the new wheels required: `python-docx`, `lxml`, `openpyxl`, `et-xmlfile`.
2. Extend each build script (`packaging/build_linux.sh`, `build_macos.sh`, `build_windows.ps1`) so the bootstrap virtualenv installs those wheels from `vendor/wheels` right after the PyInstaller/Nuitka tooling. Use the existing `PIP_ARGS` pattern; do **not** allow online resolution.
3. Document that the wheels must be staged under `vendor/wheels/` before packaging and that the build scripts should fail fast with a clear error if any of the four wheels are missing.

## 3. Centralize Office parsing helpers
1. Create a new module `services/indexer/readers.py` containing reusable `read_txt`, `read_docx`, `read_pdf`, and new `read_xlsx` helpers. Move the existing functions out of `build_index.py` to this module to avoid duplication.
2. Implement `read_xlsx` using `openpyxl` in read-only mode. Iterate sheets in order, join cell values row-by-row with tabs, and separate rows/sheets with blank lines. Guard imports with `try/except` so missing wheels simply return an empty string (consistent with existing optional behavior).
3. Adjust `read_docx` to capture both paragraph text and table cell text (iterate tables, join cell values by tabs, rows by newlines). Continue returning an empty string if the library is unavailable or parsing fails.
4. Ensure each helper strips null bytes and normalizes line endings to `\n` for consistency.

## 4. Wire helpers into the indexer
1. In `services/indexer/build_index.py`, import the helper functions from `services.indexer.readers` and delete the inline definitions.
2. Update the `SUPPORTED` set to include `".xlsx"` (and reuse the tuple from the helper module if you exposed one there).
3. Modify `read_file` to delegate to the helper functions, including the new Excel branch. Keep the fail-closed behavior where unknown types return `""` so unsupported files are silently skipped.
4. Update any audit/log strings, if present, to mention Office support.

## 5. Add regression tests
1. Under `tests/`, add a new module (e.g., `tests/test_readers_office.py`). Use the standard library `tempfile` helpers to create temporary `.docx` and `.xlsx` files during the test run.
2. Generate the `.docx` fixture via `python-docx` (if available) and `.xlsx` via `openpyxl`; skip the test with a descriptive message if the import fails (so CI still passes when wheels are absent).
3. Assert that the helper functions return normalized text containing both paragraph/table content for Word and sheet/row/cell content for Excel.
4. If a pytest runner is not already configured, add a `tests/__init__.py` (if missing) and ensure the repository’s CI entrypoint runs `python -m pytest`. Update docs/STATUS_BOARD or the relevant CI doc if needed.

## 6. Update user-facing documentation
1. Mention `.docx` and `.xlsx` support in `README.md` under **Quick Start** or **Day-2 Highlights** so operators know the capability exists.
2. If any security documentation references supported file types (e.g., `docs/Security_Checklist.md`), add the new formats and note they are processed fully offline via `python-docx`/`openpyxl`.
3. Add a brief note to `docs/QuickStart_card.md` about Office ingestion, including the requirement that the relevant wheels are bundled on the stick.

## 7. Validate end-to-end
1. After code edits, run the unit tests locally (`python -m pytest`).
2. Rebuild an index against a sample source that includes `.docx` and `.xlsx` files to verify chunks are emitted (see `services/indexer/build_index.py` for the existing CLI entry point).
3. For packaging, execute `packaging/build_<platform>` in a dry run with the new wheels staged to confirm the new dependencies are installed and copied into `App/`.

Keep every change offline-safe: no new network calls, no telemetry, and maintain the existing audit discipline. Treat any failure to locate the Office wheels during packaging as a packaging-time error, not a runtime surprise.
