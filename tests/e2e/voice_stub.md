# Voice Mode Stub Test — Day 2 Prep

## Purpose
Verify that enabling Voice Mode triggers the offline TTS hook without requiring real hardware synthesis.

## Preconditions
- Voice binaries absent or replaced with placeholders in `App/bin/tts/`.
- `VoiceAnnouncer` configured with mock synthesizer that records invocations.
- Voice Mode toggle stored in `Data/config/voice_mode.json.enc`.

## Steps
1. Launch `python -m apps.launcher.main --mode standard --voice --probe`
2. After PIN acceptance, confirm log entry in `Data/logs/voice.log` with line `Voice Mode enabled.`
3. Ensure console prints “Voice Mode enabled. (stub)” from mock synthesizer.
4. Answer `No` to watcher prompt; verify no indexing begins.
5. Exit launcher; open `Data/logs/voice.log` and confirm no additional voice lines (only initial ready signal).

## Expected Results
- No network calls, all voice output simulated locally.
- TTS hook uses OS voice when available, otherwise falls back to `App/bin/tts/espeak-ng` (not invoked during stub test).
- Voice Mode toggle persists across relaunch; disabling it should append `Voice Mode disabled.` to log and suppress announcements.

PS C:\Users\eric\OneDrive\Documents\R-Team> python -m apps.launcher.main --mode hardened --voice --probe --ask "List open questions for Client A"
PIN accepted.
Temp sandbox — verified (paths under Data/tmp).
Mode: Hardened — Outbound+DNS blocked; limited privileges; adapters detected; proceeding.
Host folder bound read-only: C:\OCRC_READONLY
Voice Mode enabled. Hold space to speak.
DNS: BLOCKED (ok)
SOCKET: BLOCKED (ok)
TTS> Ready.
Plan: review retrieved chunks for "List open questions for Client A" and surface key takeaways.
- purpose and overview this illustrative family trust is designed to steward multi asset wealth for two generations while preserving flexibility for changing circumstances it is a neutral sample set for testing an offline ai workflow not advice the trust aims …
- crut charitable remainder unitrust that pays a percentage to noncharitable beneficiaries with the remainder to charity grat grantor retained annuity trust that returns an annuity to the grantor for a term remainder to beneficiaries fmv fair market value the price …
Ask "Sources?" for file names and dates.

Sources:
- Client_A\Trust_Structure_Overview.txt (modified 2025-10-08)
- Shared\Glossary.md (modified 2025-10-08)
Plan: review retrieved chunks for "List open questions for Client A" and surface key takeaways.       
- purpose and overview this illustrative family trust is designed to steward multi asset wealth for two generations while preserving flexibility for changing circumstances it is a neutral sample set for testing an offline ai workflow not advice the trust aims …
- crut charitable remainder unitrust that pays a percentage to noncharitable beneficiaries with the remainder to charity grat grantor retained annuity trust that returns an annuity to the grantor for a term remainder to beneficiaries fmv fair market value the price …
Ask "Sources?" for file names and dates.

Sources:
- Trust_Structure_Overview.txt (modified 2025-10-08)
- Glossary.md (modified 2025-10-08)
TTS> Plan: review retrieved chunks for "List open questions for Client A" and surface key takeaways.  
PS C:\Users\eric\OneDrive\Documents\R-Team>  