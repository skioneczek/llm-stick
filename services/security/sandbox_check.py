"""Verify that hardened temp sandbox variables point into the stick."""
from __future__ import annotations

import os
from pathlib import Path

DATA_ROOT = Path("Data")
TMP_ROOT = DATA_ROOT / "tmp"
_ENV_KEYS = ("TMPDIR", "TMP", "TEMP")


def verify_temp_sandbox() -> tuple[bool, str]:
    """Confirm all temp env vars resolve inside `Data/tmp`.

    Returns (ok, message) matching the audit style used elsewhere.
    """
    expected = TMP_ROOT.resolve()
    missing = []
    wrong = []

    for key in _ENV_KEYS:
        value = os.environ.get(key)
        if value is None:
            missing.append(key)
            continue
        try:
            path = Path(value).resolve()
        except OSError:
            wrong.append(f"{key}={value} (unresolvable)")
            continue
        if not str(path).startswith(str(expected)):
            wrong.append(f"{key}→{path}")

    if missing:
        return False, f"Temp sandbox — failed; missing env vars: {', '.join(missing)}."
    if wrong:
        joined = "; ".join(wrong)
        return False, f"Temp sandbox — failed; reverting. Details: {joined}."

    return True, "Temp sandbox — verified (paths under Data/tmp)."
