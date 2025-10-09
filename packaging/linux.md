# Linux Packaging Plan

## Goal
Produce a portable `Start-Linux.AppImage` that executes directly from the removable stick without installation or network access.

## Prerequisites
- **Linux build host** (Ubuntu 22.04 or similar) with AppImage tooling permissions.
- **Python 3.11+** available offline.
- **Vendor cache** at `packaging/../vendor/` containing wheels for PyInstaller/Nuitka, `zstandard`, and all Python dependencies.
- **App binaries** staged under `App/bin/` in the repository.
- **AppImageTool** extracted offline at `vendor/appimagetool/AppRun` (executable).
- **Stick layout** staged locally:
  ```
  stick_root/
    App/
    Data/
    Docs/
    Samples/
  ```

## Build Steps (PyInstaller backend)
1. Run offline shell:
   ```bash
   VENDOR_DIR=/mnt/offline/vendor \
   PYTHON=/opt/python/bin/python3 \
   BACKEND=pyinstaller \
   packaging/build_linux.sh /mnt/offline/stick_root
   ```
2. Script actions:
   - Creates `.build/linux/` workspace with venv.
   - Installs PyInstaller from wheel cache (`--no-index`).
   - Produces a standalone binary (`Start-Linux`) inside the build dist directory.
   - Assembles an AppDir with desktop entry and optional icon.
   - Invokes `appimagetool` to generate `Start-Linux.AppImage`.
   - Copies `App/`, `Docs/`, and `Samples/` into the stick root.

## Build Steps (Nuitka backend)
- Set `BACKEND=nuitka`. The script will use Nuitka's standalone binary output as the AppDir payload. Ensure `zstandard` wheel is present.

## Launch Verification
- Mark the AppImage executable (`chmod +x Start-Linux.AppImage`).
- Run from terminal or file manager. Confirm:
  - PIN entry precedes UI.
  - Enforced mode audit logged to `Data/logs/audits.log`.
  - Host binding defaults to `~/OCRC_READONLY/` (or cached alias) and only reads from host path.
  - All writes remain inside `Data/` (check `Data/config/` and `Data/logs/`).

## Maintenance Notes
- Keep `packaging/build_linux.sh` synchronized with dependency updates and icons under `App/icons/`.
- Ensure `vendor/appimagetool/` stays version-locked and accessible; no downloads during packaging.
- Provide shell wrapper `apps/launcher/scripts/Start-Linux.sh` for developer convenience; production AppImage embeds equivalent logic.
