"""Preflight mode enforcement interfaces and pseudocode stubs."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol


class SecurityMode(str, Enum):
    STANDARD = "standard"
    HARDENED = "hardened"
    PARANOID = "paranoid"


@dataclass(frozen=True)
class AuditResult:
    mode: SecurityMode
    passed: bool
    message: str


class AdapterInspector(Protocol):
    def list_active(self) -> list[str]:
        """Return interface names that are currently active/connected."""


class NetworkEnforcer(Protocol):
    def deny_outbound(self) -> None:
        """Install process-scoped outbound socket deny rules."""

    def disable_dns(self) -> None:
        """Disable DNS resolution (noop under STANDARD)."""

    def self_test(self) -> bool:
        """Attempt outbound connection to confirm denial; return True on success."""


class PrivilegeReducer(Protocol):
    def drop_excess(self) -> None:
        """Apply least-privilege adjustments (token filtering, seccomp, etc.)."""


class TempManager(Protocol):
    def purge(self) -> None:
        """Delete and recreate temporary working directories."""


class AuditLogger(Protocol):
    def emit(self, result: AuditResult) -> None:
        """Persist the 1–2 line audit message locally."""


STANDARD_AUDIT = (
    "Mode: Standard — Outbound sockets blocked; DNS blocked; adapters detected; proceeding."
)
HARDENED_AUDIT = (
    "Mode: Hardened — Outbound+DNS blocked; limited privileges; adapters detected; proceeding."
)
PARANOID_BLOCK_AUDIT = (
    "Mode: Paranoid — Adapters detected; please disable Wi-Fi/unplug Ethernet."
)
PARANOID_PASS_AUDIT = (
    "Mode: Paranoid — No adapters detected; sandbox active; proceeding."
)


def enforce_mode(
    mode: SecurityMode,
    inspector: AdapterInspector,
    network: NetworkEnforcer,
    privileges: PrivilegeReducer,
    temps: TempManager,
    audit: AuditLogger,
) -> AuditResult:
    """Pseudocode orchestrating preflight checks and generating audits."""
    # Pseudocode outline:
    # 1. temps.purge() to ensure clean workspace.
    # 2. network.deny_outbound(); if failure, fall back to internal socket interception.
    # 3. if mode is HARDENED or PARANOID: network.disable_dns().
    # 4. if mode is HARDENED: privileges.drop_excess().
    # 5. if mode is PARANOID: assert inspector.list_active() is empty, else abort.
    # 6. run network.self_test(); if it fails, mark AuditResult.passed = False.
    # 7. Select appropriate audit string above; adjust wording when adapters absent/present.
    # 8. audit.emit(result) and return it.
    raise NotImplementedError


def bind_host_path(readonly_root: Path) -> Path:
    """Return the validated read-only host folder path."""
    # Pseudocode:
    # - resolve readonly_root, verify it matches policy location.
    # - assert filesystem permissions are read-only from process perspective.
    # - return an alias path the app will use for scanning only.
    raise NotImplementedError


def ready_signal(voice_mode_on: bool) -> None:
    """Notify UI stack that preflight checks passed and voice toggle honored."""
    # Pseudocode:
    # - ensure voice_mode_on defaults to False unless user opted in.
    # - trigger UI large-text view and optional voice annunciation.
    # - no return value.
    raise NotImplementedError
