"""Host filesystem binding helpers."""
from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .pinpad import PinContext
from .storage import SecureConfig


class HostPathPrompt(Protocol):
    """UI hook used when the default read-only folder is missing."""

    def choose_path(self) -> Path: ...

    def notify_invalid(self, message: str) -> None: ...


@dataclass(frozen=True)
class HostPolicy:
    windows_default: Path = Path("C:/OCRC_READONLY/")
    unix_default: Path = Path("~/OCRC_READONLY/")

    def expected_root(self) -> Path:
        system = platform.system().lower()
        if system == "windows":
            return self.windows_default
        return self.unix_default


class HostBindingError(RuntimeError):
    """Raised when a valid host binding cannot be established."""


class HostBindingManager:
    def __init__(
        self,
        config: SecureConfig,
        prompt: HostPathPrompt,
        policy: HostPolicy | None = None,
    ) -> None:
        self._config = config
        self._prompt = prompt
        self._policy = policy or HostPolicy()

    def ensure_binding(self, pin: PinContext) -> Path:
        alias = self._config.read("host_alias", pin.pin)
        if alias:
            cached = Path(alias.get("path", ""))
            if self._is_valid_path(cached):
                return cached

        resolved_default = self._policy.expected_root().expanduser()
        if self._is_valid_path(resolved_default):
            self._persist(pin, resolved_default)
            return resolved_default

        # Prompt user once
        for _ in range(3):
            candidate = self._prompt.choose_path()
            if self._is_valid_path(candidate):
                self._persist(pin, candidate)
                return candidate
            self._prompt.notify_invalid(
                f"Path '{candidate}' is not a readable directory."
            )
        raise HostBindingError("Failed to bind a read-only host folder after multiple attempts.")

    def _persist(self, pin: PinContext, path: Path) -> None:
        payload = {"path": str(path.resolve())}
        self._config.write("host_alias", pin.pin, payload)

    @staticmethod
    def _is_valid_path(path: Path) -> bool:
        if not path:
            return False
        try:
            target = path.expanduser().resolve()
        except FileNotFoundError:
            return False
        if not target.exists() or not target.is_dir():
            return False
        if not os.access(target, os.R_OK):
            return False
        try:
            next(target.iterdir())
        except StopIteration:
            pass
        except PermissionError:
            return False
        return True
