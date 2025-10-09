"""Loopback-only web UI server for the LLM Stick."""

from __future__ import annotations

import argparse
import socket
from http import HTTPStatus
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    import flask
except ImportError as exc:  # pragma: no cover - operational safeguard
    raise SystemExit(
        "Flask is required for the loopback web UI. Bundle the wheel offline and install locally."
    ) from exc

from services.indexer.source import get_current_source, slug_for_source
from services.preflight.mode_state import Mode, get_mode
from services.retriever import serve as retriever_service
from services.security import net_guard
from services.security.http_guard import apply_secure_headers
from services.threads import store as thread_store
from services.ingest import registry as ingest_registry


APP_ROOT = Path(__file__).resolve().parent
STATIC_DIR = APP_ROOT / "static"
TEMPLATE_DIR = APP_ROOT / "templates"
AUDIT_LOOPBACK_READY = "UI server bound to 127.0.0.1 with CSP applied."

app = flask.Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    template_folder=str(TEMPLATE_DIR),
)
app.config.update(JSON_AS_ASCII=False)


@app.after_request
def _apply_headers(response: flask.Response) -> flask.Response:
    headers, audit = apply_secure_headers(response.headers)
    for key, value in headers.items():
        response.headers[key] = value
    response.headers.setdefault("X-Audit", audit)
    return response


def _resolve_view() -> str:
    return flask.request.args.get("view") or app.config.get("VIEW_MODE", "standard")


@app.route("/")
def home() -> flask.Response:
    thread_metas = thread_store.list_threads()
    threads = []
    for meta in thread_metas:
        if not isinstance(meta, dict):
            continue
        detail = thread_store.get_thread(meta.get("id", ""))
        threads.append(detail or meta)
    view = _resolve_view()
    show_cli_button = view == "standard"
    return flask.render_template(
        "threads.html",
        threads=threads,
        view=view,
        show_cli_button=show_cli_button,
    )


@app.route("/threads", methods=["POST"])
def create_thread() -> flask.Response:
    data: Dict[str, object] = flask.request.get_json(force=False, silent=True) or {}
    title = str(data.get("title") or "Untitled").strip()
    client_slug = str(data.get("client_slug") or "default").strip() or "default"
    source_path = str(data.get("source") or get_current_source())
    source_slug = slug_for_source(source_path)
    thread = thread_store.new_thread(
        title,
        client_slug,
        source_slug,
        source_path=source_path,
    )
    return flask.jsonify({"thread": thread}), HTTPStatus.CREATED


def _thread_source_path(thread: Dict[str, object]) -> Optional[str]:
    path = thread.get("source_path")
    if isinstance(path, str) and path:
        return path
    client_slug = thread.get("client_slug")
    if isinstance(client_slug, str) and client_slug:
        entry = ingest_registry.get_client(client_slug)
        if entry and entry.get("source"):
            return str(entry["source"])
    return None


@app.route("/threads/<thread_id>/messages", methods=["POST"])
def append_message(thread_id: str) -> flask.Response:
    data: Dict[str, object] = flask.request.get_json(force=False, silent=True) or {}
    prompt = str(data.get("prompt") or "").strip()
    if not prompt:
        return flask.jsonify({"error": "Prompt required"}), HTTPStatus.BAD_REQUEST

    thread = thread_store.get_thread(thread_id)
    if not thread:
        return flask.jsonify({"error": "Thread not found"}), HTTPStatus.NOT_FOUND

    client_slug = thread.get("client_slug")
    source_path = _thread_source_path(thread)

    result = retriever_service.answer(
        prompt,
        client_slug=str(client_slug) if isinstance(client_slug, str) else None,
        source_path=source_path,
    )

    thread_store.append_message(thread_id, role="user", text=prompt)

    plan = result.get("plan") or "Plan: review archives and ingest missing documents before answering."
    bullets = result.get("bullets") or []
    response_lines = [plan] + [f"- {line}" for line in bullets]

    thread_store.append_message(
        thread_id,
        role="assistant",
        text="\n".join(response_lines).strip(),
        citations=result.get("sources"),
        meta={"plan": plan},
    )

    updated = thread_store.get_thread(thread_id)
    return flask.jsonify({"thread": updated})


@app.route("/threads/<thread_id>/archive", methods=["POST"])
def archive_thread(thread_id: str) -> flask.Response:
    data: Dict[str, object] = flask.request.get_json(force=False, silent=True) or {}
    archive = bool(data.get("archive", True))
    updated = thread_store.archive_thread(thread_id, archive=archive)
    if not updated:
        return flask.jsonify({"error": "Thread not found"}), HTTPStatus.NOT_FOUND
    return flask.jsonify({"thread": updated})


@app.route("/search")
def search_threads() -> flask.Response:
    query = flask.request.args.get("q", "")
    matches = thread_store.search(query)
    return flask.jsonify({"matches": matches})


@app.route("/set-source", methods=["POST"])
def set_source_from_ui() -> flask.Response:
    data: Dict[str, object] = flask.request.get_json(force=False, silent=True) or {}
    path = data.get("path")
    force = bool(data.get("force", False))
    if not path:
        return flask.jsonify({"error": "path required"}), HTTPStatus.BAD_REQUEST

    from apps.launcher.main import _set_source_and_reindex

    mode = get_mode() or Mode.STANDARD
    result = _set_source_and_reindex(str(path), force=force, mode=mode, emit=False)
    status = HTTPStatus.OK if result.get("status") == "ok" else HTTPStatus.BAD_REQUEST
    return flask.jsonify(result), status


@app.route("/ingest", methods=["POST"])
def ingest() -> flask.Response:
    data: Dict[str, object] = flask.request.get_json(force=False, silent=True) or {}
    path = data.get("path")
    client_slug = data.get("client_slug")
    dest_mode = data.get("dest", "HOST_LOCAL")
    if not path or not client_slug:
        return flask.jsonify({"error": "path and client_slug required"}), HTTPStatus.BAD_REQUEST

    from apps.launcher.main import handle_ingest_from_ui

    mode = get_mode() or Mode.STANDARD
    result = handle_ingest_from_ui(str(path), str(dest_mode), str(client_slug), mode=mode)
    status = HTTPStatus.OK if result.get("status") == "ok" else HTTPStatus.BAD_REQUEST
    return flask.jsonify(result), status


@app.route("/hotswap", methods=["POST"])
def hotswap() -> flask.Response:
    data: Dict[str, object] = flask.request.get_json(force=False, silent=True) or {}
    client_slug = data.get("client_slug")
    if not client_slug:
        return flask.jsonify({"error": "client_slug required"}), HTTPStatus.BAD_REQUEST

    from apps.launcher.main import handle_hotswap_from_ui

    mode = get_mode() or Mode.STANDARD
    result = handle_hotswap_from_ui(str(client_slug), mode=mode)
    status = HTTPStatus.OK if result.get("status") == "ok" else HTTPStatus.BAD_REQUEST
    return flask.jsonify(result), status


@app.route("/preset", methods=["POST"])
def preset() -> flask.Response:
    data: Dict[str, object] = flask.request.get_json(force=False, silent=True) or {}
    preset_id = data.get("preset")
    if not preset_id:
        return flask.jsonify({"error": "preset required"}), HTTPStatus.BAD_REQUEST

    from apps.launcher.main import handle_reader_preset

    message = handle_reader_preset(str(preset_id))
    return flask.jsonify({"message": message})


@app.route("/sources")
def sources() -> flask.Response:
    current = get_current_source()
    slug = slug_for_source(current)
    return flask.jsonify({"source": str(current), "slug": slug})


def _bind_loopback(port: int = 0) -> Tuple[str, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", port))
    addr, bound_port = sock.getsockname()
    sock.close()
    return addr, bound_port


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Loopback web UI server")
    parser.add_argument("--port", type=int, default=0, help="Port to bind (0 for random)")
    parser.add_argument("--view", choices=["standard", "enhanced"], default="standard")
    args = parser.parse_args(argv)

    addr, port = _bind_loopback(args.port)
    ok, audit = net_guard.allow_loopback_only()
    if not ok:
        print(audit)
        raise SystemExit(1)
    print(f"{AUDIT_LOOPBACK_READY} http://{addr}:{port}")

    app.config["VIEW_MODE"] = args.view
    app.run(host=addr, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
