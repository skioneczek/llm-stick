# services/security/pin_gate.py
from __future__ import annotations
from dataclasses import dataclass
from . import keystore as ks

@dataclass
class PinResult:
    ok: bool
    message: str
    lockout: ks.LockoutState

def first_boot_phrase_if_any() -> str | None:
    """Return phrase on first boot so user can write it down; None otherwise."""
    return ks.init_if_missing(default_pin="123456")

def unlock_with_pin(pin: str) -> PinResult:
    st = ks.check_lockout()
    if st.hard_lock:
        return PinResult(False, "Hard lock: too many failures. Re-plug required.", st)
    if st.lockout_until:
        remaining = max(0, st.lockout_until - ks._now())
        return PinResult(False, f"Timed lock: wait {remaining//60} min.", st)
    ok = ks.verify_pin(pin)
    if ok:
        ks.clear_failures()
        return PinResult(True, "PIN accepted.", ks.check_lockout())
    ks.record_failed_attempt()
    st = ks.check_lockout()
    return PinResult(False, "PIN failed.", st)

def change_pin(current: str, new_pin: str) -> PinResult:
    check = ks.verify_pin(current)
    if not check:
        ks.record_failed_attempt()
        return PinResult(False, "PIN failed.", ks.check_lockout())
    if not ks.set_pin(new_pin):
        return PinResult(False, "New PIN must be 6 digits.", ks.check_lockout())
    return PinResult(True, "PIN changed.", ks.check_lockout())

def reset_with_recovery(phrase: str, new_pin: str) -> PinResult:
    if not ks.verify_phrase(phrase):
        return PinResult(False, "Recovery phrase incorrect.", ks.check_lockout())
    if not ks.set_pin(new_pin):
        return PinResult(False, "New PIN must be 6 digits.", ks.check_lockout())
    return PinResult(True, "PIN reset.", ks.check_lockout())
