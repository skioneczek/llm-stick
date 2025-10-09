# services/preflight/host_alias.py
import os
from .audit import Audit, audit_host_alias

_DEFAULTS = {
    "win32": r"C:\OCRC_READONLY",
    "darwin": os.path.expanduser("~/OCRC_READONLY"),
    "linux": os.path.expanduser("~/OCRC_READONLY"),
}

def _platform_key():
    import sys
    if sys.platform.startswith("win"): return "win32"
    if sys.platform == "darwin": return "darwin"
    return "linux"

def bind_host_path(chosen: str | None = None) -> Audit:
    path = chosen or _DEFAULTS[_platform_key()]
    # Day-1 rule: it “passes” if the folder exists; our app enforces read-only by policy.
    exists = os.path.isdir(path)
    return audit_host_alias(path, exists)
