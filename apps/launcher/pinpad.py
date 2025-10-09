"""PIN entry orchestration for the launcher."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from services.security.interfaces import PIN_LENGTH, LockoutState


@dataclass
class PinContext:
    pin: str


class KeyVault(Protocol):
    def unlock(self, pin: str) -> bool: ...

    def lock(self) -> None: ...


class LockoutManager(Protocol):
    def current_state(self) -> LockoutState: ...

    def failed(self, state: LockoutState) -> LockoutState: ...

    def reset(self) -> None: ...


class PinPrompt(Protocol):
    def prompt(self) -> str: ...

    def notify_failure(self, attempts: int) -> None: ...

    def notify_lockout(self, until: str | None) -> None: ...


class PinPad:
    def __init__(
        self,
        vault: KeyVault,
        lockouts: LockoutManager,
        prompt: PinPrompt,
    ) -> None:
        self._vault = vault
        self._lockouts = lockouts
        self._prompt = prompt

    def obtain_pin(self) -> PinContext:
        while True:
            state = self._lockouts.current_state()
            if state.is_locked:
                self._prompt.notify_lockout(state.locked_until.isoformat() if state.locked_until else None)
                continue
            candidate = self._prompt.prompt()
            if len(candidate) != PIN_LENGTH or not candidate.isdigit():
                self._prompt.notify_failure(state.attempts)
                continue
            if self._vault.unlock(candidate):
                self._lockouts.reset()
                return PinContext(candidate)
            new_state = self._lockouts.failed(state)
            if new_state.requires_replug:
                raise RuntimeError("Device locked. Please remove and reinsert the stick.")
            self._prompt.notify_failure(new_state.attempts)

    def lock(self) -> None:
        self._vault.lock()
