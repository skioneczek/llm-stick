"""Preflight enforcement wiring for launcher runtime."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from services.preflight.interfaces import (
    AuditLogger,
    AuditResult,
    AdapterInspector,
    NetworkEnforcer,
    PrivilegeReducer,
    SecurityMode,
    TempManager,
    HARDENED_AUDIT,
    PARANOID_BLOCK_AUDIT,
    PARANOID_PASS_AUDIT,
    STANDARD_AUDIT,
)


class EnforcementError(RuntimeError):
    """Raised when preflight enforcement cannot proceed."""


@dataclass
class PreflightDeps:
    inspector: AdapterInspector
    network: NetworkEnforcer
    privileges: PrivilegeReducer
    temps: TempManager
    audit: AuditLogger


class PreflightController:
    def __init__(self, deps: PreflightDeps) -> None:
        self._deps = deps

    def enforce(self, mode: SecurityMode) -> AuditResult:
        deps = self._deps
        deps.temps.purge()
        deps.network.deny_outbound()

        if mode in (SecurityMode.HARDENED, SecurityMode.PARANOID):
            deps.network.disable_dns()
        if mode is SecurityMode.HARDENED:
            deps.privileges.drop_excess()

        adapters = deps.inspector.list_active()
        if mode is SecurityMode.PARANOID and adapters:
            result = AuditResult(mode=mode, passed=False, message=PARANOID_BLOCK_AUDIT)
            deps.audit.emit(result)
            return result

        self_test_ok = deps.network.self_test()
        if not self_test_ok:
            base = self._message_for(mode, bool(adapters))
            message = f"{base} Network self-test failed; refusing to continue."
            result = AuditResult(mode=mode, passed=False, message=message)
            deps.audit.emit(result)
            return result

        message = self._message_for(mode, bool(adapters))
        result = AuditResult(mode=mode, passed=True, message=message)
        deps.audit.emit(result)
        return result

    @staticmethod
    def _message_for(mode: SecurityMode, adapters_present: bool) -> str:
        if mode is SecurityMode.STANDARD:
            return STANDARD_AUDIT
        if mode is SecurityMode.HARDENED:
            return HARDENED_AUDIT
        return PARANOID_PASS_AUDIT if not adapters_present else PARANOID_BLOCK_AUDIT
