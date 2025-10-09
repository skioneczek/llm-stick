"""Launcher core orchestration for the air-gapped LLM Stick."""
from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from services.preflight.interfaces import AuditResult, SecurityMode

from .host_binding import HostBindingManager
from .pinpad import PinContext, PinPad
from .preflight import PreflightController
from .voice import VoiceAnnouncer
from .watcher import FileWatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LauncherPaths:
    """Common directory structure expected on the stick."""

    stick_root: Path
    app_dir: Path
    data_dir: Path
    docs_dir: Path
    samples_dir: Path
    config_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "config_dir", self.data_dir / "config")
        object.__setattr__(self, "logs_dir", self.data_dir / "logs")

    @classmethod
    def discover(cls, start: Path) -> "LauncherPaths":
        root = start.resolve()
        app_dir = root / "App"
        if not app_dir.exists():
            dev_app_dir = root / "apps"
            if dev_app_dir.exists():
                app_dir = dev_app_dir
            else:
                raise FileNotFoundError(f"Unable to locate App/ or apps/ under {root}")

        data_dir = root / "Data"
        docs_dir = root / "Docs"
        samples_dir = root / "Samples"
        for path in (data_dir, docs_dir, samples_dir):
            path.mkdir(parents=True, exist_ok=True)
        return cls(root, app_dir, data_dir, docs_dir, samples_dir)


class LauncherApp:
    """High-level orchestrator used by Start-* entry points."""

    def __init__(
        self,
        paths: LauncherPaths,
        pinpad: PinPad,
        preflight: PreflightController,
        host_binding: HostBindingManager,
        watcher: FileWatcher,
        voice: VoiceAnnouncer,
        ui_runner: Callable[[Path, Path, bool], None],
        mode_provider: Callable[[], SecurityMode],
        mode_persist: Callable[[SecurityMode], None],
        audit_sink: Callable[[AuditResult], None],
    ) -> None:
        self.paths = paths
        self.pinpad = pinpad
        self.preflight = preflight
        self.host_binding = host_binding
        self.watcher = watcher
        self.voice = voice
        self.ui_runner = ui_runner
        self.mode_provider = mode_provider
        self.mode_persist = mode_persist
        self.audit_sink = audit_sink

    def launch(self) -> None:
        logger.info("Starting launcher flow from %s", self.paths.stick_root)
        pin_context = self.pinpad.obtain_pin()
        logger.debug("PIN accepted; mounting encrypted Data volume")

        host_path = self.host_binding.ensure_binding(pin_context)
        logger.info("Read-only host path bound: %s", host_path)

        active_mode = self.mode_provider()
        result = self._enforce_mode(active_mode)
        if not result.passed:
            raise RuntimeError(result.message)

        voice_enabled = self.voice.is_enabled(pin_context)
        self.voice.ready(pin_context, voice_enabled)

        ui_thread = threading.Thread(
            target=self.ui_runner,
            args=(self.paths.app_dir, host_path, voice_enabled),
            daemon=True,
            name="ui-runner",
        )
        ui_thread.start()

        self.watcher.begin(host_path)

        try:
            while ui_thread.is_alive():
                time.sleep(0.5)
        finally:
            self.watcher.stop()
            self.pinpad.lock()
            logger.info("Launcher flow terminated.")

    def toggle_mode(self, target: SecurityMode) -> AuditResult:
        logger.info("Mode toggle requested: %s", target.value)
        current_mode = self.mode_provider()
        result = self._enforce_mode(target)
        if result.passed:
            self.mode_persist(target)
        else:
            logger.info("Reverting to previous mode: %s", current_mode.value)
            revert_result = self._enforce_mode(current_mode)
            if revert_result.passed:
                self.mode_persist(current_mode)
        return result

    def _enforce_mode(self, mode: SecurityMode) -> AuditResult:
        result = self.preflight.enforce(mode)
        self.audit_sink(result)
        if not result.passed:
            logger.warning("Preflight enforcement failed: %s", result.message)
        return result


def default_ui_runner(app_dir: Path, host_path: Path, voice_enabled: bool) -> None:
    """Placeholder UI launcher for packaging smoke tests."""
    summary = {
        "app_dir": str(app_dir),
        "host_path": str(host_path),
        "voice_enabled": voice_enabled,
    }
    print("UI runner invoked:")
    print(json.dumps(summary, indent=2))
    # Real implementation would import the accessibility-first UI stack here.


def persist_mode_to_file(paths: LauncherPaths, mode: SecurityMode) -> None:
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    state_file = paths.config_dir / "security_mode.json"
    state_file.write_text(json.dumps({"mode": mode.value}), encoding="utf-8")


def read_mode_from_file(paths: LauncherPaths) -> SecurityMode:
    state_file = paths.config_dir / "security_mode.json"
    if not state_file.exists():
        return SecurityMode.STANDARD
    try:
        payload = json.loads(state_file.read_text(encoding="utf-8"))
        return SecurityMode(payload.get("mode", SecurityMode.STANDARD.value))
    except (ValueError, KeyError):
        return SecurityMode.STANDARD
