# services/preflight/audit.py
from dataclasses import dataclass
from enum import Enum

class Mode(Enum):
    STANDARD = "standard"
    HARDENED = "hardened"
    PARANOID = "paranoid"

@dataclass
class Audit:
    ok: bool
    msg: str

def audit_pin(unlocked: bool) -> Audit:
    return Audit(ok=unlocked, msg=("PIN accepted." if unlocked else "PIN failed."))

def audit_mode(mode: Mode, adapters_active: bool, guards_ok: bool) -> Audit:
    if mode == Mode.PARANOID:
        if adapters_active:
            return Audit(False, "Mode: Paranoid — Adapters detected; please disable Wi-Fi/unplug Ethernet.")
        return Audit(True, "Mode: Paranoid — No adapters detected; sandbox active; proceeding.")
    # Standard/Hardened
    if not guards_ok:
        return Audit(False, f"Mode: {mode.value.capitalize()} — Network guard failed; reverting.")
    if mode == Mode.STANDARD:
        return Audit(True, "Mode: Standard — Outbound sockets blocked; DNS blocked; adapters detected; proceeding.")
    return Audit(True, "Mode: Hardened — Outbound+DNS blocked; limited privileges; adapters detected; proceeding.")

def audit_voice(enabled: bool) -> Audit:
    return Audit(True, ("Voice Mode enabled. Hold space to speak." if enabled else "Voice Mode disabled."))

def audit_host_alias(path: str, readonly_ok: bool) -> Audit:
    if readonly_ok:
        return Audit(True, f"Host folder bound read-only: {path}")
    return Audit(False, "Read-only binding failed; select another folder.")
