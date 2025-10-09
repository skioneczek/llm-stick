from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

REGISTRY_PATH = Path("Data/ingested_registry.json")


def _load() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"clients": {}}


def _save(data: Dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def register_client(client_slug: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    data = _load()
    clients: Dict[str, Any] = data.setdefault("clients", {})
    existing = clients.get(client_slug, {})
    merged = {**existing, **meta}
    merged.setdefault("client_slug", client_slug)
    merged.setdefault("registered_at", int(time.time()))
    merged["last_updated"] = int(time.time())
    clients[client_slug] = merged
    _save(data)
    return merged


def get_client(client_slug: str) -> Optional[Dict[str, Any]]:
    data = _load()
    return data.get("clients", {}).get(client_slug)


def list_clients() -> Dict[str, Dict[str, Any]]:
    return _load().get("clients", {})
