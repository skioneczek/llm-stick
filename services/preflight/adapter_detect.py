# services/preflight/adapter_detect.py
# Returns True if ANY network adapter appears active (UP/Connected).
from __future__ import annotations
import subprocess, sys, os, re

def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, shell=False)
        return 0, out
    except Exception as e:
        try:
            return e.returncode, e.output  # type: ignore[attr-defined]
        except Exception:
            return 1, ""

def adapters_active() -> bool:
    plat = sys.platform
    # ---- Windows
    if plat.startswith("win"):
        # 1) PowerShell Get-NetAdapter (fast, modern)
        code, out = _run(["powershell", "-NoProfile", "-Command",
                          "(Get-NetAdapter | Where-Object {$_.Status -eq 'Up'}).Count"])
        if code == 0:
            try: return int(out.strip()) > 0
            except: pass
        # 2) netsh fallback
        code, out = _run(["netsh", "interface", "show", "interface"])
        if code == 0:
            # Look for 'Connected' in State column
            return bool(re.search(r"\bConnected\b", out, re.IGNORECASE))
        return True  # safe default

    # ---- macOS
    if plat == "darwin":
        # ifconfig shows "status: active" for up interfaces
        code, out = _run(["ifconfig", "-a"])
        if code == 0:
            return bool(re.search(r"status:\s*active", out, re.IGNORECASE))
        return True

    # ---- Linux & others
    # Prefer "ip link" then fallback to /sys/class/net
    code, out = _run(["/sbin/ip", "-o", "link", "show", "up"])
    if code == 0:
        return bool(out.strip())
    try:
        base = "/sys/class/net"
        for name in os.listdir(base):
            p = os.path.join(base, name, "operstate")
            if os.path.exists(p) and open(p).read().strip() == "up":
                return True
    except Exception:
        pass
    return True
