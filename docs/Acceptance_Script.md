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

# Acceptance Script — Day 3 (2025-10-10)

## Preconditions
- Device remains air-gapped; adapters stay ON for Standard/Hardened streaming checks and OFF for Paranoid validation.
- Default LLM profile targeted for Day-3 (`offline-balanced-q4`) and model assets staged under `App/models/llm/`; wrapper tooling lives in `core/llm/`.
- SHA256 manifests prepared beneath `packaging/checksums/` (one JSON manifest + `.sha256` files). Keep Windows `Get-FileHash` available for spot checks.
- Web UI static bundle rebuilt (including `apps/webui/static/app.js`) and SSE streaming flag enabled by Day-3 deliverable.

## Scenario 6 — LLM Wrapper & Registry (12:00 ET)
```powershell
python -m core.llm.wrap --list-profiles
```
Expected: Table lists `offline-balanced-q4` with footprint metadata and marks it `(default)`.

```powershell
python -m core.llm.wrap --run --profile offline-balanced-q4 --prompt "Summarize Client A trust highlights."
```
Expected: Wrapper streams tokens to stdout without network calls; exit code 0 when binaries/models present. On missing assets, returns actionable error referencing `App/bin/llama/` and `App/models/llm/` paths.

## Scenario 7 — Checksum Policy Enforcement (13:15 ET)
```powershell
Get-ChildItem packaging/checksums/*.sha256 | ForEach-Object { Get-Content $_ }
```
Expected: Manifests list SHA256 for each Day-3 artifact (LLM binaries, GGUF models, web assets).

```powershell
python - <<'PY'
import json, subprocess, pathlib
manifest = json.load(open('packaging/checksums/manifest.json', 'r', encoding='utf-8'))
for rel_path, expected in manifest.items():
    path = pathlib.Path(rel_path)
    result = subprocess.run(['powershell', '-NoLogo', '-Command', f"Get-FileHash -Algorithm SHA256 '{path}'"], capture_output=True, text=True)
    hash_line = next((line for line in result.stdout.splitlines() if line.strip().startswith('SHA256')), '')
    actual = hash_line.split(':', 1)[-1].strip()
    print(rel_path, actual == expected)
PY
```
Expected: Every entry prints `True`. Any mismatch blocks acceptance until corrected.

## Scenario 8 — Standard Streaming Web UI (15:30 ET)
```powershell
python -m apps.launcher.main --mode standard --pin 123456 --probe --ui standard --ask "List open questions for Client A"
```
Expected: Hardened-style audits for Standard mode (DNS/SOCKET blocked) then `Loopback Web UI available at http://127.0.0.1:<port>`. Browser opens automatically. In the UI, the answer renders incrementally (streaming chunks) before citations appear—verifiable in browser dev tools Network tab (`/stream` SSE).

## Scenario 9 — Hardened Streaming Parity (15:30 ET)
```powershell
python -m apps.launcher.main --mode hardened --pin 123456 --probe --ui enhanced --ask "Outline checksum policy for Day 3"
```
Expected: Hardened audit includes temp sandbox verification (`Temp sandbox — verified`). UI loads in enhanced (large text) view with the same streaming behaviour as Standard. Guard prints continue to show DNS/socket blocked.

## Scenario 10 — Paranoid CLI Fallback (17:30 ET)
```powershell
python -m apps.launcher.main --mode paranoid --pin 123456 --probe --ask "Confirm Paranoid fallback behaviour"
```
Expected: Paranoid audit refuses to launch UI (`UI server disabled in Paranoid mode.`) while CLI answer prints plan + bullets and cites `Sources` on demand. No browser window opens. Capture console transcript and checksum verification logs for the acceptance bundle.

