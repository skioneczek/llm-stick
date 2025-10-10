from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional

from services.retriever import query as query_module
from services.retriever.citations import map_citations_to_sources
from services.threads.export import render_thread_html


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
    )

    if not result:
        return {
            "plan": None,
            "summary": "",
            "bullets": [],
            "sources": [],
        }

    plan = result.get("plan")
    bullets: List[str] = result.get("bullets", []) or []
    citations = map_citations_to_sources(result.get("sources", []))
    answer_text = str(result.get("answer_text") or "")

    summary = ""
    for candidate in bullets:
        cleaned = candidate.strip().lstrip("- ")
        if cleaned:
            summary = cleaned
            break
    if not summary:
        for line in answer_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.lower().startswith("plan:"):
                continue
            summary = stripped.lstrip("- ").strip()
            if summary:
                break
    if not summary:
        summary = "No matching chunks found offline. Consider refining the question."

    # Ensure plan falls back to explanatory text
    if plan is None:
        plan = "Plan: review archives and ingest missing documents before answering."

    return {
        "plan": plan,
        "summary": summary,
        "bullets": bullets,
        "sources": citations,
        "answer_text": answer_text,
    }


def get_thread_snapshot(thread_id: str, size: str = "standard") -> str:
    """Return an HTML snapshot of a stored conversation thread."""
    font = "large" if size.lower() == "large" else "standard"
    return render_thread_html(thread_id, {"font": font})
