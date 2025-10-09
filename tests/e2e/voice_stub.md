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
