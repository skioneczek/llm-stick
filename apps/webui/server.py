"""Loopback-only web UI server for the LLM Stick."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import uuid
from http import HTTPStatus
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

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

try:  # optional PDF engine (offline bundle)
    from weasyprint import HTML as _WeasyHTML  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _WeasyHTML = None


APP_ROOT = Path(__file__).resolve().parent
STATIC_DIR = APP_ROOT / "static"
TEMPLATE_DIR = APP_ROOT / "templates"
TMP_DIR = Path("Data/tmp/webui")
TMP_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_LOOPBACK_READY = "UI server bound to 127.0.0.1 with CSP applied."
AUDIT_PRINT_LOCAL = "Print invoked (local assets only)."

PDF_ENGINE_SETTING = os.environ.get("PDF_ENGINE", "").strip().lower()
WKHTML_BIN = os.environ.get("WKHTMLTOPDF_BIN") or shutil.which("wkhtmltopdf")
PDF_ENGINE_NAME: Optional[str]
if PDF_ENGINE_SETTING == "wkhtml" and WKHTML_BIN:
    PDF_ENGINE_NAME = "wkhtml"
elif PDF_ENGINE_SETTING == "weasy" and _WeasyHTML is not None:
    PDF_ENGINE_NAME = "weasy"
else:
    PDF_ENGINE_NAME = None

if PDF_ENGINE_NAME == "weasy":
    AUDIT_PDF_ENGINE = "PDF export (engine weasyprint)"
elif PDF_ENGINE_NAME == "wkhtml":
    AUDIT_PDF_ENGINE = "PDF export (engine wkhtml)"
else:
    AUDIT_PDF_ENGINE = None

AUDIT_PDF_FALLBACK = "PDF export fallback (engine missing)"

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


_STREAMS: Dict[str, Dict[str, object]] = {}
_STREAM_LOCK = threading.Lock()


def _register_stream() -> str:
    sid = uuid.uuid4().hex
    with _STREAM_LOCK:
        _STREAMS[sid] = {"q": [], "done": False, "error": None, "meta": {}}
    return sid


def _update_stream(sid: str, key: str, value: object) -> None:
    with _STREAM_LOCK:
        if sid in _STREAMS:
            _STREAMS[sid][key] = value


def _append_stream_token(sid: str, token: str) -> None:
    with _STREAM_LOCK:
        entry = _STREAMS.get(sid)
        if entry is not None:
            entry.setdefault("q", []).append(token)


def _stream_response(sid: str) -> Iterable[str]:
    index = 0
    while True:
        with _STREAM_LOCK:
            state = dict(_STREAMS.get(sid) or {})
        if not state:
            yield "event: error\ndata: stream-missing\n\n"
            break

        queue = state.get("q", [])
        while index < len(queue):
            token = queue[index]
            index += 1
            yield f"data: {token}\n\n"

        if state.get("error"):
            yield f"event: error\ndata: {state['error']}\n\n"
            break

        if state.get("done"):
            meta = state.get("meta") or {}
            yield f"event: meta\ndata: {json.dumps(meta)}\n\n"
            yield "event: end\ndata: end\n\n"
            break

        time.sleep(0.05)

    with _STREAM_LOCK:
        _STREAMS.pop(sid, None)


def _launch_answer_thread(
    sid: str,
    thread: Dict[str, object],
    prompt: str,
    realtime: bool,
    source_override: Optional[str],
) -> None:
    def _runner() -> None:
        tokens: list[str] = []
        try:
            source_path = source_override or _thread_source_path(thread)

            def on_token(token: str) -> None:
                tokens.append(token)
                _append_stream_token(sid, token)

            result = retriever_service.answer_llm(
                prompt,
                source_path=source_path,
                realtime=realtime,
                stream_callback=on_token,
            )

            answer_text = result.get("answer") or "".join(tokens).strip()
            plan_text = result.get("plan") or ""
            citations = result.get("sources") or []

            thread_store.append_message(
                thread["id"],
                role="assistant",
                text=answer_text,
                citations=citations,
                meta={
                    "plan": plan_text,
                    "mode": result.get("mode"),
                    "source_path": result.get("source_path"),
                    "raw_output": result.get("raw_output"),
                },
            )

            _update_stream(
                sid,
                "meta",
                {
                    "sources": citations,
                    "plan": plan_text,
                    "thread_id": thread.get("id"),
                },
            )
            _update_stream(sid, "done", True)
        except Exception as exc:  # pragma: no cover - background safety
            _update_stream(sid, "error", str(exc))
            _update_stream(sid, "done", True)

    threading.Thread(target=_runner, daemon=True).start()


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

    thread_store.append_message(thread_id, role="user", text=prompt)
    result = retriever_service.answer_llm(
        prompt,
        source_path=source_path,
        realtime=bool(data.get("realtime")),
    )

    answer_text = (
        result.get("answer")
        or result.get("answer_text")
        or result.get("raw_output")
        or ""
    )
    plan_text = result.get("plan") or ""

    thread_store.append_message(
        thread_id,
        role="assistant",
        text=answer_text,
        citations=result.get("sources"),
        meta={
            "plan": plan_text,
            "mode": result.get("mode"),
            "source_path": result.get("source_path"),
        },
    )

    updated = thread_store.get_thread(thread_id)
    return flask.jsonify({"thread": updated})


@app.route("/api/ask", methods=["POST"])
def ask_stream() -> flask.Response:
    payload: Dict[str, object] = flask.request.get_json(force=False, silent=True) or {}
    prompt = str(payload.get("prompt") or "").strip()
    thread_id = str(payload.get("thread_id") or "").strip()
    realtime = bool(payload.get("realtime"))
    source_override = str(payload.get("source_path") or "").strip() or None
    if not prompt:
        return flask.jsonify({"error": "Prompt required"}), HTTPStatus.BAD_REQUEST
    if not thread_id:
        return flask.jsonify({"error": "thread_id required"}), HTTPStatus.BAD_REQUEST

    thread = thread_store.get_thread(thread_id)
    if not thread:
        return flask.jsonify({"error": "Thread not found"}), HTTPStatus.NOT_FOUND

    thread_store.append_message(
        thread_id,
        role="user",
        text=prompt,
        meta={"realtime": realtime, "source_path": source_override},
    )

    sid = _register_stream()
    _launch_answer_thread(sid, thread, prompt, realtime, source_override)

    response = {"sid": sid, "sse": f"/api/stream/{sid}"}
    return flask.jsonify(response), HTTPStatus.ACCEPTED


@app.route("/api/stream/<sid>", methods=["GET"])
def stream_tokens(sid: str) -> flask.Response:
    generator = flask.stream_with_context(_stream_response(sid))
    response = flask.Response(generator, mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


def _render_thread_html(thread: Dict[str, object], *, font: str = "large") -> str:
    return flask.render_template("print_thread.html", thread=thread, font=font)


def _generate_pdf_payload(html: str) -> tuple[Optional[bytes], Optional[str]]:
    if PDF_ENGINE_NAME == "weasy" and _WeasyHTML is not None:
        pdf = _WeasyHTML(string=html, base_url=str(STATIC_DIR)).write_pdf()  # type: ignore[arg-type]
        return pdf, AUDIT_PDF_ENGINE
    if PDF_ENGINE_NAME == "wkhtml" and WKHTML_BIN:
        with tempfile.TemporaryDirectory(prefix="webui-", dir=TMP_DIR) as tmpdir:
            html_path = Path(tmpdir) / "thread.html"
            pdf_path = Path(tmpdir) / "thread.pdf"
            html_path.write_text(html, encoding="utf-8")
            cmd = [WKHTML_BIN, "--quiet", str(html_path), str(pdf_path)]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (subprocess.CalledProcessError, OSError):
                return None, None
            return pdf_path.read_bytes(), AUDIT_PDF_ENGINE
    return None, None


@app.route("/print/<thread_id>")
@app.route("/_print/<thread_id>")
def print_thread(thread_id: str):
    thread = thread_store.get_thread(thread_id)
    if not thread:
        return flask.jsonify({"error": "Thread not found"}), HTTPStatus.NOT_FOUND
    html = _render_thread_html(thread, font="large")
    response = flask.make_response(html)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["X-Action-Audit"] = AUDIT_PRINT_LOCAL
    return response


@app.route("/export/pdf/<thread_id>")
@app.route("/threads/<thread_id>/pdf")
def export_pdf(thread_id: str):
    thread = thread_store.get_thread(thread_id)
    if not thread:
        return flask.jsonify({"error": "Thread not found"}), HTTPStatus.NOT_FOUND

    # inside your /export/pdf/<thread_id> route handler
    from apps.webui import pdf_engine
    html = render_thread_html(thread_id, {"font": "standard"})  # you already have this
    pdf_bytes, audit_hdr, audit_detail = pdf_engine.render_pdf_bytes(html)
    if pdf_bytes:
        resp = app.response_class(pdf_bytes, mimetype="application/pdf")
        resp.headers["Content-Disposition"] = f'attachment; filename="thread-{thread_id}.pdf"'
    else:
        # JSON fallback for UI toast
        resp = app.response_class('{"fallback":"print-to-pdf"}', mimetype="application/json")
    # audits
    resp.headers["X-Action-Audit"] = audit_hdr
    resp.headers["X-Engine-Detail"] = audit_detail
    return apply_secure_headers(resp)

    pdf_bytes, audit = _generate_pdf_payload(html)

    if pdf_bytes and audit:
        response = flask.Response(pdf_bytes, mimetype="application/pdf")
        response.headers["Content-Disposition"] = f'attachment; filename="thread-{thread_id}.pdf"'
        response.headers["X-Action-Audit"] = audit
        return response

    fallback = flask.jsonify({
        "fallback": "print-to-pdf",
        "engine": PDF_ENGINE_NAME or "none",
        "audit": AUDIT_PDF_FALLBACK,
    })
    fallback.headers["X-Action-Audit"] = AUDIT_PDF_FALLBACK
    return fallback


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


def _write_ready_file(path: str, url: str) -> None:
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(url)


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Loopback web UI server")
    parser.add_argument("--port", type=int, default=0, help="Port to bind (0 for random)")
    parser.add_argument("--view", choices=["standard", "enhanced"], default="standard")
    parser.add_argument("--ready-file", default=None)
    args = parser.parse_args(argv)

    addr, port = _bind_loopback(args.port)
    ok, audit = net_guard.allow_loopback_only()
    if not ok:
        print(audit)
        raise SystemExit(1)

    url = f"http://{addr}:{port}"
    print(f"UI: {url} (view={args.view})", flush=True)
    print(f"{AUDIT_LOOPBACK_READY} {url}")

    if args.ready_file:
        _write_ready_file(args.ready_file, url)

    app.config["VIEW_MODE"] = args.view
    app.run(host=addr, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
