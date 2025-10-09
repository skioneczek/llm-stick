# services/memory/ledger.py
from __future__ import annotations
import json, time
from pathlib import Path
from typing import List, Dict

LEDGER_PATH = Path("Data/memory_ledger.json")

def _load() -> Dict:
    if LEDGER_PATH.exists():
        return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    return {"entries": []}

def _save(data: Dict):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

def add(client: str, key: str, value: str):
    d = _load()
    d["entries"].append({
        "ts": int(time.time()),
        "client": client,
        "key": key,
        "value": value[:500]  # keep it short
    })
    _save(d)

def list_client(client: str) -> List[Dict]:
    d = _load()
    return [e for e in d["entries"] if e["client"].lower() == client.lower()]

def prune(client: str, key: str):
    d = _load()
    d["entries"] = [e for e in d["entries"] if not (e["client"].lower()==client.lower() and e["key"]==key)]
    _save(d)

if __name__ == "__main__":
    # quick demo
    add("Client A", "mission", "Conservative allocation; education priority; staged grants.")
    print(list_client("Client A"))
