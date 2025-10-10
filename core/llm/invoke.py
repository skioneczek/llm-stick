"""Shared llama.cpp invocation helpers for offline execution."""
from __future__ import annotations

import datetime as _dt
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence
import subprocess

ROOT = Path(__file__).resolve().parent.parent.parent
TMP_DIR = ROOT / "Data" / "tmp" / "llm"
LOG_DIR = ROOT / "Data" / "logs"
LOG_PATH = LOG_DIR / "llm.log"

StdSink = Optional[Callable[[str], None]]


@dataclass
class InvokeResult:
    """Return payload for llama.cpp invocations."""

    returncode: int
    stdout: str
    stderr: str
    prompt_path: Path
    log_path: Path
    command: Sequence[str]


def _timestamp() -> str:
    return _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _stage_prompt(prompt: str, profile_name: str) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    safe_profile = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in profile_name)
    filename = f"{_dt.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{safe_profile or 'profile'}.txt"
    prompt_path = TMP_DIR / filename
    prompt_path.write_text(prompt, encoding="utf-8")
    return prompt_path


def invoke(
    command: Sequence[str],
    prompt: str,
    *,
    profile_name: str,
    env: Optional[dict[str, str]] = None,
    stream_callback: Optional[Callable[[str], None]] = None,
    stdout_sink: StdSink = None,
    stderr_sink: StdSink = None,
) -> InvokeResult:
    """Execute llama.cpp and tee output to audit logs and optional sinks."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    prompt_path = _stage_prompt(prompt, profile_name)

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    header = (
        f"[{_timestamp()}] profile={profile_name} command={' '.join(map(str, command))}\n"
        f"prompt_file={prompt_path.relative_to(ROOT)}\n"
    )

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    with LOG_PATH.open("a", encoding="utf-8") as log_handle:
        log_handle.write(header)
        log_handle.flush()

        process = subprocess.Popen(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=merged_env,
        )

        if process.stdout is None or process.stderr is None:
            raise RuntimeError("Failed to capture llama.cpp output streams")

        stdout_lock = threading.Lock()
        stderr_lock = threading.Lock()
        stop_event = threading.Event()

        def _emit_stdout(chunk: str) -> None:
            if not chunk:
                return
            stdout_chunks.append(chunk)
            if stream_callback:
                stream_callback(chunk)
            if stdout_sink:
                stdout_sink(chunk)
            with stdout_lock:
                log_handle.write(chunk)
                log_handle.flush()

        def _emit_stderr(chunk: str) -> None:
            if not chunk:
                return
            stderr_chunks.append(chunk)
            if stderr_sink:
                stderr_sink(chunk)
            with stderr_lock:
                log_handle.write(f"[stderr] {chunk}")
                log_handle.flush()

        def _drain_stdout() -> None:
            try:
                for chunk in iter(lambda: process.stdout.read(1), ""):
                    if stop_event.is_set():
                        break
                    _emit_stdout(chunk)
            finally:
                process.stdout.close()

        def _drain_stderr() -> None:
            try:
                for chunk in iter(lambda: process.stderr.read(1), ""):
                    if stop_event.is_set():
                        break
                    _emit_stderr(chunk)
            finally:
                process.stderr.close()

        stdout_thread = threading.Thread(target=_drain_stdout, daemon=True)
        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()

        returncode = 0
        try:
            returncode = process.wait()
        except KeyboardInterrupt:
            stop_event.set()
            process.terminate()
            returncode = process.wait()
        finally:
            stop_event.set()
            stdout_thread.join(timeout=1.0)
            stderr_thread.join(timeout=1.0)

        footer = f"[{_timestamp()}] returncode={returncode}\n"
        log_handle.write(footer)
        log_handle.flush()

    return InvokeResult(
        returncode=returncode,
        stdout="".join(stdout_chunks),
        stderr="".join(stderr_chunks),
        prompt_path=prompt_path,
        log_path=LOG_PATH,
        command=tuple(command),
    )
