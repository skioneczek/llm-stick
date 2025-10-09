"""Validate dynamic data source selections within the read-only trust boundary."""
from __future__ import annotations

import os
from pathlib import Path, PurePath
from typing import Tuple

BYTES_PER_MB = 1024 * 1024

DEFAULT_ROOT = Path(os.environ.get("LLM_STICK_ALLOWED_SOURCE", "C:/OCRC_READONLY")).resolve()

VALIDATE_OK = "Data source validated: {path} ({files} files, size {size_mb:.1f} MB)."
VALIDATE_CONFIRM = "Data source requires confirm: {path} ({files} files, size {size_mb:.1f} MB)."
VALIDATE_FAIL = "Data source invalid: {reason}."


class SourceEscapeError(RuntimeError):
    """Raised when a symlink or junction escapes the approved root."""


def _resolve(path: str) -> Path:
    return Path(path).expanduser().resolve(strict=True)


def _norm(path: Path) -> PurePath:
    return PurePath(os.path.normcase(str(path)))


def _is_within_root(target: Path, root: Path) -> bool:
    try:
        _norm(target).relative_to(_norm(root))
        return True
    except ValueError:
        return False


def _scan_tree(resolved: Path, root: Path, max_files: int, max_bytes: int) -> tuple[int, int, bool]:
    total_files = 0
    total_bytes = 0

    for current_path, dirnames, filenames in os.walk(resolved, followlinks=False):
        current = Path(current_path)
        if not _is_within_root(current.resolve(), root):
            raise SourceEscapeError("symlink resolved outside allowed root")

        # Check directory symlinks/junctions before descending (os.walk will not follow them)
        for dirname in list(dirnames):
            child = current / dirname
            if child.is_symlink():
                target = child.resolve(strict=False)
                if not _is_within_root(target, root):
                    raise SourceEscapeError(f"symlink {child} escapes allowed root")

        for filename in filenames:
            candidate = current / filename
            try:
                if candidate.is_symlink():
                    target = candidate.resolve(strict=False)
                    if not _is_within_root(target, root):
                        raise SourceEscapeError(f"symlink {candidate} escapes allowed root")
                    stat_result = candidate.stat(follow_symlinks=False)
                else:
                    stat_result = candidate.stat(follow_symlinks=False)
            except OSError:
                continue

            total_files += 1
            total_bytes += stat_result.st_size

            if total_files > max_files or total_bytes > max_bytes:
                return total_files, total_bytes, True

    return total_files, total_bytes, False


def validate_source(path: str, allowed_root: Path | None = None, *, force: bool = False) -> Tuple[bool, str]:
    """Ensure the user-selected source stays inside the approved read-only root.

    Returns a tuple `(ok, audit_line)` where `ok` is False for both invalid selections
    and for selections that exceed soft caps (Integrator must re-run after confirmation).
    """

    root = (allowed_root or DEFAULT_ROOT).resolve()

    max_files_env = os.environ.get("LLM_STICK_SOURCE_MAX_FILES", "5000")
    max_mb_env = os.environ.get("LLM_STICK_SOURCE_MAX_MB", "1024")
    try:
        max_files = int(max_files_env)
    except ValueError:
        max_files = 5000
    try:
        max_bytes = int(float(max_mb_env) * BYTES_PER_MB)
    except ValueError:
        max_bytes = 1024 * BYTES_PER_MB

    try:
        resolved = _resolve(path)
    except FileNotFoundError:
        return False, VALIDATE_FAIL.format(reason="path does not exist")
    except (OSError, RuntimeError) as exc:
        return False, VALIDATE_FAIL.format(reason=f"unresolvable path ({exc})")

    if not resolved.exists():
        return False, VALIDATE_FAIL.format(reason="path does not exist")
    if not resolved.is_dir():
        return False, VALIDATE_FAIL.format(reason="selection is not a directory")
    if not _is_within_root(resolved, root):
        return False, VALIDATE_FAIL.format(reason=f"outside allowed root {root}")

    try:
        next(resolved.iterdir(), None)
    except PermissionError:
        return False, VALIDATE_FAIL.format(reason="read permission denied")
    except OSError as exc:
        return False, VALIDATE_FAIL.format(reason=f"filesystem error ({exc})")

    try:
        total_files, total_bytes, limit_hit = _scan_tree(resolved, root, max_files, max_bytes)
    except SourceEscapeError as exc:
        return False, VALIDATE_FAIL.format(reason=str(exc))

    size_mb = total_bytes / BYTES_PER_MB if total_bytes else 0.0

    if limit_hit and not force:
        return False, VALIDATE_CONFIRM.format(path=str(resolved), files=total_files, size_mb=size_mb)

    return True, VALIDATE_OK.format(path=str(resolved), files=total_files, size_mb=size_mb)
