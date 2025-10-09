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

BUILD_ROOT="$SCRIPT_DIR/.build/linux"
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
APP_NAME="Start-Linux"

if [ "$BACKEND" = "pyinstaller" ]; then
  "$VENV_PYTHON" -m PyInstaller \
    --clean \
    --noconfirm \
    --name "$APP_NAME" \
    --onefile \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_ROOT/build" \
    --specpath "$SPEC_DIR" \
    --hidden-import "apps.launcher" \
    --collect-submodules "apps.launcher" \
    "$ENTRY_POINT"
  APP_IMAGE_SOURCE="$DIST_DIR/$APP_NAME"
else
  "$VENV_PYTHON" -m nuitka \
    --standalone \
    --onefile \
    --output-dir "$DIST_DIR" \
    --include-package=apps.launcher \
    "$ENTRY_POINT"
  APP_IMAGE_SOURCE="$DIST_DIR/$APP_NAME.bin"
fi

APPIMAGE_TOOL="$VENDOR_DIR/appimagetool/AppRun"
if [ ! -x "$APPIMAGE_TOOL" ]; then
  echo "Missing appimagetool at $APPIMAGE_TOOL" >&2
  exit 1
fi

APPDIR="$BUILD_ROOT/AppDir"
mkdir -p "$APPDIR/usr/bin"
cp "$APP_IMAGE_SOURCE" "$APPDIR/usr/bin/$APP_NAME"
cat > "$APPDIR/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Exec=$APP_NAME
Icon=llm-stick
Categories=Utility;
EOF

mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
if [ -f "$REPO_ROOT/App/icons/llm-stick.png" ]; then
  cp "$REPO_ROOT/App/icons/llm-stick.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/llm-stick.png"
fi

chmod +x "$APPDIR/usr/bin/$APP_NAME"

"$APPIMAGE_TOOL" "$APPDIR" "$DIST_DIR/$APP_NAME.AppImage"

if [ ! -f "$DIST_DIR/$APP_NAME.AppImage" ]; then
  echo "AppImage build failed" >&2
  exit 1
fi

cp "$DIST_DIR/$APP_NAME.AppImage" "$STICK_ROOT/Start-Linux.AppImage"
rsync -a "$REPO_ROOT/App" "$STICK_ROOT/App"
for folder in Docs Samples; do
  if [ -d "$REPO_ROOT/$folder" ]; then
    rsync -a "$REPO_ROOT/$folder" "$STICK_ROOT/$folder"
  fi
done

echo "Packaging complete. Output written to $STICK_ROOT"
