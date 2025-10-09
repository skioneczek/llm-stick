#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STICK_ROOT="${1:-"$SCRIPT_DIR/../stick_root"}"
PYTHON_BIN="${PYTHON:-python3}"
VENDOR_DIR="${VENDOR_DIR:-"$SCRIPT_DIR/../vendor"}"
BACKEND="${BACKEND:-pyinstaller}"

if [ ! -d "$STICK_ROOT" ]; then
  echo "Stick root '$STICK_ROOT' is missing. Create the layout before packaging." >&2
  exit 1
fi
if [ ! -d "$VENDOR_DIR" ]; then
  echo "Vendor cache '$VENDOR_DIR' is missing. Populate offline dependencies first." >&2
  exit 1
fi

BUILD_ROOT="$SCRIPT_DIR/.build/macos"
VENV_PATH="$BUILD_ROOT/.venv"
DIST_DIR="$BUILD_ROOT/dist"
SPEC_DIR="$BUILD_ROOT/spec"
mkdir -p "$BUILD_ROOT" "$DIST_DIR" "$SPEC_DIR"

if [ ! -d "$VENV_PATH" ]; then
  "$PYTHON_BIN" -m venv "$VENV_PATH"
fi
VENV_PYTHON="$VENV_PATH/bin/python"
PIP_ARGS=("install" "--no-index" "--find-links" "$VENDOR_DIR/wheels")
if [ "$BACKEND" = "pyinstaller" ]; then
  "$VENV_PYTHON" -m pip "${PIP_ARGS[@]}" pyinstaller
else
  "$VENV_PYTHON" -m pip "${PIP_ARGS[@]}" nuitka zstandard
fi

REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENTRY_POINT="$REPO_ROOT/apps/launcher/__main__.py"
APP_NAME="Start-macOS"

if [ "$BACKEND" = "pyinstaller" ]; then
  "$VENV_PYTHON" -m PyInstaller \
    --clean \
    --noconfirm \
    --name "$APP_NAME" \
    --onedir \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_ROOT/build" \
    --specpath "$SPEC_DIR" \
    --hidden-import "apps.launcher" \
    --collect-submodules "apps.launcher" \
    "$ENTRY_POINT"
  APP_DIR="$DIST_DIR/$APP_NAME/$APP_NAME.app"
else
  "$VENV_PYTHON" -m nuitka \
    --standalone \
    --onefile \
    --macos-create-app-bundle \
    --output-dir "$DIST_DIR" \
    --include-package=apps.launcher \
    "$ENTRY_POINT"
  APP_DIR="$DIST_DIR/$APP_NAME.app"
fi

if [ ! -d "$APP_DIR" ]; then
  echo "Build failed: missing $APP_NAME.app" >&2
  exit 1
fi

rsync -a "$APP_DIR" "$STICK_ROOT/Start-macOS.app"

for folder in Docs Samples; do
  if [ -d "$REPO_ROOT/$folder" ]; then
    rsync -a "$REPO_ROOT/$folder" "$STICK_ROOT/$folder"
  fi
done

APP_SOURCE="$REPO_ROOT/App"
if [ ! -d "$APP_SOURCE" ]; then
  echo "Missing App/ directory at $APP_SOURCE" >&2
  exit 1
fi
rsync -a "$APP_SOURCE" "$STICK_ROOT/App"

echo "Packaging complete. Output written to $STICK_ROOT"
