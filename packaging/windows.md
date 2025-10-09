# Windows Packaging Plan

## Goal
Produce a portable `Start-Windows.exe` launcher that lives at the root of the air-gapped stick (`stick_root/`) and bootstraps the Python runtime without installing anything on the host.

## Prerequisites
- **Python 3.11+** available offline to build artifacts.
- **Vendor cache** at `packaging/../vendor/` containing wheels for `pyinstaller`, `nuitka`, `zstandard`, and all application dependencies (no network calls during build).
- **Prebuilt binaries** (e.g., `llama.cpp`, `whisper`) staged under `App/bin/` within the repository.
- **Stick layout** prepared locally:
  ```
  stick_root/
    App/
    Data/
    Docs/
    Samples/
  ```
  (`Data/` may start empty; all runtime writes remain inside it.)

## Build Steps (PyInstaller backend)
1. Open an offline PowerShell session.
2. Run the build script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File packaging/build_windows.ps1 `
     -StickRoot C:\path\to\stick_root `
     -Python C:\Python311\python.exe `
     -VendorDir C:\offline\vendor `
     -Backend pyinstaller
   ```
3. Script actions:
   - Creates `.build/windows/` workspace with isolated virtualenv.
   - Installs PyInstaller from local wheel cache (`--no-index`).
   - Bundles `apps/launcher/__main__.py` into `Start-Windows.exe`.
   - Copies repository `App/`, `Docs/`, and `Samples/` into `stick_root/`.
   - Leaves all mutable data paths pointing to `stick_root/Data/`.
4. Verify outputs:
   - `stick_root/Start-Windows.exe`
   - `stick_root/App/` (Python package + binaries)
   - `stick_root/Docs/`, `stick_root/Samples/`

## Build Steps (Nuitka backend)
Repeat with `-Backend nuitka`. Nuitka produces a single-file executable; ensure `zstandard` wheel exists in cache.

## Launch Verification
- Double-click `Start-Windows.exe` from removable media.
- Confirm preflight audit line prints and only `Data/` receives writes (check `Data/logs/audits.log`).
- Ensure the PIN gate appears before any UI loads.

## Maintenance Notes
- Update `packaging/build_windows.ps1` when dependencies change. Always re-populate `vendor/` offline before packaging.
- Maintain `Start-Windows.ps1` shim for development mode; production binary embeds equivalent logic.
