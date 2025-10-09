# services/security/pin_gate.py
# Stub: in-memory only for Day 1; Data/ encryption wires in later.
_STORED_PIN = "123456"  # replace during real init

def unlock_with_pin(pin: str) -> bool:
    return pin == _STORED_PIN

def change_pin(current: str, new_pin: str) -> bool:
    global _STORED_PIN
    if current != _STORED_PIN or len(new_pin) != 6 or not new_pin.isdigit():
        return False
    _STORED_PIN = new_pin
    return True
