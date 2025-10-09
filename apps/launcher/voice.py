"""Voice mode helpers."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .pinpad import PinContext
from .storage import SecureConfig

logger = logging.getLogger(__name__)


class VoiceSynthesizer(Protocol):
    def announce_ready(self) -> None: ...


@dataclass
class VoiceDeps:
    config: SecureConfig
    synthesizer: VoiceSynthesizer | None = None


class VoiceAnnouncer:
    def __init__(self, deps: VoiceDeps) -> None:
        self._deps = deps

    def is_enabled(self, pin: PinContext) -> bool:
        payload = self._deps.config.read("voice_mode", pin.pin)
        if payload is None:
            return False
        return bool(payload.get("enabled", False))

    def ready(self, pin: PinContext, enabled: bool) -> None:
        self._deps.config.write("voice_mode", pin.pin, {"enabled": enabled})
        if not enabled:
            logger.info("Voice mode disabled; large-text UI only")
            return
        if not self._deps.synthesizer:
            logger.warning("Voice synthesizer unavailable; skipping announcement")
            return
        try:
            self._deps.synthesizer.announce_ready()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Voice announcement failed: %s", exc)
