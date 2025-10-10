# apps/webui/server_stdlib.py
from __future__ import annotations
import argparse, json, traceback, os
from pathlib import Path
from http import HTTPStatus
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs

# deps from our codebase
from services.threads import store, export as thread_export
from services.retriever import serve as retriever
from services.indexer.source import get_current_source, index_path_for_source
from apps.webui import pdf_engine

try:
    from services.ingest import registry as ingest_registry
except Exception:  # pragma: no cover - optional dependency
    ingest_registry = None

# --- Security headers (WSGI friendly) ---
_CSP = (
  "default-src 'none'; "
  "script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; font-src 'self'; "
  "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)
_SEC_HEADERS = [
  ("Content-Security-Policy", _CSP),
  ("X-Content-Type-Options", "nosniff"),
  ("X-Frame-Options", "DENY"),
  ("Referrer-Policy", "no-referrer"),
  ("Permissions-Policy", "geolocation=(), microphone=(), camera=()"),
]

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = (BASE_DIR / "templates").resolve()
STATIC_DIR = (BASE_DIR / "static").resolve()

_MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
}

def _with_sec(headers: list[tuple[str,str]] | None) -> list[tuple[str,str]]:
    base: list[tuple[str,str]] = []
    if headers:
        for k, v in headers:
            base.append((str(k), str(v)))
    base.extend(_SEC_HEADERS)
    return base

def _serve_file(path: Path):
    ext = path.suffix.lower()
    ct = _MIME.get(ext, "application/octet-stream")
    body = path.read_bytes()
    headers = [("Content-Type", ct), ("Cache-Control", "no-store")]
    return "200 OK", _with_sec(headers), body

def _read_registry() -> dict[str, object]:
    if ingest_registry and hasattr(ingest_registry, "load_registry"):
        try:
            data = ingest_registry.load_registry()
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    registry_path = Path("Data/ingested_registry.json")
    if registry_path.exists():
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8") or "{}")
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    return {}

def _read_json(environ) -> dict[str, object] | None:
    try:
        length = int(environ.get("CONTENT_LENGTH", "0") or 0)
    except Exception:
        length = 0
    if length < 0:
        length = 0
    body = environ["wsgi.input"].read(length) if length else b""
    if not body:
        return {}
    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def _json_response(
    payload: dict[str, object],
    *,
    status_code: int = 200,
    extra_headers: list[tuple[str, str]] | None = None,
):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers: list[tuple[str, str]] = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Cache-Control", "no-store"),
        ("Content-Length", str(len(body))),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    status_line = f"{status_code} {HTTPStatus(status_code).phrase}"
    return status_line, _with_sec(headers), body


def _ok_json(payload: dict[str, object], extra_headers: list[tuple[str, str]] | None = None):
    return _json_response(payload, status_code=200, extra_headers=extra_headers)


def _error_json(code: int, message: str):
    return _json_response({"error": message}, status_code=code)


def _ok_html(html: str, extra_headers: list[tuple[str, str]] | None = None):
    body = html.encode("utf-8")
    headers = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Cache-Control", "no-store"),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    return "200 OK", _with_sec(headers), body


def _no_content():
    return "204 No Content", _with_sec([( "Cache-Control", "no-store")]), b""


def _respond_json(
    start_response,
    status_code: int,
    payload: dict[str, object],
    extra_headers: list[tuple[str, str]] | None = None,
):
    status, headers, body = _json_response(payload, status_code=status_code, extra_headers=extra_headers)
    start_response(status, headers)
    return [body]


def app(environ, start_response):
    method = environ["REQUEST_METHOD"]
    path = (environ.get("PATH_INFO") or "/").rstrip("/") or "/"
    qs = parse_qs(environ.get("QUERY_STRING", ""))

    try:
        # health & favicon
        if method=="GET" and path=="/health":
            status, headers, body = _ok_json({"ok": True})
            start_response(status, headers); return [body]
        if method=="GET" and path=="/favicon.ico":
            status, headers, body = _no_content()
            start_response(status, headers); return [body]

        # home html shell
        if method=="GET" and path=="/":
            html_path = TEMPLATES_DIR / "threads.html"
            if not html_path.exists():
                start_response("500 Internal Server Error", _with_sec([("Content-Type","text/plain")]))
                return [b"Missing threads template"]
            status, headers, body = _serve_file(html_path)
            start_response(status, headers); return [body]

        # static assets
        if method=="GET" and path.startswith("/static/"):
            rel = path.split("/static/", 1)[1]
            target = (STATIC_DIR / rel).resolve()
            try:
                if not str(target).startswith(str(STATIC_DIR)) or not target.exists() or not target.is_file():
                    raise FileNotFoundError
                status, headers, body = _serve_file(target)
                start_response(status, headers); return [body]
            except FileNotFoundError:
                start_response("404 Not Found", _with_sec([( "Content-Type","text/plain")]))
                return [b""]

        # API: list/search threads
        if method=="GET" and path in ("/api/threads", "/threads"):
            q_raw = (qs.get("q", [""])[0] or "")
            results = store.search(q_raw, limit=0)
            threads = []
            for entry in results:
                thread = store.get_thread(entry.get("id")) if isinstance(entry, dict) else None
                threads.append(thread or entry)
            status, headers, body = _ok_json({"threads": threads})
            start_response(status, headers); return [body]

        # source info
        if method=="GET" and path in ("/api/sources", "/sources"):
            current = get_current_source()
            index_path = str(index_path_for_source(current)) if current else None
            registry = _read_registry()
            clients = sorted(registry.keys()) if isinstance(registry, dict) else []
            payload = {
                "active_source": str(current) if current else None,
                "managed_index": index_path,
                "clients": clients,
            }
            status, headers, body = _ok_json(payload)
            start_response(status, headers); return [body]

        # new thread
        if method=="POST" and path=="/threads":
            data = _read_json(environ)
            if data is None:
                status, headers, body = _error_json(400, "invalid json")
                start_response(status, headers); return [body]
            t = store.new_thread(
                data.get("title","Untitled"),
                data.get("client_slug"),
                data.get("source_slug"),
            )
            status, headers, body = _ok_json({"thread": t})
            start_response(status, headers); return [body]

        # append message + answer
        if method=="POST" and path.startswith("/threads/") and path.endswith("/messages"):
            parts = path.strip("/").split("/")
            if len(parts) != 3:
                return _respond_json(start_response, 404, {"error": "not found"})

            tid = parts[1]
            payload = _read_json(environ)
            if payload is None:
                return _respond_json(start_response, 400, {"error": "invalid json"})

            text = (payload.get("text") or payload.get("prompt") or "").strip()
            if not text:
                return _respond_json(start_response, 400, {"error": "empty prompt"})

            thread = store.get_thread(tid)
            if not thread:
                return _respond_json(start_response, 404, {"error": "thread not found"})

            user_msg = store.append_message(tid, "user", text, [])
            if user_msg is None:
                return _respond_json(start_response, 500, {"error": "failed to append message"})

            client_slug = thread.get("client_slug") if isinstance(thread, dict) else None
            source_path = thread.get("source_path") if isinstance(thread, dict) else None

            result = retriever.answer(
                text,
                client_slug=str(client_slug) if client_slug else None,
                source_path=str(source_path) if source_path else None,
            )
            answer_text = result.get("answer_text") or result.get("answer") or "Here's what I found."
            plan = (result.get("plan") or "Plan: review archives and ingest missing documents before answering.").strip()
            bullets = [b for b in (result.get("bullets") or []) if b]
            citations = result.get("sources") or []

            assistant_msg = store.append_message(
                tid,
                "assistant",
                answer_text,
                citations=citations,
                meta={"plan": plan},
            )
            if assistant_msg is None:
                return _respond_json(start_response, 500, {"error": "failed to append assistant message"})

            updated = store.get_thread(tid)
            return _respond_json(
                start_response,
                200,
                {
                    "thread": updated,
                    "reply": {
                        "text": answer_text,
                        "plan": plan,
                        "bullets": bullets,
                    },
                    "sources": citations,
                },
            )

        # archive
        if method=="POST" and path.startswith("/threads/") and path.endswith("/archive"):
            tid = path.split("/")[2]
            store.archive(tid)
            status, headers, body = _ok_json({"ok": True})
            start_response(status, headers); return [body]

        # search (optional q)
        if method=="GET" and path in ("/api/search", "/search"):
            q_raw = (qs.get("q", [""])[0] or "")
            results = store.search(q_raw)
            status, headers, body = _ok_json({"matches": results})
            start_response(status, headers); return [body]

        # placeholders for future UI → CLI bridges
        if method=="POST" and path in ("/set-source","/ingest","/hotswap","/preset","/sources"):
            status, headers, body = _ok_json({"queued": True})
            start_response(status, headers); return [body]

        # print (large-print)
        if method=="GET" and path.startswith("/_print/"):
            tid  = path.rsplit("/",1)[1]
            html = thread_export.render_thread_html(tid, {"font":"large"})
            status, headers, body = _ok_html(html, [("X-Action-Audit","Print invoked (local assets only)")])
            start_response(status, headers); return [body]

        # export pdf (auto-select engine)
        if method=="GET" and path.startswith("/export/pdf/"):
            tid  = path.rsplit("/",1)[1]
            html = thread_export.render_thread_html(tid, {"font":"standard"})
            pdf_bytes, audit_hdr, audit_detail = pdf_engine.render_pdf_bytes(html)
            if pdf_bytes:
                headers = [
                    ("Content-Type","application/pdf"),
                    ("Content-Disposition", f'attachment; filename="thread-{tid}.pdf"'),
                    ("X-Action-Audit", audit_hdr),
                    ("X-Engine-Detail", audit_detail),
                ]
                start_response("200 OK", _with_sec(headers))
                return [pdf_bytes]
            return _respond_json(
                start_response,
                200,
                {"fallback": "print-to-pdf", "thread_id": tid},
                extra_headers=[
                    ("X-Action-Audit", audit_hdr),
                    ("X-Engine-Detail", audit_detail),
                ],
            )

        # 404
        start_response("404 Not Found", _with_sec([( "Content-Type","text/plain")]))
        return [b""]

    except Exception:
        tb = traceback.format_exc().encode("utf-8")
        start_response("500 Internal Server Error", _with_sec([( "Content-Type","text/plain")]))
        return [tb]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--view", choices=["standard","enhanced"], default="standard")
    ap.add_argument("--ready-file", default=None)
    args = ap.parse_args()

    srv = make_server("127.0.0.1", args.port, app)
    url = f"http://127.0.0.1:{srv.server_port}"
    print("CSP applied (offline assets only).", flush=True)
    print(f"UI: {url} (view={args.view})", flush=True)

    if args.ready_file:
        os.makedirs(os.path.dirname(args.ready_file), exist_ok=True)
        with open(args.ready_file, "w", encoding="utf-8") as f:
            f.write(url)

    srv.serve_forever()

if __name__=="__main__":
    main()
