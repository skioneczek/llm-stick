# apps/launcher/main.py
import sys
import os
import argparse
import json
import time
import subprocess
import threading
import webbrowser
import atexit
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

# Make package imports work when launched as a module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.preflight.mode_state import set_mode, Mode, set_adapters_active, set_guards_ok
from services.preflight.host_alias import bind_host_path
from services.preflight.adapter_detect import adapters_active
from services.preflight.audit import audit_voice  # reuse the existing voice audit line
from services.retriever import query as retriever
from services.indexer import build_index as index_builder
from services.indexer.source import (
    get_current_source,
    set_current_source,
    index_path_for_source,
    slug_for_source,
    stats_for_source,
)
from services.ingest import queue as ingest_queue
from services.ingest import registry as ingest_registry
from services.security import net_guard, logs as security_logs, sandbox_check, source_guard
from services.security.crypto_provider import get_provider
from services.security.pin_gate import (
    unlock_with_pin,
    change_pin,
    reset_with_recovery,
    first_boot_phrase_if_any,
)
from services.voice import tts_stub, stt_stub


READER_PRESETS = {
    "48pt-serif": "48pt serif, bold, high-contrast",
    "48pt-sans": "48pt sans, bold, high-contrast",
    "72pt-serif": "72pt serif, normal weight, white on black",
    "72pt-sans": "72pt sans, high-contrast yellow on black",
}

TEMP_DECRYPT_DIR = Path("Data/tmp/hotswap")
_URL_RE = re.compile(r"(http://127\.0\.0\.1:\d+)")
_UI_PROCESS: Optional[subprocess.Popen[str]] = None


def _resolve_index_path(index_override: str | None) -> Path:
    if index_override:
        return Path(index_override).expanduser().resolve()
    source = get_current_source()
    return index_path_for_source(source).resolve()


def _voice_single_turn(args, prompt: str | None = None, *, mode: Mode | None = None) -> None:
    """Run a single Ready → listen → answer → speak loop."""
    tts_stub.speak("Ready.")
    utterance = prompt if prompt is not None else stt_stub.listen()
    if not utterance:
        tts_stub.speak("No input captured.")
        return

    decrypted_path = None
    try:
        client_slug = getattr(args, "use_client", None)
        if client_slug:
            entry = ingest_registry.get_client(client_slug)
            if not entry:
                msg = f"Client registry entry not found: {client_slug}"
                print(msg)
                tts_stub.speak("Client not found.")
                return
            try:
                index_path = _decrypt_index_if_needed(entry, mode)
                if str(index_path).startswith(str(TEMP_DECRYPT_DIR)):
                    decrypted_path = index_path
            except Exception as exc:
                print(f"Unable to prepare index: {exc}")
                tts_stub.speak("Index unavailable.")
                return
        else:
            index_path = _resolve_index_path(args.index)

        if not index_path.exists():
            print("Index not found; please build index for the selected folder.")
            tts_stub.speak("Index missing.")
            return

        index = retriever.load_index(index_path)
        hits = retriever.top_hits(index, utterance, k=8)
        answer, cites = retriever.extractive_answer(utterance, hits)
        print(answer)
        if cites:
            print()
        retriever._print_sources(cites)

        first_line = answer.splitlines()[0] if answer else "No answer available."
        tts_stub.speak(first_line)
    finally:
        if decrypted_path:
            _purge_decrypted_index(decrypted_path)


def _print_sandbox_if_hardened(mode: Mode | None, emit: bool = True) -> Dict[str, str] | None:
    if mode != Mode.HARDENED:
        return None
    ok, message = sandbox_check.verify_temp_sandbox()
    if emit:
        print(message)
    return {"ok": ok, "message": message}


def _set_source_and_reindex(
    path: str,
    *,
    force: bool,
    mode: Mode | None,
    emit: bool = True,
) -> dict:
    ok, audit_line = source_guard.validate_source(path, force=force)
    if emit:
        print(audit_line)
    if not ok:
        status = "confirm" if audit_line.startswith("Data source requires confirm") else "error"
        return {"status": status, "audit": audit_line}

    resolved = set_current_source(path)
    index_path = index_path_for_source(resolved)
    if emit:
        print(f"Rebuilding index for {resolved} → {index_path} ...")
    try:
        stats = index_builder.build_index(resolved, index_path)
    except Exception as exc:  # pragma: no cover - operational safeguard
        message = f"Index rebuild failed: {exc}"
        if emit:
            print(message)
        return {"status": "error", "audit": message}

    sandbox_result = _print_sandbox_if_hardened(mode, emit=emit)

    return {
        "status": "ok",
        "audit": audit_line,
        "sandbox": sandbox_result,
        "stats": stats,
        "index_path": str(index_path),
    }


def handle_set_source_from_ui(path: str, *, force: bool = False, mode: Mode = Mode.STANDARD) -> dict:
    """UI hook to reuse the CLI Set Source workflow."""
    return _set_source_and_reindex(path, force=force, mode=mode, emit=False)


def _apply_reader_preset(preset_id: str) -> str:
    descriptor = READER_PRESETS.get(preset_id.lower())
    if descriptor is None:
        return f"Reader preset not recognized: {preset_id}"
    return f"Reader preset applied: {preset_id} — {descriptor}"


def handle_reader_preset(preset_id: str) -> str:
    """UI hook for reader preset toggles."""
    return _apply_reader_preset(preset_id)


def _run_ingest_pipeline(
    source_path: Path,
    *,
    storage_mode: str,
    client_slug: str,
    counts: Dict[str, int],
    crypto_provider: str | None = None,
) -> Dict[str, object]:
    resolved = Path(source_path).expanduser().resolve()
    storage_mode = storage_mode.upper()
    slug = slug_for_source(resolved)

    if storage_mode == "HOST_LOCAL":
        index_path = index_path_for_source(resolved)
        stats = index_builder.build_index(resolved, index_path)
        crypto_audit = None
    elif storage_mode == "STICK_ENCRYPTED":
        dest_root = Path("Data/ingested") / slug
        dest_root.mkdir(parents=True, exist_ok=True)
        temp_index = dest_root / "index.json"
        stats = index_builder.build_index(resolved, temp_index)
        provider = get_provider(crypto_provider)
        encrypted_path = dest_root / "index.enc"
        ok, audit_line = provider.encrypt_file(temp_index, encrypted_path)
        crypto_audit = audit_line
        temp_index.unlink(missing_ok=True)
        if not ok:
            raise RuntimeError(audit_line)
        index_path = encrypted_path
    else:
        raise ValueError(f"Unsupported storage mode {storage_mode}")

    entry = {
        "client_slug": client_slug,
        "source": str(resolved),
        "storage_mode": storage_mode,
        "index_path": str(index_path),
        "files": stats.get("files", counts.get("files", 0)),
        "chunks": stats.get("chunks", counts.get("chunks", 0)),
        "size_bytes": stats.get("size_bytes", counts.get("size_bytes", 0)),
        "slug": slug,
        "updated_at": int(time.time()),
        "ocr_available": False,
        "crypto_provider": crypto_provider or "none",
    }
    if crypto_audit:
        entry["crypto_audit"] = crypto_audit

    ingest_registry.register_client(client_slug, entry)
    return entry


def _print_registry_table(entries: Dict[str, Dict]) -> None:
    if not entries:
        print("No clients registered.")
        return
    headers = ["Slug", "Storage", "Last Indexed", "Size (MB)", "Index Path"]
    print(" | ".join(headers))
    print("-" * 80)
    for slug, meta in entries.items():
        storage = meta.get("storage_mode", "?")
        last = meta.get("updated_at", 0)
        size_mb = (meta.get("size_bytes", 0) or 0) / (1024 * 1024)
        index_path = meta.get("index_path", "-")
        print(f"{slug} | {storage} | {last} | {size_mb:.1f} | {index_path}")


def _decrypt_index_if_needed(entry: Dict, mode: Mode | None, emit: bool = True) -> Path:
    index_path = Path(entry.get("index_path", "")).expanduser()
    storage_mode = entry.get("storage_mode", "HOST_LOCAL").upper()
    if index_path.suffix != ".enc":
        return index_path

    if mode != Mode.HARDENED:
        raise RuntimeError("Encrypted index can only be used in Hardened mode.")

    provider = get_provider(entry.get("crypto_provider"))
    slug = entry.get("slug", "tmp")
    TEMP_DECRYPT_DIR.mkdir(parents=True, exist_ok=True)
    temp_out = TEMP_DECRYPT_DIR / f"{slug}_index.json"
    ok, audit = provider.decrypt_file(index_path, temp_out)
    if emit:
        print(audit)
    if not ok:
        raise RuntimeError(audit)
    return temp_out


def _purge_decrypted_index(path: Path) -> None:
    if path and path.exists() and path.is_file():
        try:
            path.unlink()
        except OSError:
            pass


def _drain_process_output(proc: subprocess.Popen[str], prefix: str = "[webui]") -> None:
    if not proc.stdout:
        return

    def _pump() -> None:
        assert proc.stdout is not None  # mypy guard
        for line in proc.stdout:
            print(f"{prefix} {line.rstrip()}")

    threading.Thread(target=_pump, name="webui-stdout", daemon=True).start()


def _launch_ui_server(view: str) -> Tuple[subprocess.Popen[str], str]:
    cmd = [sys.executable, "-m", "apps.webui.server", "--view", view]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    url = "http://127.0.0.1"
    if proc.stdout:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            stripped = line.rstrip()
            print(f"[webui] {stripped}")
            match = _URL_RE.search(stripped)
            if match:
                url = match.group(1)
                break
        if proc.poll() is not None and proc.returncode not in (0, None):
            raise RuntimeError("Web UI server exited during startup.")
        _drain_process_output(proc)

    return proc, url


def _register_ui_cleanup(proc: subprocess.Popen[str]) -> None:
    def _cleanup() -> None:
        if proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass

    atexit.register(_cleanup)


def _run_ui_loop(view: str) -> None:
    ok, audit = net_guard.allow_loopback_only()
    print(audit)
    if not ok:
        return

    try:
        proc, url = _launch_ui_server(view)
    except FileNotFoundError as exc:
        print(f"Failed to launch web UI server: {exc}")
        return
    except RuntimeError as exc:
        print(str(exc))
        return

    global _UI_PROCESS
    _UI_PROCESS = proc
    _register_ui_cleanup(proc)

    print(f"Loopback Web UI available at {url}")
    try:
        webbrowser.open(url)
    except webbrowser.Error as exc:
        print(f"Browser launch failed: {exc}")

    print("Press Ctrl+C to stop the web UI server.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("Stopping web UI server...")
    finally:
        if proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass


def handle_ingest_from_ui(path: str, dest_mode: str, client_slug: str, *, mode: Mode = Mode.STANDARD) -> dict:
    ok, audit_line = source_guard.validate_source(path)
    if not ok:
        return {"status": "error", "audit": audit_line}
    files, size_bytes = stats_for_source(path)
    counts = {"files": files, "size_bytes": size_bytes}
    job_id = ingest_queue.enqueue_job(
        str(Path(path).expanduser()),
        "",
        client_slug,
        counts,
        storage_mode=dest_mode.upper(),
    )
    try:
        entry = _run_ingest_pipeline(
            Path(path),
            storage_mode=dest_mode,
            client_slug=client_slug,
            counts=counts,
        )
    except Exception as exc:
        return {"status": "error", "audit": str(exc), "job_id": job_id}
    result = {"status": "ok", "entry": entry, "counts": counts, "job_id": job_id}
    sandbox = _print_sandbox_if_hardened(mode, emit=False)
    if sandbox:
        result["sandbox"] = sandbox
    return result


def handle_hotswap_from_ui(client_slug: str, *, mode: Mode = Mode.STANDARD) -> dict:
    entry = ingest_registry.get_client(client_slug)
    if not entry:
        return {"status": "error", "audit": f"Client not found: {client_slug}"}
    decrypted = None
    try:
        if entry.get("storage_mode", "HOST_LOCAL").upper() == "STICK_ENCRYPTED":
            decrypted = _decrypt_index_if_needed(entry, mode, emit=False)
        resolved = set_current_source(entry.get("source"))
        sandbox = _print_sandbox_if_hardened(mode, emit=False)
        return {
            "status": "ok",
            "source": str(resolved),
            "sandbox": sandbox,
            "decrypted_index": str(decrypted) if decrypted else None,
        }
    except Exception as exc:
        return {"status": "error", "audit": str(exc)}
    finally:
        if decrypted:
            _purge_decrypted_index(Path(decrypted))


def boot(args):
    # 1) PIN unlock (uses persisted keystore + lockouts)
    pin_res = unlock_with_pin(args.pin)
    print(pin_res.message)
    if not pin_res.ok:
        return None

    # 2) Detect adapters and apply guards for the selected mode
    active = adapters_active()
    set_adapters_active(active)

    guards_ok = False
    mode = Mode(args.mode)
    if mode == Mode.STANDARD:
        guards_ok = net_guard.apply_standard_guards()
    elif mode == Mode.HARDENED:
        tmp_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Data", "tmp"))
        guards_ok = net_guard.apply_hardened_guards(tmp_root)
        ok, message = sandbox_check.verify_temp_sandbox()
        print(message)
        if not ok:
            guards_ok = False
    elif mode == Mode.PARANOID:
        # In Paranoid we rely on adapters being OFF; we don't patch sockets here.
        guards_ok = True
    set_guards_ok(guards_ok)

    # 3) Mode audit (prints the 1–2 line message and commits mode if ok)
    print(set_mode(mode).msg)

    # 4) Host alias (policy: read-only)
    print(bind_host_path().msg)

    # 5) Voice audit line (toggle state only; actual TTS/STT is stubbed elsewhere)
    print(audit_voice(args.voice).msg)

    # 6) Optional inline probe (only meaningful in Standard/Hardened)
    if args.probe and mode in (Mode.STANDARD, Mode.HARDENED):
        dns_line, sock_line = net_guard.probe_text()
        print(dns_line)
        print(sock_line)

    # 7) Optional Q&A against the local index (post-audit, inside guarded process)
    if args.ask and args.voice:
        _voice_single_turn(args, prompt=args.ask, mode=mode)
    elif args.ask:
        retriever.run(args.ask, index_path=args.index, use_client=args.use_client)
    elif args.voice:
        _voice_single_turn(args, mode=mode)

    return mode


def main() -> None:
    ap = argparse.ArgumentParser(description="LLM Stick launcher (offline, guarded)")
    ap.add_argument("--mode", default="standard", choices=["standard", "hardened", "paranoid"])
    ap.add_argument("--pin", default="123456", help="6-digit PIN")
    ap.add_argument("--voice", action="store_true", help="Enable Voice Mode")
    ap.add_argument("--probe", action="store_true", help="Inline DNS/socket probe after guards")
    ap.add_argument("--ask", default=None, help="Ask a question against the local index")
    ap.add_argument(
        "--index",
        default=None,
        help="Override index path (defaults to the managed path for the active source)",
    )
    ap.add_argument("--clear-logs", action="store_true", help="Clear on-stick logs and exit")
    ap.add_argument("--panic", action="store_true", help="Wipe temp workspace and exit")
    ap.add_argument(
        "--set-source",
        metavar="PATH",
        default=None,
        help="Validate and store a read-only data source, then rebuild its index",
    )
    ap.add_argument(
        "--confirm-set-source",
        metavar="PATH",
        default=None,
        help="Confirm a warned Set Source selection and rebuild its index",
    )
    ap.add_argument(
        "--list-source",
        action="store_true",
        help="Print the currently selected data source and exit",
    )
    ap.add_argument(
        "--reader-preset",
        metavar="PRESET",
        default=None,
        help="Apply a reader preset (mirrors UI toggle)",
    )
    ap.add_argument(
        "--ui",
        metavar="MODE",
        choices=["standard", "enhanced"],
        default=None,
        help="Launch loopback web UI in the chosen mode",
    )
    ap.add_argument(
        "--ingest",
        metavar="PATH",
        default=None,
        help="Ingest a source folder for a client slug",
    )
    ap.add_argument(
        "--dest",
        metavar="MODE",
        default="HOST_LOCAL",
        help="Ingest storage mode (HOST_LOCAL or STICK_ENCRYPTED)",
    )
    ap.add_argument(
        "--client",
        metavar="SLUG",
        default=None,
        help="Client slug for ingest or hotswap",
    )
    ap.add_argument(
        "--hotswap",
        metavar="SLUG",
        default=None,
        help="Switch active source to the specified client slug",
    )
    ap.add_argument(
        "--list-clients",
        action="store_true",
        help="List registered ingest clients",
    )
    ap.add_argument(
        "--use-client",
        metavar="SLUG",
        default=None,
        help="Use the stored registry entry for retrieval",
    )

    # PIN lifecycle ops
    ap.add_argument("--change-pin", nargs=2, metavar=("CURRENT", "NEW"), help="Change PIN (6 digits)")
    ap.add_argument("--reset-pin", nargs=2, metavar=("PHRASE", "NEW"), help="Reset PIN using recovery phrase")
    ap.add_argument(
        "--show-first-boot-phrase",
        action="store_true",
        help="Print the generated recovery phrase if keys were just created",
    )

    args = ap.parse_args()
    selected_mode = Mode(args.mode)

    # First-boot key init (prints phrase only if keys were just created AND flag is set)
    phrase = first_boot_phrase_if_any()
    if args.show_first_boot_phrase:
        if phrase:
            print("\n*** WRITE THIS DOWN (store offline) ***")
            print(phrase)
            print("*** DO NOT LOSE THIS PHRASE ***\n")
        else:
            print("Recovery phrase already set (not shown). Keep your printed copy secure.")

    # Handle maintenance commands and exit early
    if args.clear_logs:
        print(security_logs.clear_logs())
        return
    if args.panic:
        print(security_logs.wipe_temps())
        return

    if args.list_source:
        current = get_current_source()
        index_file = index_path_for_source(current)
        print(f"Current data source: {current}")
        print(f"Managed index file: {index_file}")
        return
    if args.reader_preset:
        print(_apply_reader_preset(args.reader_preset))
        return

    if args.list_clients:
        _print_registry_table(ingest_registry.list_clients())
        return

    if args.ingest and not args.client:
        print("--ingest requires --client <slug>.")
        return

    if args.hotswap and not args.client:
        print("--hotswap requires --client <slug> (slug matches registry entry).")
        return

    if args.set_source and args.confirm_set_source:
        print("Provide either --set-source or --confirm-set-source, not both.")
        return

    if args.set_source:
        result = _set_source_and_reindex(args.set_source, force=False, mode=selected_mode)
        if result["status"] == "ok":
            print("Set Source completed.")
        elif result["status"] == "confirm":
            print(f"Re-run with --confirm-set-source \"{args.set_source}\" to proceed.")
        return

    if args.confirm_set_source:
        result = _set_source_and_reindex(args.confirm_set_source, force=True, mode=selected_mode)
        if result["status"] == "ok":
            print("Confirmed Set Source completed.")
        else:
            print(result["audit"])
        return

    if args.ingest:
        ingest_path = Path(args.ingest).expanduser()
        if not ingest_path.exists():
            print(f"Ingest source not found: {ingest_path}")
            return
        ok, audit_line = source_guard.validate_source(str(ingest_path))
        print(audit_line)
        if not ok:
            print("Ingest aborted.")
            return

        files, size_bytes = stats_for_source(ingest_path)
        counts = {"files": files, "size_bytes": size_bytes}
        job_id = ingest_queue.enqueue_job(
            str(ingest_path),
            "",
            args.client,
            counts,
            storage_mode=args.dest.upper(),
        )
        print(f"Ingest job queued: {job_id}")
        try:
            registry_entry = _run_ingest_pipeline(
                ingest_path,
                storage_mode=args.dest,
                client_slug=args.client,
                counts=counts,
            )
            print("Ingest completed.")
            print(json.dumps(registry_entry, indent=2))
        except Exception as exc:
            print(f"Ingest failed: {exc}")
        return
    if args.hotswap:
        entry = ingest_registry.get_client(args.hotswap)
        if not entry:
            print(f"Client not found in registry: {args.hotswap}")
            return
        decrypted = None
        if entry.get("storage_mode", "HOST_LOCAL").upper() == "STICK_ENCRYPTED":
            try:
                decrypted = _decrypt_index_if_needed(entry, selected_mode)
                print(f"Decrypted index staged at {decrypted}")
            except Exception as exc:
                print(f"Hotswap failed: {exc}")
                return
        resolved = set_current_source(entry.get("source"))
        print(f"Hotswap completed: {args.hotswap} → {resolved}")
        _print_sandbox_if_hardened(selected_mode)
        _purge_decrypted_index(Path(decrypted) if decrypted else None)
        return

    # Handle PIN change/reset commands and exit
    if args.change_pin:
        cur, new = args.change_pin
        res = change_pin(cur, new)
        print(res.message)
        return
    if args.reset_pin:
        phr, new = args.reset_pin
        res = reset_with_recovery(phr, new)
        print(res.message)
        return

    # Normal guarded boot
    boot_mode = boot(args)

    if args.ui:
        if boot_mode is None:
            return
        if boot_mode == Mode.PARANOID:
            print(net_guard.audit_ui_server_disabled())
            print("Use CLI mode in Paranoid.")
            return
        _run_ui_loop(args.ui)

if __name__ == "__main__":
    main()
