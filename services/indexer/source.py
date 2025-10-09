from __future__ import annotations
import hashlib
import os
from pathlib import Path
from typing import Tuple

DEFAULT_SOURCE = Path("Samples")
SOURCE_FILE = Path("Data/current_source.txt")
INDEX_DIR = Path("Data/indexes")


def _normalize(path: Path | str) -> Path:
    return Path(path).expanduser().resolve()


def set_current_source(path: Path | str) -> Path:
    """Persist the active source folder and return the resolved path."""
    resolved = _normalize(path)
    SOURCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_FILE.write_text(str(resolved), encoding="utf-8")
    return resolved


def get_current_source(default: Path | str | None = None) -> Path:
    """Read the active source folder, falling back to default when missing."""
    if SOURCE_FILE.exists():
        text = SOURCE_FILE.read_text(encoding="utf-8").strip()
        if text:
            return _normalize(text)
    default_path = _normalize(default or DEFAULT_SOURCE)
    return set_current_source(default_path)


def slug_for_source(path: Path | str) -> str:
    resolved = _normalize(path)
    return hashlib.sha1(str(resolved).encode("utf-8")).hexdigest()[:12]


def index_path_for_source(path: Path | str) -> Path:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    slug = slug_for_source(path)
    return INDEX_DIR / f"index_{slug}.json"


def stats_for_source(path: Path | str) -> Tuple[int, int]:
    """Return `(file_count, total_bytes)` for the resolved source folder."""
    resolved = _normalize(path)
    total_files = 0
    total_bytes = 0

    if not resolved.exists() or not resolved.is_dir():
        return total_files, total_bytes

    for root, _dirnames, filenames in os.walk(resolved, followlinks=False):
        base = Path(root)
        for name in filenames:
            candidate = base / name
            try:
                stat = candidate.stat(follow_symlinks=False)
            except OSError:
                continue
            total_files += 1
            total_bytes += stat.st_size

    return total_files, total_bytes


def hotswap_source(client: str, path: Path | str) -> Path:
    """Switch the active source and emit the hotswap audit line."""
    resolved = set_current_source(path)
    print(f"Hotswap activated: {client}")
    return resolved
