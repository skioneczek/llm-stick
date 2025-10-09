from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional

from services.retriever import query as query_module


def answer(
    prompt: str,
    *,
    client_slug: Optional[str] = None,
    source_path: Optional[str] = None,
    index_path: Optional[str] = None,
) -> Dict[str, object]:
    """Return structured retrieval output without printing to stdout."""
    if client_slug and source_path:
        raise ValueError("Provide either client_slug or source_path, not both.")

    result = query_module.run(
        prompt,
        index_path=Path(index_path) if index_path else None,
        use_client=client_slug,
        source_override=source_path,
        suppress_output=True,
    )

    if not result:
        return {
            "plan": None,
            "bullets": [],
            "sources": [],
        }

    plan = result.get("plan")
    bullets: List[str] = result.get("bullets", []) or []
    citations = result.get("sources", []) or []

    # Ensure plan falls back to explanatory text
    if plan is None:
        plan = "Plan: review archives and ingest missing documents before answering."

    return {
        "plan": plan,
        "bullets": bullets,
        "sources": citations,
    }
