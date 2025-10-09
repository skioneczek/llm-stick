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

## Scenario 8 — Loopback and HTTP Guard Audits
```powershell
python - <<'PY'
from services.security import net_guard, http_guard

ok, audit = net_guard.allow_loopback_only()
print(ok, audit)
net_guard.clear_guards()
print(net_guard.audit_ui_server_disabled())

headers, csp_audit = http_guard.apply_secure_headers({})
print(headers["Content-Security-Policy"])
print(csp_audit)
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
```powershell
python - <<'PY'
import os
from pathlib import Path
from services.security import source_guard

print(audit_voice(True).msg)
print(audit_voice(False).msg)
allowed_root = Path('Samples').resolve()
os.environ['LLM_STICK_ALLOWED_SOURCE'] = str(allowed_root)

ok, audit = source_guard.validate_source(str(Path('Samples/Client_A')))
print(ok, audit)

ok, audit = source_guard.validate_source(str(Path('C:/Windows')))
print(ok, audit)  # expect False, outside allowed root

# Trigger confirm-required by lowering thresholds
os.environ['LLM_STICK_SOURCE_MAX_FILES'] = '0'
ok, audit = source_guard.validate_source(str(Path('Samples/Client_A')))
print(ok, audit)  # expect False with confirm message
os.environ.pop('LLM_STICK_SOURCE_MAX_FILES')

# Symlink escape check (skip gracefully if symlinks unavailable)
link_root = allowed_root / 'link_escape'
target_outside = Path('..').resolve()
try:
    if link_root.exists() or link_root.is_symlink():
        link_root.unlink()
    link_root.symlink_to(target_outside, target_is_directory=True)
    ok, audit = source_guard.validate_source(str(link_root))
    print(ok, audit)  # expect False with escape message
except (OSError, NotImplementedError) as exc:
    print('Symlink test skipped:', exc)
finally:
    if link_root.is_symlink():
        link_root.unlink()
PY
```
