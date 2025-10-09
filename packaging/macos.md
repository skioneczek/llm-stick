# macOS Packaging Plan

## Goal
Deliver a portable `Start-macOS.app` bundle that runs entirely from the removable stick with no installer or network requirements.

## Prerequisites
- **macOS 13+** build host with Xcode command-line tools (for codesign if desired).
- **Python 3.11+** available offline.
- **Vendor cache** located at `packaging/../vendor/` containing wheels for PyInstaller/Nuitka and application dependencies.
- **App binaries** (llama.cpp, whisper, etc.) already copied under `App/bin/` inside the repo.
- **Stick layout** staged locally:
  ```
  stick_root/
    App/
    Data/
    Docs/
    Samples/
  ```

## Build Steps (PyInstaller backend)
1. Launch an offline terminal.
2. Run:
   ```bash
   VENDOR_DIR=/Volumes/Offline/vendor \
   PYTHON=/usr/local/bin/python3 \
   BACKEND=pyinstaller \
   packaging/build_macos.sh /Volumes/Offline/stick_root
   ```
3. Script actions:
   - Creates `.build/macos/` workspace with venv.
   - Installs PyInstaller from wheel cache (`--no-index`).
   - Bundles `apps/launcher/__main__.py` into `Start-macOS.app` (within the stick root).
   - Syncs `App/`, `Docs/`, `Samples/` into `stick_root/`.

## Build Steps (Nuitka backend)
- Set `BACKEND=nuitka` before invoking the script. Nuitka is configured to emit an `.app` bundle. Ensure `zstandard` wheel is present.

## Optional Codesign & Notarization
- Offline builds skip signing by default. For local codesign (no notarization), run after packaging:
  ```bash
  codesign --deep --force --sign - stick_root/Start-macOS.app
  ```
- Notarization is incompatible with air-gap requirements; do not submit to Apple services.

## Launch Verification
- From Finder, double-click `Start-macOS.app`. Confirm:
  - PIN pad appears with large-text UI, no voice output unless Voice Mode toggled.
  - Preflight audit message logs to `Data/logs/audits.log`.
  - Host read-only binding defaults to `~/OCRC_READONLY/` or stored alias.
  - All writes confined to `Data/`.

## Maintenance Notes
- Keep `packaging/build_macos.sh` aligned with dependency changes and new binaries.
- Ensure the `.app` bundle includes shell wrapper `Start-macOS.command` for developer parity.
- Refresh vendor cache whenever dependencies or Python minor versions change; never allow pip to reach the internet during packaging.
