#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STICK_ROOT="$(cd "$SCRIPT_DIR/../../" && pwd)"
export LLM_STICK_ROOT="$STICK_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
exec "$PYTHON_BIN" -m apps.launcher
