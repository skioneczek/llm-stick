from __future__ import annotations
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any

JOBS_DIR = Path("Data/ingest_jobs")


def _ensure_jobs_dir() -> None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)


def enqueue_job(
    source: str,
    dest: str,
    client_slug: str,
    counts: Dict[str, int],
    storage_mode: str = "HOST_LOCAL",
    crypto_provider: str | None = None,
) -> str:
    """Create an ingest job file and return its identifier."""
    _ensure_jobs_dir()
    job_id = f"job-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    job_path = JOBS_DIR / f"{job_id}.json"
    payload: Dict[str, Any] = {
        "job_id": job_id,
        "source": source,
        "dest": dest,
        "client_slug": client_slug,
        "counts": counts,
        "created_at": int(time.time()),
        "status": "queued",
        "storage_mode": storage_mode.upper(),
        "crypto_provider": crypto_provider,
    }
    job_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return job_id


def job_path(job_id: str) -> Path:
    _ensure_jobs_dir()
    return JOBS_DIR / f"{job_id}.json"


def load_job(job_id: str) -> Dict[str, Any]:
    path = job_path(job_id)
    if not path.exists():
        raise FileNotFoundError(f"Ingest job not found: {job_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def update_job(job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    path = job_path(job_id)
    data = load_job(job_id)
    data.update(updates)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
