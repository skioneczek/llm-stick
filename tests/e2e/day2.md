# Day 2 E2E Checklist (Mirrors `docs/Acceptance_Script.md`)

## Scenario 1 — PIN Change / Reset Lifecycle

### 1A Happy Path
```powershell
python - <<'PY'
from services.security import pin_gate

first = pin_gate.change_pin("123456", "654321")
second = pin_gate.change_pin("654321", "123456")
print(first)
print(second)
PY
```

### 1B Wrong Current PIN
```powershell
python - <<'PY'
from services.security import pin_gate

result = pin_gate.change_pin("000000", "222222")
print(result)
PY
```

### 1C Lockout After Repeated Failures
```powershell
python - <<'PY'
from services.security import pin_gate
states = []
for attempt in range(1, 7):
    res = pin_gate.unlock_with_pin("999999")
    states.append((attempt, res.ok, res.message, res.lockout.failed, res.lockout.lockout_until, res.lockout.hard_lock))
print(states)
PY
```

### 1D Recovery Reset
```powershell
python - <<'PY'
from services.security import pin_gate, keystore
phrase = keystore.generate_recovery_phrase()
keystore.set_phrase(phrase)
print("reset_fail", pin_gate.reset_with_recovery("wrong phrase", "222222"))
print("reset_ok", pin_gate.reset_with_recovery(phrase, "123456"))
PY
```

## Scenario 2 — Standard Mode Guards
```powershell
python -m apps.launcher.main --mode standard --pin 123456 --probe --ask "Summarize Client A trust highlights" --index Data/index.json
```

## Scenario 3 — Hardened Mode Guards + Temp Sandbox
```powershell
python -m apps.launcher.main --mode hardened --pin 123456 --probe --ask "List liquidity and distribution targets" --index Data/index.json
```

```powershell
python - <<'PY'
import os
print(os.environ.get("TMP"))
print(os.environ.get("TEMP"))
print(os.path.isdir(os.environ.get("TMP")))
PY
```

```powershell
python - <<'PY'
from services.security import net_guard
net_guard.wipe_temp_sandbox()
print("sandbox_reset", net_guard._tmp_root)
PY
```

## Scenario 4 — Paranoid Mode Enforcement
```powershell
python -m apps.launcher.main --mode paranoid --pin 123456 --probe
```

## Scenario 5 — Voice Stub Loop
```powershell
python - <<'PY'
from services.preflight.audit import audit_voice
print(audit_voice(True).msg)
print(audit_voice(False).msg)
PY
```
