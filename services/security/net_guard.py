# services/security/net_guard.py
# Process-local outbound guard: monkeypatch sockets & DNS. No admin rights required.
from __future__ import annotations
import socket, builtins, os, tempfile, shutil
from typing import Any, Tuple

# Keep originals so we can restore if needed
_ORIG = {
    "socket": socket.socket,
    "create_connection": socket.create_connection,
    "getaddrinfo": socket.getaddrinfo,
}

class _BlockAllSockets(socket.socket):
    def connect(self, address: Tuple[str, int]) -> None:  # type: ignore[override]
        raise OSError("Outbound networking blocked by LLM Stick guard.")
    def connect_ex(self, address: Tuple[str, int]) -> int:  # type: ignore[override]
        raise OSError("Outbound networking blocked by LLM Stick guard.")

def _block_dns(*args: Any, **kwargs: Any):
    raise OSError("DNS resolution blocked by LLM Stick guard.")

def _patch_base(block_dns: bool):
    socket.socket = _BlockAllSockets   # type: ignore[assignment]
    socket.create_connection = _ORIG["create_connection"]  # keep for libs, but it uses socket underneath
    if block_dns:
        socket.getaddrinfo = _block_dns  # type: ignore[assignment]

def _restore():
    socket.socket = _ORIG["socket"]            # type: ignore[assignment]
    socket.create_connection = _ORIG["create_connection"]  # type: ignore[assignment]
    socket.getaddrinfo = _ORIG["getaddrinfo"]  # type: ignore[assignment]

def self_test(expect_blocked: bool=True) -> bool:
    # 1) DNS should fail if blocked, else may succeed (we only check "blocked" path here)
    try:
        socket.getaddrinfo("example.com", 80)  # noqa
        dns_blocked = False
    except Exception:
        dns_blocked = True
    # 2) Outbound socket should fail if blocked
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(("1.1.1.1", 80))
        s.close()
        sock_blocked = False
    except Exception:
        sock_blocked = True
    return (dns_blocked and sock_blocked) if expect_blocked else (not dns_blocked and not sock_blocked)

# Hardened/Paranoid temp sandbox (no host writes, but control temp locality)
_tmp_root = None
def enable_temp_sandbox(root: str):
    """Redirect temp dirs to an on-stick folder (created if missing)."""
    global _tmp_root
    _tmp_root = os.path.abspath(root)
    os.makedirs(_tmp_root, exist_ok=True)
    os.environ["TMPDIR"] = _tmp_root
    os.environ["TEMP"] = _tmp_root
    os.environ["TMP"] = _tmp_root
    tempfile.tempdir = _tmp_root

def wipe_temp_sandbox():
    global _tmp_root
    if _tmp_root and os.path.isdir(_tmp_root):
        shutil.rmtree(_tmp_root, ignore_errors=True)
    _tmp_root = None

def apply_standard_guards() -> bool:
    """Block outbound sockets and DNS at process level; verify with self-test."""
    _patch_base(block_dns=True)
    return self_test(expect_blocked=True)

def apply_hardened_guards(tmp_root: str) -> bool:
    """Standard + temp sandbox & (optionally) later privilege tightening."""
    _patch_base(block_dns=True)
    enable_temp_sandbox(tmp_root)
    return self_test(expect_blocked=True)

def clear_guards():
    _restore()

def probe_text() -> tuple[str, str]:
    """Run DNS+socket checks in the *current process* and return short lines."""
    import socket
    # DNS
    try:
        socket.getaddrinfo("example.com", 80)
        dns_line = "DNS: PASS (unexpected — should be blocked)"
    except Exception:
        dns_line = "DNS: BLOCKED (ok)"
    # SOCKET
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(("1.1.1.1", 80))
        s.close()
        sock_line = "SOCKET: PASS (unexpected — should be blocked)"
    except Exception:
        sock_line = "SOCKET: BLOCKED (ok)"
    return dns_line, sock_line
