# Acceptance Script — Day 2 (2025-10-09)

## Preconditions
- Device stays air-gapped; leave adapters ON for Standard/Hardened; turn adapters OFF only for Paranoid pass check.
- Run commands from repo root; ensure default PIN `123456` and Samples index `Data/index.json` exist.
- Voice toggle must remain OFF on launch; large-text UI assumed.

## Scenario 1 — PIN Change / Reset Lifecycle
### 1A Happy Path (change then revert)
```powershell
python - <<'PY'
from services.security import pin_gate

first = pin_gate.change_pin("123456", "654321")
second = pin_gate.change_pin("654321", "123456")
print(first)
print(second)
PY
```
Expected: Each `PinResult` shows `ok=True` with messages `"PIN changed."`; lockout counters reset.

### 1B Failure Path (wrong current PIN)
```powershell
python - <<'PY'
from services.security import pin_gate

result = pin_gate.change_pin("000000", "222222")
print(result)
PY
```
Expected: `ok=False`, message `"PIN failed."`, lockout counter increments (`lockout.failed` > 0).

### 1C Lockout After Repeated Failed Unlocks
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
Expected: Attempts return `ok=False`. After 5th failure `lockout.lockout_until` becomes non-zero (15 min). Attempt 6 continues to deny with same lockout info; no hard lock yet.

### 1D Recovery Reset (success + failure)
```powershell
python - <<'PY'
from services.security import pin_gate, keystore
phrase = keystore.generate_recovery_phrase()
keystore.set_phrase(phrase)
print("reset_fail", pin_gate.reset_with_recovery("wrong phrase", "222222"))
print("reset_ok", pin_gate.reset_with_recovery(phrase, "123456"))
PY
```
Expected: First result `ok=False` with recovery error; second `ok=True` and message `"PIN reset."`.

## Scenario 2 — Standard Mode Guards (outbound/DNS blocked)
```powershell
python -m apps.launcher.main --mode standard --pin 123456 --probe --ask "Summarize Client A trust highlights" --index Data/index.json
```
Expected: `PIN accepted.` followed by Standard audit with adapters detected; probe outputs `DNS: BLOCKED (ok)` and `SOCKET: BLOCKED (ok)`; answer provides bullets plus Samples citations.

## Scenario 3 — Hardened Mode Guards + Temp Sandbox + Clear Logs Stub
```powershell
python -m apps.launcher.main --mode hardened --pin 123456 --probe --ask "List liquidity and distribution targets" --index Data/index.json
```
Expected: Hardened audit mentions outbound + DNS blocked and limited privileges; probe still blocked; `Data/tmp/` exists and env vars `TMP`, `TEMP`, `TMPDIR` point inside repo.

```powershell
python - <<'PY'
import os
print(os.environ.get("TMP"))
print(os.environ.get("TEMP"))
print(os.path.isdir(os.environ.get("TMP")))
PY
```
Expected: Printed paths under `Data/tmp/` and directory exists.

```powershell
python - <<'PY'
from services.security import net_guard
net_guard.wipe_temp_sandbox()
print("sandbox_reset", net_guard._tmp_root)
PY
```
Expected: Sandbox directory removed; `_tmp_root` prints `None`; follow-up check shows `Data/tmp/` regenerated clean by next guard run.

## Scenario 4 — Paranoid Mode Enforcement
```powershell
python -m apps.launcher.main --mode paranoid --pin 123456 --probe
```
Expected: Audit prints `Mode: Paranoid — Adapters detected; please disable Wi-Fi/unplug Ethernet.` and process exits before host alias or voice audits. Re-run with adapters physically disabled to confirm pass (optional).

## Scenario 5 — Voice Stub Loop (manual toggle only)
```powershell
python - <<'PY'
from services.preflight.audit import audit_voice
print(audit_voice(True).msg)
print(audit_voice(False).msg)
PY
```
Expected: Messages match `apps/ui/voice_script.md`: `"Voice Mode enabled. Hold space to speak."` then `"Voice Mode disabled."`

### Prompt/Answer Template Check
Re-use Standard/Hardened launcher runs above to confirm answers follow `docs/prompt_templates.md` patterns (plan → answer → sources) and require explicit "Sources" request before speaking citations.
