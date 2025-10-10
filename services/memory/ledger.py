# services/memory/ledger.py
from __future__ import annotations
import json, time
from pathlib import Path
from typing import List, Dict, Optional, Any

LEDGER_PATH = Path("Data/memory_ledger.json")

def _load() -> Dict:
    if LEDGER_PATH.exists():
        return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    return {"entries": []}

def _save(data: Dict):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

def add(
    client: str,
    key: str,
    value: str,
    *,
    source_slug: Optional[str] = None,
    client_slug: Optional[str] = None,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    d = _load()
    entry = {
        "ts": int(time.time()),
        "client": client,
        "key": key,
        "value": value[:500],  # keep it short
        "source_slug": source_slug or "unknown",
    }
    if client_slug:
        entry["client_slug"] = client_slug
    if thread_id:
        entry["thread_id"] = thread_id
    d["entries"].append(entry)
    _save(d)
    return entry

def list_client(
    client: str,
    source_slug: Optional[str] = None,
    client_slug: Optional[str] = None,
) -> List[Dict]:
    d = _load()
    results = [e for e in d["entries"] if e["client"].lower() == client.lower()]
    if source_slug:
        results = [e for e in results if e.get("source_slug") == source_slug]
    if client_slug:
        results = [e for e in results if e.get("client_slug") == client_slug]
    return results


def list_memory(thread_id: str) -> List[Dict]:
    d = _load()
    return [e for e in d["entries"] if e.get("thread_id") == thread_id]

def prune(
    client: str,
    key: str,
    source_slug: Optional[str] = None,
    client_slug: Optional[str] = None,
):
    d = _load()
    def should_keep(entry: Dict) -> bool:
        client_match = entry["client"].lower() == client.lower()
        key_match = entry["key"] == key
        source_match = True if source_slug is None else entry.get("source_slug") == source_slug
        slug_match = True if client_slug is None else entry.get("client_slug") == client_slug
        return not (client_match and key_match and source_match and slug_match)

    d["entries"] = [e for e in d["entries"] if should_keep(e)]
    _save(d)


def add_memory(
    thread_id: str,
    client_slug: str,
    source_slug: str,
    key: str,
    value: str,
    client_label: Optional[str] = None,
) -> Dict[str, Any]:
    label = client_label or client_slug or "unknown"
    return add(
        label,
        key,
        value,
        source_slug=source_slug,
        client_slug=client_slug,
        thread_id=thread_id,
    )

if __name__ == "__main__":
    # quick demo
    add_memory("thr-demo", "client-a", "123abc456def", "mission", "Conservative allocation; education priority.")
    print(list_client("client-a", source_slug="123abc456def", client_slug="client-a"))
