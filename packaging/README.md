# Packaging Overview

All builds run fully offline and assume the USB stick layout:

```
stick_root/
  App/
  Data/
  Docs/
  Samples/
```

`App/` contains the Python sources (`apps/launcher`), prebuilt AI binaries, and vendored dependencies. `Data/` is created at first run. Build scripts live alongside the repository and emit the expected `Start-*` artifacts into `/stick_root`.

## Prerequisites
- Python 3.11 with virtual environment support
- Nuitka or PyInstaller wheels downloaded to the local `vendor/` cache
- llama.cpp and whisper binaries pre-staged under `App/bin/`
- No network access during packaging

## Scripts
- `build_windows.ps1`
- `build_macos.sh`
- `build_linux.sh`

Each script accepts `--stick-root` (path to output layout) and `--python` (explicit interpreter). Dependencies are resolved from `vendor/` and no pip network calls are made.
