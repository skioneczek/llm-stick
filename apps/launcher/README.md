# Launcher Architecture

## Overview
The launcher stack provides a single entry point across Windows, macOS, and Linux for the air‑gapped "LLM Stick." Each launcher wraps the same Python core (`apps.launcher`) and performs:

1. PIN gate & key vault handshake.
2. Security mode enforcement via `services.preflight`.
3. Host read-only folder binding and alias caching.
4. UI bootstrap with optional voice annunciation.
5. Passive file discovery prompts during runtime.

## Components
- `core.py`: Main orchestration class that coordinates PIN checks, preflight enforcement, UI startup, and file watching.
- `pinpad.py`: CLI PIN prompt wrapper around `services.security` interfaces.
- `preflight.py`: Concrete implementations that adapt the protocol definitions in `services.preflight.interfaces` to the launcher environment.
- `host_binding.py`: Resolves and persists the read-only host folder alias under `Data/` using encrypted storage.
- `watcher.py`: Poll-based file watcher that stays on-stick and surfaces new file counts.
- `voice.py`: Dispatches the optional voice announcement hook controlled by the Voice Mode toggle.
- `__main__.py`: Entry point used by packaging to produce `Start-*` binaries.

## Start Flow
1. `Start-*` wrapper (per OS) resolves the stick root, sets `LLM_STICK_ROOT`, and runs `python -m apps.launcher` (portable binary entry point in production).
2. `LauncherPaths.discover()` validates `App/`, creates `Data/`, `Docs/`, `Samples/` if missing.
3. `PinPad.obtain_pin()` prompts for the 6-digit PIN, applying lockout rules before unlocking the encrypted `Data/` volume.
4. `HostBindingManager.ensure_binding(pin_ctx)` reads the cached host alias (encrypted under PIN); if unavailable, validates the mandated read-only default (`C:\OCRC_READONLY\` on Windows, `~/OCRC_READONLY/` elsewhere) or prompts once for a substitute. Successful selection persists to `Data/config/host_alias.json.enc`.
5. `PreflightController.enforce(active_mode)` executes the security policy (see pseudocode below), stores the 1–2 line audit in `Data/logs/audits.log`, and returns pass/fail.
6. `VoiceAnnouncer.is_enabled(pin_ctx)` and `VoiceAnnouncer.ready(...)` restore/apply the Voice Mode toggle (default false), storing state under `Data/config/voice_mode.json.enc`; optional synthesizer announces readiness.
7. UI thread launches with `ui_runner(app_dir, host_path, voice_enabled)`, while `FileWatcher.begin(host_path)` starts polling the read-only host alias.
8. Watcher prompts: “Found N new files. Index now?” — indexing only proceeds on user approval; all write activity remains inside `Data/`.
9. On exit, watcher stops and the key vault is re-locked.

## Host Binding Pseudocode
```python
def ensure_binding(pin_ctx):
    alias = secure_config.read("host_alias", pin_ctx.pin)
    if alias and is_valid(alias.path):
        return Path(alias.path)

    default_path = policy.expected_root().expanduser()
    if is_valid(default_path):
        secure_config.write("host_alias", pin_ctx.pin, {"path": str(default_path)})
        return default_path

    for attempt in range(3):
        candidate = prompt.choose_path()
        if is_valid(candidate):
            secure_config.write("host_alias", pin_ctx.pin, {"path": str(candidate.resolve())})
            return candidate
        prompt.notify_invalid(f"Path '{candidate}' is not readable.")

    raise HostBindingError("Unable to bind read-only host folder.")
```

`is_valid()` checks directory existence, read permission, and rejects non-folders. Alias data is encrypted with a PIN-derived key via `SecureConfig`.

## Mode Enforcement Pseudocode
```python
def enforce(mode):
    temps.purge()
    network.deny_outbound()

    if mode in {HARDENED, PARANOID}:
        network.disable_dns()
    if mode is HARDENED:
        privileges.drop_excess()

    adapters = inspector.list_active()
    if mode is PARANOID and adapters:
        audit.emit(AuditResult(mode, False, PARANOID_BLOCK_AUDIT))
        return AuditResult(mode, False, PARANOID_BLOCK_AUDIT)

    if not network.self_test():
        message = f"{message_for(mode, bool(adapters))} Network self-test failed; refusing to continue."
        audit.emit(AuditResult(mode, False, message))
        return AuditResult(mode, False, message)

    message = message_for(mode, bool(adapters))
    audit.emit(AuditResult(mode, True, message))
    return AuditResult(mode, True, message)
```

`message_for()` selects the standard/hardened/paranoid audit strings. AUDIT logs append to `Data/logs/audits.log`, and the launcher reverts to the previous mode on failure.

## Per-OS Wrappers
- `Start-Windows.ps1`: PowerShell shim executed by PyInstaller/Nuitka output (`Start-Windows.exe`).
- `Start-macOS.command`: Double-clickable shell script packaged into `Start-macOS.app`.
- `Start-Linux.sh`: Bash wrapper bundled inside the AppImage (`Start-Linux.AppImage`).

Each wrapper ensures Python runtime isolation, sets `LLM_STICK_ROOT`, and launches the shared Python module.

## Data Layout
```
stick_root/
  Start-Windows.exe
  Start-macOS.app/
  Start-Linux.AppImage
  App/
    launcher/
      ... (Python package)
  Data/
    config/
      host_alias.json.enc
      voice_mode.json.enc
    logs/
      audits.log
  Docs/
  Samples/
```

- `Data/` is only writable by the application. Alias metadata is AES-encrypted with a key derived from the active PIN.
- `Docs/` and `Samples/` ship neutral placeholder content.

## Security Modes
`core.LauncherApp` wires the security slider to the enforcement policy:
- **Standard:** Block outbound sockets, DNS optional.
- **Hardened:** Block outbound + DNS, drop privileges.
- **Paranoid:** Require adapters disabled; refuse to start otherwise.

Every mode transition triggers a self-check audit; success continues, failure reverts to the previous mode.

## Offline Packaging
Common build interface lives under `packaging/`:
- `build_windows.ps1` → Nuitka or PyInstaller CLI.
- `build_macos.sh` → create `.app` bundle.
- `build_linux.sh` → produce AppImage via `pyinstaller` + `appimagetool`.

All scripts rely on vendored dependencies and operate without network access.

## Future Hooks
- Replace CLI PIN prompt with tactile UI once `apps/ui` implements accessibility surfaces.
- Integrate real voice synthesis pipeline in `voice.py` when Speech Mode ships.
