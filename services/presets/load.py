from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any

PRESET_DIR = Path("Data/presets")
SYSTEM_PRESETS = PRESET_DIR / "system.json"
USER_PRESETS = PRESET_DIR / "user.json"


def _load_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"role": path.stem, "presets": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_system() -> Dict[str, Any]:
    return _load_file(SYSTEM_PRESETS)


def load_user() -> Dict[str, Any]:
    return _load_file(USER_PRESETS)


def load_all() -> List[Dict[str, Any]]:
    return [load_system(), load_user()]
