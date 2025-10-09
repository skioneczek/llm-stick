from __future__ import annotations
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Iterator

from services.indexer.build_index import build_index
from services.indexer.source import slug_for_source
from services.ingest.queue import load_job, update_job
from services.ingest.registry import register_client
from services.memory.ledger import add as ledger_add
from services.security.crypto_provider import get_provider

HOST_LOCAL_ROOT = Path(os.environ.get("LLM_STICK_HOST_CACHE", Path.home() / ".llmstick"))
STICK_ENCRYPTED_ROOT = Path("Data/ingested")
OCR_BIN_DIR = Path("bin")


class OCRUnavailable(RuntimeError):
    pass


def _iter_files(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        base = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not (base / d).is_symlink()]
        for name in filenames:
            candidate = base / name
            if candidate.is_symlink():
                continue
            yield candidate


def _ocr_available() -> bool:
    tesseract = OCR_BIN_DIR / "tesseract"
    pdftotext = OCR_BIN_DIR / "pdftotext"
    return tesseract.exists() or pdftotext.exists()


def _normalize_file(path: Path) -> str:
    """Return best-effort UTF-8 text extraction."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

{{ ... }}


def run_job(job_id: str) -> Dict[str, object]:
    job = load_job(job_id)
    source = Path(job["source"]).expanduser().resolve()
    dest = Path(job["dest"]).expanduser().resolve() if job.get("dest") else None
    storage_mode = job.get("storage_mode", "HOST_LOCAL").upper()
    client_slug = job["client_slug"]
    crypto_name = job.get("crypto_provider")

    start_ts = int(time.time())
    job_record = update_job(job_id, {"status": "running", "started_at": start_ts})

    ocr_ready = _ocr_available()
    job_record["ocr_available"] = ocr_ready
    update_job(job_id, {"ocr_available": ocr_ready})

    files_processed = 0
    temp_dir = Path("Data/tmp/ingest") / job_id
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    chunks_dir = temp_dir / "chunks"

    for source_file in _iter_files(source):
        text = _normalize_file(source_file)
        if not text:
            continue
        _write_temp_chunks(chunks_dir, source_file, text)
        files_processed += 1

    slug = slug_for_source(source)

    if storage_mode == "HOST_LOCAL":
        base_root = dest if dest else HOST_LOCAL_ROOT.expanduser()
        host_dir = (base_root / ".llmstick" / slug)
        host_dir.mkdir(parents=True, exist_ok=True)
        index_path = host_dir / "index.json"
        stats = build_index(chunks_dir, index_path)
        ledger_add(client_slug, "ingest", f"Indexed {stats['files']} files", source_slug=slug)
    elif storage_mode == "STICK_ENCRYPTED":
        STICK_ENCRYPTED_ROOT.mkdir(parents=True, exist_ok=True)
        encrypted_dir = STICK_ENCRYPTED_ROOT / slug
        encrypted_dir.mkdir(parents=True, exist_ok=True)
        index_path = encrypted_dir / "index.enc"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        provider = get_provider(crypto_name)
        temp_index = temp_dir / "index.json"
        stats = build_index(chunks_dir, temp_index)
        ok, audit_line = provider.encrypt_file(temp_index, index_path)
        ledger_add(client_slug, "ingest", audit_line, source_slug=slug)
        temp_index.unlink(missing_ok=True)
        if not ok:
            update_job(job_id, {"status": "failed", "error": audit_line, "completed_at": int(time.time())})
            raise RuntimeError(audit_line)
    else:
        update_job(job_id, {"status": "failed", "error": f"Unsupported storage mode {storage_mode}", "completed_at": int(time.time())})
        raise RuntimeError(f"Unsupported storage mode {storage_mode}")

    registry_entry = {
        "client_slug": client_slug,
        "source": str(source),
        "storage_mode": storage_mode,
        "index_path": str(index_path),
        "files": stats.get("files", 0),
        "chunks": stats.get("chunks", 0),
        "size_bytes": stats.get("size_bytes", 0),
        "slug": slug,
        "updated_at": int(time.time()),
        "ocr_available": ocr_ready,
        "job_id": job_id,
    }

    register_client(client_slug, registry_entry)

    update_job(job_id, {
        "status": "completed",
        "completed_at": int(time.time()),
        "registry_entry": registry_entry,
        "files_processed": files_processed,
    })

    shutil.rmtree(temp_dir, ignore_errors=True)

    return registry_entry
