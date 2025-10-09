from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional

from services.retriever import query as query_module
from services.retriever.citations import map_citations_to_sources
from services.threads.export import render_thread_html


def _format_answer(result: Dict[str, object]) -> str:
    if not result:
        return "Here's what I found."

    answer_text = str(
        result.get("answer")
        or result.get("answer_text")
        or ""
    ).strip()
    if answer_text:
        return answer_text

    plan = str(result.get("plan") or "").strip()
    bullets = [str(b).strip() for b in (result.get("bullets") or []) if str(b).strip()]

    segments: List[str] = []
    if plan:
        segments.append(plan)
    if bullets:
        bullet_lines = "\n".join(f"• {b}" for b in bullets)
        if plan:
            segments.append("Here are the key points:\n" + bullet_lines)
        else:
            segments.append("Here are the key points:\n" + bullet_lines)

    combined = "\n".join(segments).strip()
    if combined:
        return combined

    return "Here's what I found."


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

    answer_data = result
    plan = answer_data.get("plan")
    bullets: List[str] = answer_data.get("bullets", []) or []
    citations = map_citations_to_sources(answer_data.get("sources", []))

    # Ensure plan falls back to explanatory text
    if plan is None:
        plan = "Plan: review archives and ingest missing documents before answering."

    formatted = _format_answer({
        "plan": plan,
        "bullets": bullets,
        "answer_text": answer_data.get("answer_text"),
        "answer": answer_data.get("answer"),
    })

    return {
        "plan": plan,
        "bullets": bullets,
        "sources": citations,
        "answer": formatted,
        "answer_text": formatted,
    }


def get_thread_snapshot(thread_id: str, size: str = "standard") -> str:
    """Return an HTML snapshot of a stored conversation thread."""
    font = "large" if size.lower() == "large" else "standard"
    return render_thread_html(thread_id, {"font": font})
