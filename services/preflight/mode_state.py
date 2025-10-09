# services/preflight/mode_state.py
from .audit import Mode, Audit, audit_mode

_current_mode = Mode.STANDARD
_adapters_active = True          # Integrator will replace with real detection
_guards_ok = True                # Security will set after guard attempts

def get_mode() -> Mode:
    return _current_mode

def set_mode(new_mode: Mode) -> Audit:
    global _current_mode
    # confirmation UI for restrictive modes lives in apps/ui; assume confirmed
    result = audit_mode(new_mode, _adapters_active, _guards_ok)
    if result.ok:
        _current_mode = new_mode
    return result

# These allow Integrator/Security to feed real values:
def set_adapters_active(active: bool):  # called by Integrator
    global _adapters_active
    _adapters_active = active

def set_guards_ok(ok: bool):            # set True once guards applied
    global _guards_ok
    _guards_ok = ok
