from __future__ import annotations
from pathlib import Path
from typing import Iterable, Dict, List


def map_citations_to_sources(citations: Iterable[Dict]) -> List[Dict[str, str]]:
    """Return a de-duplicated list of filename/date tuples from retrieval citations."""
    normalized = []
    seen = set()
    for cite in citations or []:
        file_val = str(cite.get("file") or "").strip()
        date_val = str(cite.get("date") or "").strip()
        name = Path(file_val).name if file_val else ""
        if not name and not date_val:
            continue
        key = (name, date_val)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"file": name, "date": date_val})
    return normalized
