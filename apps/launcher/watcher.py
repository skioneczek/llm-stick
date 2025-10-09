"""Simple polling watcher for new host files."""
from __future__ import annotations

import threading
import time
from collections import deque
from pathlib import Path
from typing import Protocol


class WatchPrompt(Protocol):
    def notify(self, pending: int) -> bool:
        """Return True if user approves indexing after notification."""


class FileWatcher:
    def __init__(self, prompt: WatchPrompt, interval_seconds: float = 10.0) -> None:
        self._prompt = prompt
        self._interval = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._known: set[Path] = set()
        self._queue: deque[Path] = deque()

    def begin(self, host_root: Path) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(host_root,),
            name="host-watcher",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run(self, host_root: Path) -> None:
        self._scan_once(host_root)
        while not self._stop.wait(self._interval):
            self._scan_once(host_root)
            if self._queue:
                pending = len(self._queue)
                approved = self._prompt.notify(pending)
                if approved:
                    self._queue.clear()

    def _scan_once(self, root: Path) -> None:
        for entry in root.rglob("*"):
            if not entry.is_file():
                continue
            if entry in self._known:
                continue
            self._known.add(entry)
            self._queue.append(entry)
