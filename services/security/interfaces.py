"""Security service interfaces covering PIN, encryption, lockouts, and logging."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol

PIN_LENGTH = 6
RECOVERY_WORD_COUNT = 12


@dataclass(frozen=True)
class LockoutState:
    attempts: int
    locked_until: datetime | None
    requires_replug: bool = False

    @property
    def is_locked(self) -> bool:
        return self.locked_until is not None and self.locked_until > datetime.now()


class TimeProvider(Protocol):
    def now(self) -> datetime:
        """Return current UTC timestamp for deterministic lockout math."""


class KeyVault(Protocol):
    def unlock(self, pin: str) -> bool:
        """Attempt PIN unwrap of master key material."""

    def rewrap(self, new_pin: str) -> None:
        """Rotate wrapping key after PIN change or recovery reset."""

    def lock(self) -> None:
        """Erase decrypted keys from memory."""


class RecoveryStore(Protocol):
    def verify_phrase(self, words: list[str]) -> bool:
        """Validate 12-word recovery phrase."""

    def rotate_phrase(self) -> list[str]:
        """Generate and persist a new recovery phrase securely."""


class EncryptedFilesystem(Protocol):
    def mount(self) -> Path:
        """Mount encrypted Data/ volume read/write for application only."""

    def wipe_temporary(self) -> None:
        """Securely delete transient files then recreate directories."""


class IntegrityLogger(Protocol):
    def append(self, message: str) -> None:
        """Write human-readable log entry."""

    def add_hash_note(self, digest: str) -> None:
        """Attach rolling hash of log contents for tamper evidence."""

    def clear(self) -> None:
        """Erase logs after confirmation."""


def unlock_with_pin(pin: str, vault: KeyVault, lockouts: LockoutState) -> bool:
    """Return True when provided 6-digit PIN opens the key vault."""
    # Pseudocode:
    # - Validate len(pin) == PIN_LENGTH and pin.isdigit().
    # - If lockouts.is_locked: deny.
    # - Call vault.unlock(pin); on success reset attempt counter and return True.
    # - On failure increment attempts via failed_attempt() helper.
    raise NotImplementedError


def change_pin(current: str, new: str, confirm: str, vault: KeyVault) -> bool:
    """Change PIN after verifying current PIN and matching confirmation."""
    # Pseudocode:
    # - Ensure new and confirm match and satisfy length/digit rules.
    # - unlock_with_pin(current,...); if success call vault.rewrap(new).
    # - Return True on completion; otherwise False.
    raise NotImplementedError


def reset_with_recovery(words: list[str], store: RecoveryStore, vault: KeyVault) -> bool:
    """Rewrap master key using recovery phrase flow."""
    # Pseudocode:
    # - Ensure len(words) == RECOVERY_WORD_COUNT.
    # - store.verify_phrase(words); if fail abort.
    # - Prompt user for new PIN twice; call vault.rewrap(new_pin).
    # - Rotate recovery phrase via store.rotate_phrase().
    raise NotImplementedError


def failed_attempt(state: LockoutState, clock: TimeProvider) -> LockoutState:
    """Return updated lockout state based on attempt thresholds."""
    # Pseudocode:
    # - Increment attempts.
    # - If attempts == 5: set locked_until = now + 15 minutes.
    # - If attempts >= 10: set requires_replug = True and locked_until = None.
    # - Otherwise keep unlocked.
    raise NotImplementedError


def wipe_temps(fs: EncryptedFilesystem) -> None:
    """Clear temporary artifacts inside encrypted volume only."""
    # Pseudocode:
    # - fs.wipe_temporary() and ensure host read-only path untouched.
    raise NotImplementedError


def clear_logs(logger: IntegrityLogger) -> None:
    """Single control to clear logs after user confirmation."""
    # Pseudocode:
    # - Confirm user intent (UI layer) then logger.clear(); append hash note of empty state.
    raise NotImplementedError


PANIC_PHRASE = "panic"


def handle_voice_panic(command: str, fs: EncryptedFilesystem, vault: KeyVault) -> None:
    """Respond to voice command by wiping temps and locking vault."""
    # Pseudocode:
    # - Compare normalized command to PANIC_PHRASE.
    # - fs.wipe_temporary(); vault.lock(); trigger application exit.
    raise NotImplementedError
