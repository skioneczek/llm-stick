"""Console launcher wiring for development and packaging."""
from __future__ import annotations

import getpass
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from services.security.interfaces import LockoutState

from .core import (
    LauncherApp,
    LauncherPaths,
    default_ui_runner,
    persist_mode_to_file,
    read_mode_from_file,
)
from .host_binding import HostBindingManager, HostPolicy
from .pinpad import KeyVault, LockoutManager, PinPad, PinPrompt
from .preflight import PreflightController, PreflightDeps
from .storage import SecureConfig
from .voice import VoiceAnnouncer, VoiceDeps
from .watcher import FileWatcher, WatchPrompt

logger = logging.getLogger(__name__)


DEFAULT_PIN = "123456"
AUDIT_LOG_FILENAME = "audits.log"


class SimpleKeyVault(KeyVault):
    def __init__(self, config: SecureConfig) -> None:
        self._config = config
        self._ensure_default_pin()

    def _ensure_default_pin(self) -> None:
        record = self._config.read("pin_hash", DEFAULT_PIN)
        if record:
            return
        self._config.write("pin_hash", DEFAULT_PIN, {"hash": DEFAULT_PIN})

    def unlock(self, pin: str) -> bool:
        record = self._config.read("pin_hash", pin)
        if not record:
            return False
        return record.get("hash") == pin

    def lock(self) -> None:  # pragma: no cover - compatibility shim
        pass


class SimpleLockoutManager(LockoutManager):
    def __init__(self) -> None:
        self._state = LockoutState(attempts=0, locked_until=None, requires_replug=False)

    def current_state(self) -> LockoutState:
        return self._state

    def failed(self, state: LockoutState) -> LockoutState:
        attempts = state.attempts + 1
        locked_until: Optional[datetime] = state.locked_until
        requires_replug = state.requires_replug
        if attempts == 5:
            locked_until = datetime.now() + timedelta(minutes=15)
        elif attempts >= 10:
            locked_until = None
            requires_replug = True
        self._state = LockoutState(attempts=attempts, locked_until=locked_until, requires_replug=requires_replug)
        return self._state

    def reset(self) -> None:
        self._state = LockoutState(attempts=0, locked_until=None, requires_replug=False)


class ConsolePinPrompt(PinPrompt):
    def prompt(self) -> str:
        return getpass.getpass("Enter 6-digit PIN: ")

    def notify_failure(self, attempts: int) -> None:
        print(f"Incorrect PIN. Attempts: {attempts}")

    def notify_lockout(self, until: str | None) -> None:
        if until:
            print(f"PIN pad locked until {until}")
        else:
            print("PIN pad locked. Remove and reinsert device.")


class ConsoleHostPrompt:
    def choose_path(self) -> Path:
        value = input("Select read-only host folder path: ")
        return Path(value.strip())

    def notify_invalid(self, message: str) -> None:
        print(message)


class ConsoleWatchPrompt(WatchPrompt):
    def notify(self, pending: int) -> bool:
        answer = input(f"Found {pending} new files. Index now? [y/N] ")
        return answer.strip().lower() in {"y", "yes"}


class ConsoleAuditLogger:
    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, result) -> None:
        message = result.message
        print(message)
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{datetime.now().isoformat()} :: {message}\n")


class NoopAdapterInspector:
    def list_active(self) -> list[str]:
        return []


class MemoryNetworkEnforcer:
    def __init__(self) -> None:
        self._denied = False

    def deny_outbound(self) -> None:
        self._denied = True

    def disable_dns(self) -> None:
        pass

    def self_test(self) -> bool:
        return self._denied


class NoopPrivilegeReducer:
    def drop_excess(self) -> None:
        pass


class NoopTempManager:
    def purge(self) -> None:
        pass


class NoopVoiceSynthesizer:
    def announce_ready(self) -> None:
        print("Voice Mode: Ready.")


@dataclass
class LauncherRuntime:
    paths: LauncherPaths
    config: SecureConfig
    key_vault: SimpleKeyVault
    lockouts: SimpleLockoutManager
    host_binding: HostBindingManager
    watcher: FileWatcher
    voice: VoiceAnnouncer
    preflight: PreflightController
    audit_logger: ConsoleAuditLogger


def build_runtime(stick_root: Path) -> LauncherRuntime:
    paths = LauncherPaths.discover(stick_root)
    config = SecureConfig(paths.config_dir)
    key_vault = SimpleKeyVault(config)
    lockouts = SimpleLockoutManager()
    host_binding = HostBindingManager(config=config, prompt=ConsoleHostPrompt(), policy=HostPolicy())
    watcher = FileWatcher(prompt=ConsoleWatchPrompt())
    voice = VoiceAnnouncer(VoiceDeps(config=config, synthesizer=NoopVoiceSynthesizer()))
    audit_logger = ConsoleAuditLogger(paths.logs_dir / AUDIT_LOG_FILENAME)
    preflight = PreflightController(
        PreflightDeps(
            inspector=NoopAdapterInspector(),
            network=MemoryNetworkEnforcer(),
            privileges=NoopPrivilegeReducer(),
            temps=NoopTempManager(),
            audit=audit_logger,
        )
    )
    return LauncherRuntime(
        paths=paths,
        config=config,
        key_vault=key_vault,
        lockouts=lockouts,
        host_binding=host_binding,
        watcher=watcher,
        voice=voice,
        preflight=preflight,
        audit_logger=audit_logger,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s :: %(message)s")
    root_env = os.environ.get("LLM_STICK_ROOT")
    if root_env:
        stick_root = Path(root_env)
    else:
        stick_root = Path(__file__).resolve().parents[2]
    runtime = build_runtime(stick_root)

    pinpad = PinPad(
        vault=runtime.key_vault,
        lockouts=runtime.lockouts,
        prompt=ConsolePinPrompt(),
    )

    app = LauncherApp(
        paths=runtime.paths,
        pinpad=pinpad,
        preflight=runtime.preflight,
        host_binding=runtime.host_binding,
        watcher=runtime.watcher,
        voice=runtime.voice,
        ui_runner=default_ui_runner,
        mode_provider=lambda: read_mode_from_file(runtime.paths),
        mode_persist=lambda mode: persist_mode_to_file(runtime.paths, mode),
        audit_sink=runtime.audit_logger.emit,
    )

    app.launch()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
