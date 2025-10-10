# apps/webui/server_stdlib.py
import json, time, uuid
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Iterable
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs

from services.security.http_guard import apply_secure_headers
from services.threads import store
from services.retriever import serve as rag
from services.threads.export import render_thread_html

ROOT = Path(__file__).parent.resolve()
STATIC = ROOT / "static"
TEMPL = ROOT / "templates"

# Simple in-memory SSE registry
_streams: Dict[str, Dict] = {}  # sid -> {"q": List[str], "done": bool, "err": Optional[str], "meta": dict}

def _hdr(content_type: str, extra: Optional[List[Tuple[str, str]]] = None) -> List[Tuple[str, str]]:
    merged = [("Content-Type", content_type)] + (extra or [])
    secured, _audit = apply_secure_headers(merged)
    if isinstance(secured, dict):
        return [(str(k), str(v)) for k, v in secured.items()]
    return [(str(k), str(v)) for k, v in secured]  # type: ignore[arg-type]

def _json(start_response, obj, status: str = "200 OK"):
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    headers = _hdr("application/json", [("Content-Length", str(len(body)))])
    start_response(status, headers)
    return [body]

def _ok(start_response, body: bytes, ctype="text/plain", status="200 OK"):
    start_response(status, _hdr(ctype))
    return [body]

def _notfound(start_response):
    start_response("404 Not Found", _hdr("text/plain"))
    return [b""]

def _error(start_response, msg: str):
    try:
        start_response("500 Internal Server Error", _hdr("text/plain"))
    except AssertionError:
        return []
    return [msg.encode("utf-8")]

def _read_json(env) -> dict:
    try:
        n = int(env.get("CONTENT_LENGTH") or 0)
        raw = (env["wsgi.input"].read(n) if n else b"").decode("utf-8")
        return json.loads(raw) if raw else {}
    except Exception:
        return {}

def _serve_file(start_response, path: Path, ctype="text/plain"):
    if not path.exists() or not path.is_file():
        return _notfound(start_response)
    return _ok(start_response, path.read_bytes(), ctype)

def _stream_iter(sid: str) -> Iterable[bytes]:
    """SSE generator. Sends raw tokens via `data: <tok>` lines,
    then one `event: meta` with sources, then `event: end`."""
    idx = 0
    while True:
        buf = _streams.get(sid)
        if not buf:
            yield b"event: error\ndata: stream-missing\n\n"
            break

        q = buf["q"]
        # flush new tokens
        while idx < len(q):
            tok = q[idx]
            idx += 1
            yield f"data: {tok}\n\n".encode("utf-8")

        if buf.get("err"):
            yield f"event: error\ndata: {buf['err']}\n\n".encode("utf-8")
            break

        if buf.get("done"):
            meta = buf.get("meta") or {}
            yield f"event: meta\ndata: {json.dumps(meta)}\n\n".encode("utf-8")
            yield b"event: end\ndata: end\n\n"
            break

        time.sleep(0.02)

def _launch_answer_thread(sid: str, prompt: str, realtime: bool, client_slug: Optional[str], source_path: Optional[str]):
    """Bridge `answer_llm` into our SSE queue. We use a callback for streaming tokens,
    collect them locally to persist as the assistant message at the end."""
    import threading
    def _runner():
        tokens: List[str] = []
        try:
            # Stream callback pushes into SSE queue and local buffer
            def on_token(tok: str):
                tokens.append(tok)
                _streams[sid]["q"].append(tok)

            # Contract: answer_llm supports stream_callback=, returns final dict with sources
            final = rag.answer_llm(
                prompt,
                source_slug=source_path,
                realtime=realtime,
                stream_callback=on_token
            ) or {}

            _streams[sid]["meta"] = {"sources": final.get("sources", [])}
            _streams[sid]["done"] = True

            # Persist assistant message with full text (best-effort)
            full = "".join(tokens).strip()
            if full:
                # Optional: attach sources in message meta if store supports it
                try:
                    store.append_message(final.get("thread_id") or "", role="assistant", content=full)
                except Exception:
                    pass
        except Exception as e:
            _streams[sid]["err"] = str(e)
    threading.Thread(target=_runner, daemon=True).start()

def _brand_info() -> dict:
    try:
        p = Path("Data/settings/branding.json")
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"productName": "Arteem", "owner": "Eric Martin", "org": "OCRC"}

def app(env, start_response):
    try:
        method = env.get("REQUEST_METHOD", "GET").upper()
        path = env.get("PATH_INFO") or "/"

        # Root page + static
        if path == "/":
            return _serve_file(start_response, TEMPL / "threads.html", "text/html")
        if path.startswith("/static/"):
            p = (STATIC / path[len("/static/"):]).resolve()
            if str(p).endswith(".css"): return _serve_file(start_response, p, "text/css")
            if str(p).endswith(".js"):  return _serve_file(start_response, p, "application/javascript")
            return _serve_file(start_response, p)

        # Branding + source banner
        if path == "/api/brand" and method == "GET":
            return _json(start_response, _brand_info())
        if path == "/api/sources" and method == "GET":
            from services.indexer.source import get_current_source
            src = get_current_source()
            return _json(start_response, {"current_source": str(src) if src else ""})

        # Threads JSON index
        if path == "/api/threads" and method == "GET":
            return _json(start_response, {"threads": store.list_threads()})

        # Create thread
        if path == "/threads" and method == "POST":
            data = _read_json(env)
            client_slug = data.get("client_slug") or "default"
            source_slug = data.get("source_slug") or client_slug
            thread = store.create_thread(
                title=(data.get("title") or "Untitled"),
                client_slug=client_slug,
                source_slug=source_slug,
                source_path=(data.get("source_path") or "")
            )
            return _json(start_response, {"thread": thread}, "201 Created")

        # Append user message
        if path.startswith("/threads/") and path.endswith("/messages") and method == "POST":
            tid = path.split("/")[2]
            data = _read_json(env)
            mid = store.append_message(tid, role="user", content=(data.get("content") or ""))
            return _json(start_response, {"ok": True, "message_id": mid})

        if path.startswith("/threads/") and path.endswith("/archive") and method == "POST":
            tid = path.split("/")[2]
            data = _read_json(env)
            archive_flag = data.get("archive") if isinstance(data, dict) else None
            should_archive = True if archive_flag is None else bool(archive_flag)
            store.archive_thread(tid, archive=should_archive)
            return _json(start_response, {"ok": True, "archived": should_archive})

        # Ask → start stream
        if path == "/api/ask" and method == "POST":
            data = _read_json(env)
            prompt = data.get("prompt") or ""
            realtime = bool(data.get("realtime"))
            client_slug = data.get("client_slug")  # reserved for future scoping
            source_path = data.get("source_path")
            sid = uuid.uuid4().hex
            _streams[sid] = {"q": [], "done": False, "err": None, "meta": {}}
            _launch_answer_thread(sid, prompt, realtime, client_slug, source_path)
            return _json(start_response, {"sid": sid, "sse": f"/stream?sid={sid}"})

        # SSE endpoint
        if path == "/stream" and method == "GET":
            qs = parse_qs(env.get("QUERY_STRING") or "")
            sid = (qs.get("sid", [""])[0])
            # Important: correct header shape; also disable proxy buffering
            headers = _hdr("text/event-stream", [
                ("Cache-Control", "no-cache"),
                ("X-Accel-Buffering", "no"),
            ])
            start_response("200 OK", headers)
            return _stream_iter(sid)

        # Print large text
        if path.startswith("/_print/") and method == "GET":
            tid = path.split("/")[-1]
            html = render_thread_html(tid, {"font": "large"})
            return _ok(start_response, html.encode("utf-8"), "text/html")

        # PDF fallback (no engine bundled yet)
        if path.startswith("/export/pdf/") and method == "GET":
            return _json(start_response, {"fallback": "print-to-pdf"})

        return _notfound(start_response)

    except Exception as e:
        # Make the failure visible but still return valid headers
        return _error(start_response, f"Traceback: {e}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--view", choices=["standard","enhanced"], default="standard")
    args = ap.parse_args()
    httpd = make_server("127.0.0.1", args.port or 0, app)
    print(f"UI: http://127.0.0.1:{httpd.server_port} (view={args.view})", flush=True)
    httpd.serve_forever()
