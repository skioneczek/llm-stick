from __future__ import annotations
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path("Data/conversations")
INDEX_PATH = BASE_DIR / "index.json"


def _ensure_base() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def _thread_path(thread_id: str) -> Path:
    _ensure_base()
    return BASE_DIR / f"{thread_id}.json"


def _load_index() -> Dict[str, Any]:
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return {"threads": []}


def _save_index(data: Dict[str, Any]) -> None:
    _ensure_base()
    INDEX_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _meta_from_thread(thread: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": thread["id"],
        "title": thread.get("title", ""),
        "client_slug": thread.get("client_slug"),
        "source_slug": thread.get("source_slug"),
        "source_path": thread.get("source_path"),
        "created_at": thread.get("created_at"),
        "updated_at": thread.get("updated_at"),
        "archived": thread.get("archived", False),
    }


def _write_thread(thread: Dict[str, Any]) -> None:
    path = _thread_path(thread["id"])
    path.write_text(json.dumps(thread, indent=2), encoding="utf-8")


def _touch_index(meta: Dict[str, Any]) -> None:
    data = _load_index()
    threads: List[Dict[str, Any]] = data.setdefault("threads", [])
    for idx, entry in enumerate(threads):
        if entry.get("id") == meta["id"]:
            threads[idx] = {**entry, **meta}
            break
    else:
        threads.append(meta)
    _save_index(data)


def get_thread(thread_id: str) -> Optional[Dict[str, Any]]:
    path = _thread_path(thread_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_threads(include_archived: bool = False) -> List[Dict[str, Any]]:
    data = _load_index()
    threads = data.get("threads", [])
    if include_archived:
        return threads
    return [t for t in threads if not t.get("archived")]


def new_thread(
    title: str,
    client_slug: str,
    source_slug: str,
    *,
    source_path: Optional[str] = None,
) -> Dict[str, Any]:
    _ensure_base()
    now = int(time.time())
    thread_id = f"thr-{now}-{uuid.uuid4().hex[:6]}"
    thread = {
        "id": thread_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "client_slug": client_slug,
        "source_slug": source_slug,
        "source_path": source_path,
        "messages": [],
        "archived": False,
    }
    _write_thread(thread)
    _touch_index(_meta_from_thread(thread))
    return thread


def update_thread(
    thread_id: str,
    *,
    title: Optional[str] = None,
    client_slug: Optional[str] = None,
    source_slug: Optional[str] = None,
    archived: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    thread = get_thread(thread_id)
    if thread is None:
        return None
    changed = False
    if title is not None:
        thread["title"] = title
        changed = True
    if client_slug is not None:
        thread["client_slug"] = client_slug
        changed = True
    if source_slug is not None:
        thread["source_slug"] = source_slug
        changed = True
    if archived is not None:
        thread["archived"] = bool(archived)
        changed = True
    if changed:
        thread["updated_at"] = int(time.time())
        _write_thread(thread)
        _touch_index(_meta_from_thread(thread))
    return thread


def archive_thread(thread_id: str, archive: bool = True) -> Optional[Dict[str, Any]]:
    return update_thread(thread_id, archived=archive)


def append_message(
    thread_id: str,
    role: str,
    text: str,
    citations: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    thread = get_thread(thread_id)
    if thread is None:
        return None
    message = {
        "role": role,
        "text": text,
        "ts": int(time.time()),
        "citations": citations or [],
        "meta": meta or {},
    }
    thread.setdefault("messages", []).append(message)
    thread["updated_at"] = int(time.time())
    _write_thread(thread)
    _touch_index(_meta_from_thread(thread))
    return message


def search(
    query: Optional[str] = None,
    *,
    include_archived: bool = False,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    query_lc = (query or "").strip().lower()

    threads = list_threads(include_archived=include_archived)
    if not query_lc:
        if limit and limit > 0:
            return threads[:limit]
        return threads

    max_results = limit if limit and limit > 0 else None

    matches: List[Dict[str, Any]] = []
    for meta in threads:
        if max_results is not None and len(matches) >= max_results:
            break
        title = meta.get("title", "")
        if query_lc in title.lower():
            matches.append({**meta, "snippet": title})
            continue
        thread = get_thread(meta["id"])
        if not thread:
            continue
        snippet = None
        for msg in thread.get("messages", []):
            text = msg.get("text", "")
            if query_lc in text.lower():
                snippet = text.strip()
                break
        if snippet:
            matches.append({**meta, "snippet": snippet})
            if max_results is not None and len(matches) >= max_results:
                break
    return matches
