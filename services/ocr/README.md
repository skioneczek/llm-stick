# Offline OCR Binaries

## Required Tools
- **Tesseract** (`bin/tesseract`): Used for image/PDF OCR when the text layer is missing.
- **pdftotext** (`bin/pdftotext`): Provides fast text extraction for PDFs with embedded text layers.

Both executables must be copied into the repository-local `bin/` directory. No installers or network calls are made; the ingest worker simply checks for their presence and executes them directly.

## Installation Steps
1. Obtain portable builds of Tesseract and `pdftotext` compatible with the host OS.
2. Place the binaries (and required DLLs if on Windows) under `bin/` so the paths look like:
   - `bin/tesseract`
   - `bin/pdftotext`
3. Ensure the files have execute permissions (on Unix-like systems: `chmod +x bin/tesseract bin/pdftotext`).

## Runtime Behaviour
- When both binaries are present, ingest OCR will attempt to extract text from image-heavy PDFs before chunking.
- If either binary is missing, the worker logs `ocr_available: false` in the job record and registry entry, and proceeds with plain-text extraction only.
- No outbound networking occurs; all OCR work is performed locally within the guarded environment.
