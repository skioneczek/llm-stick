-from pathlib import Path
-
-LOG_DIR = Path("Data") / "logs"
-AUDIT_LOG = LOG_DIR / "audits.log"
-VOICE_LOG = LOG_DIR / "voice.log"
-TMP_DIR = Path("Data") / "tmp"
-
-def _safe_unlink(path: Path) -> None:
-    try:
-        if path.exists():
-            path.unlink()
-    except Exception:
-        pass
-
-def _safe_rmtree(path: Path) -> None:
-    if not path.exists():
-        return
-    for entry in path.iterdir():
-        if entry.is_dir():
-            _safe_rmtree(entry)
-        else:
-            _safe_unlink(entry)
-    try:
-        path.rmdir()
-    except Exception:
-        pass
-
-def clear_logs() -> str:
-    LOG_DIR.mkdir(parents=True, exist_ok=True)
-    for log in (AUDIT_LOG, VOICE_LOG):
-        _safe_unlink(log)
-        log.touch()
-    return "Logs cleared." (all files reset)
-
-def wipe_temps() -> str:
-    TMP_DIR.mkdir(parents=True, exist_ok=True)
-    _safe_rmtree(TMP_DIR)
-    TMP_DIR.mkdir(parents=True, exist_ok=True)
-    return "Temporary workspace wiped." (Data/tmp reset)
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
