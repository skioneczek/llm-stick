"""Log and temp maintenance primitives for the security stack."""
from __future__ import annotations

import os
import shutil
from pathlib import Path


DATA_ROOT = Path("Data")
LOG_GLOB = "*.log"
LEDGER_PATH = DATA_ROOT / "memory_ledger.json"
TMP_ROOT = DATA_ROOT / "tmp"


def clear_logs(include_ledger: bool = False) -> str:
    """Remove local log files under Data/ and optionally the memory ledger."""
    if not DATA_ROOT.exists():
        return "Security audit — no logs to clear (Data/ missing)."

    removed = 0
    for entry in DATA_ROOT.iterdir():
        if entry.is_file() and entry.match(LOG_GLOB):
            try:
                entry.unlink()
                removed += 1
            except OSError:
                pass

    if include_ledger and LEDGER_PATH.exists():
        try:
            LEDGER_PATH.unlink()
        except OSError:
            pass
    suffix = " (ledger cleared)" if include_ledger else ""
    return f"Security audit — cleared {removed} log file(s){suffix}."


def wipe_temps() -> str:
    """Delete the temp working directory recursively, ignoring errors."""
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT, ignore_errors=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    return "Security audit — temp workspace wiped."
