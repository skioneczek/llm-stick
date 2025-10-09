# Speech Pipeline — Placeholder Notes

Speech-to-text and text-to-speech remain fully offline. The launcher wires into `core/stt` for future integrations; today we expose staging guidelines.

## Whisper Runtime (STT)
```
App/
  bin/
    whisper/
      whisper-windows-x64.exe
      whisper-macos-arm64
      whisper-linux-x64
  models/
    stt/
      base.en.bin
      small.en.bin
```
- Binaries mirror `llama.cpp` layout and are invoked via `core.stt.whisper.run(audio_path, model_path, binary_path)` (to be implemented).
- Audio captured from Voice Mode stays under `Data/audio/` and is deleted after transcription.
- If binaries or models are missing, raise a `WhisperMissing` error with remediation text: “Drop whisper binaries under `App/bin/whisper/` and models under `App/models/stt/`.”

## Text-to-Speech Hook
- Use OS-native synthesis when available:
  - Windows: SAPI via `powershell Add-Type` / `Speak()`.
  - macOS: `/usr/bin/say` with `--voice` set from accessibility settings.
- Linux fallback: package `App/bin/tts/espeak-ng` and invoke with `--stdout` piping directly to ALSA/Pulse.
- All calls go through `core.stt.tts.speak(text, voice_mode)`; the function should no-op if Voice Mode is disabled.
- Respect audits: log announcements in `Data/logs/voice.log` without capturing microphone input.

## Next Milestones
- Implement PCM capture shim (`core/stt/capture.py`) writing to `Data/audio/session-*.wav`.
- Add unit tests that simulate missing binaries and confirm graceful prompts.
- Provide configuration file (`Data/config/voice_prefs.json.enc`) for per-user voice selection when Voice Mode is ON.
