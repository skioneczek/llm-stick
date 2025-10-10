from __future__ import annotations
from pathlib import Path
import datetime
from collections import defaultdict
from typing import Callable, Dict, Iterator, List, Optional, Tuple

from core.llm import invoke as llm_invoke
from core.llm import wrap as llm_wrap
from services.indexer.build_index import chunk_text, iter_files, read_file
from services.indexer.source import (
    get_current_source,
    index_path_for_source,
    slug_for_source,
)
from services.ingest.registry import get_client
from services.retriever import query as query_module
from services.retriever.citations import map_citations_to_sources
from services.threads.export import render_thread_html


StreamCallback = Optional[Callable[[str], None]]


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


def _resolve_source(
    slug: Optional[str],
    source_override: Optional[str] = None,
) -> Tuple[Path, Optional[Path], str, Optional[str]]:
    if slug:
        entry = get_client(slug)
        if not entry:
            raise ValueError(f"Client registry entry not found: {slug}")
        source_path_str = entry.get("source")
        index_path_str = entry.get("index_path")
        if not source_path_str:
            raise ValueError(f"Registry entry missing source path for client {slug}")
        source_path = Path(source_path_str).expanduser()
        index_path = Path(index_path_str).expanduser() if index_path_str else None
        resolved_slug = entry.get("slug") or slug
        return source_path, index_path, resolved_slug, slug

    if source_override:
        source_path = Path(source_override).expanduser()
        resolved_slug = slug_for_source(source_path)
        index_path = index_path_for_source(source_path)
        return source_path, index_path, resolved_slug, None

    source_path = get_current_source()
    resolved_slug = slug_for_source(source_path)
    index_path = index_path_for_source(source_path)
    return source_path, index_path, resolved_slug, None


def _build_temp_index(source_path: Path, *, max_chunks: int = 120) -> Dict[str, object]:
    df: Dict[str, int] = defaultdict(int)
    chunks: List[Dict[str, object]] = []

    for file_path in iter_files(source_path):
        try:
            raw = read_file(file_path)
        except Exception:
            continue
        if not raw or not raw.strip():
            continue

        rel_file = str(file_path.relative_to(source_path))
        mtime = int(file_path.stat().st_mtime)
        for idx, chunk in enumerate(chunk_text(raw, 900, 180)):
            tokens = query_module.toks(chunk)
            if not tokens:
                continue
            freqs: Dict[str, int] = {}
            for token in tokens:
                if len(token) < 2:
                    continue
                freqs[token] = freqs.get(token, 0) + 1
            if not freqs:
                continue
            for token in freqs.keys():
                df[token] = df.get(token, 0) + 1
            chunks.append(
                {
                    "id": f"{rel_file}:::{idx}",
                    "file": rel_file,
                    "mtime": mtime,
                    "len": len(tokens),
                    "freqs": freqs,
                    "preview": " ".join(tokens[:120]),
                    "text": chunk,
                }
            )
            if len(chunks) >= max_chunks:
                break
        if len(chunks) >= max_chunks:
            break

    return {
        "chunks": chunks,
        "df": dict(df),
        "N": len(chunks),
    }


def _format_context(hits: List[Dict]) -> str:
    if not hits:
        return "No offline context available."

    blocks: List[str] = []
    for idx, hit in enumerate(hits, 1):
        snippet = hit.get("text") or hit.get("preview") or ""
        snippet = snippet.replace("\n", " ").strip()
        if len(snippet) > 900:
            snippet = snippet[:900].rsplit(" ", 1)[0] + " …"
        date_str = datetime.datetime.fromtimestamp(hit["mtime"]).strftime("%Y-%m-%d")
        blocks.append(
            f"[{idx}] {hit['file']} (modified {date_str})\n{snippet}"
        )
    return "\n\n".join(blocks)


def _stream_llm(prompt_text: str, stream_callback: StreamCallback = None) -> str:
    profiles = llm_wrap.load_profiles()
    profile_name, profile = llm_wrap.select_profile(profiles, None)

    binary_path = llm_wrap.resolve_rel_path(profile["bin_rel"])
    model_path = llm_wrap.resolve_rel_path(profile["model_rel"])

    llm_wrap.ensure_asset(binary_path, "binary", profile_name)
    llm_wrap.ensure_asset(model_path, "model", profile_name)
    llm_wrap.verify_checksums(profile_name, [binary_path, model_path])

    command = llm_wrap.build_command(profile, binary_path, model_path, prompt_text)
    result = llm_invoke.invoke(
        command,
        prompt_text,
        profile_name=profile_name,
        stream_callback=stream_callback,
    )

    if result.returncode != 0:
        raise RuntimeError(f"LLM process exited with status {result.returncode}")

    return result.stdout.strip()


def _extract_plan_answer(output: str) -> Tuple[str, str]:
    normalized = output.strip()
    lower = normalized.lower()
    plan_marker = lower.find("plan:")
    answer_marker = lower.find("answer:")

    plan_body = ""
    answer_body = ""

    if plan_marker != -1:
        if answer_marker != -1 and answer_marker > plan_marker:
            plan_body = normalized[plan_marker + 5 : answer_marker].strip()
        else:
            plan_body = normalized[plan_marker + 5 :].strip()

    if answer_marker != -1:
        answer_body = normalized[answer_marker + 7 :].strip()

    if not plan_body and normalized:
        plan_body = "Review retrieved context and answer succinctly."

    if not answer_body:
        answer_body = normalized

    plan_body = plan_body.lstrip("- ")
    answer_body = answer_body.lstrip("- ")

    return plan_body, answer_body


def answer_llm(
    prompt: str,
    *,
    source_slug: Optional[str] = None,
    source_path: Optional[str] = None,
    realtime: bool = False,
    stream_callback: StreamCallback = None,
    max_chunks: int = 12,
) -> Dict[str, object]:
    source_path_resolved, index_path, resolved_slug, client_slug = _resolve_source(
        source_slug,
        source_override=source_path,
    )

    hits: List[Dict] = []
    retrieval_mode = "index"

    if not realtime and index_path and index_path.exists():
        index_data = query_module.load_index(index_path)
        hits = query_module.top_hits(index_data, prompt, k=max_chunks)
    else:
        retrieval_mode = "realtime"
        temp_index = _build_temp_index(source_path_resolved)
        hits = query_module.top_hits(temp_index, prompt, k=max_chunks)

    context_block = _format_context(hits)

    prompt_text = (
        "You are the offline LLM Stick assistant. Review the context below and answer the query.\n"
        "Respond in this exact structure:\n"
        "Plan: <one sentence describing the approach>\n"
        "Answer: <concise paragraph grounded in the context>\n"
        "Do not list citations or extra sections unless asked.\n\n"
        f"User query: {prompt}\n\n"
        f"Context:\n{context_block}\n"
    )

    emitted_tokens: List[str] = []
    buffer: List[str] = []

    def _emit(token: str) -> None:
        token = token
        if not token:
            return
        emitted_tokens.append(token)
        if stream_callback:
            stream_callback(token)

    def _handle_chunk(chunk: str) -> None:
        buffer.append(chunk)
        if chunk in {" ", "\n"} or len(buffer) >= 16:
            tok = "".join(buffer)
            buffer.clear()
            _emit(tok)

    output = _stream_llm(prompt_text, stream_callback=_handle_chunk)
    if buffer:
        _emit("".join(buffer))
    plan_text, answer_text = _extract_plan_answer(output)

    raw_sources = []
    for hit in hits:
        try:
            date_str = datetime.datetime.fromtimestamp(hit["mtime"]).strftime("%Y-%m-%d")
        except (KeyError, TypeError, ValueError):
            date_str = ""
        raw_sources.append({"file": hit.get("file", ""), "date": date_str})

    sources = map_citations_to_sources(raw_sources)

    return {
        "plan": plan_text,
        "answer": answer_text,
        "sources": sources,
        "source_path": str(source_path_resolved),
        "source_slug": resolved_slug,
        "client_slug": client_slug,
        "mode": retrieval_mode,
        "raw_output": output,
        "stream": emitted_tokens,
    }


def get_thread_snapshot(thread_id: str, size: str = "standard") -> str:
    """Return an HTML snapshot of a stored conversation thread."""
    font = "large" if size.lower() == "large" else "standard"
    return render_thread_html(thread_id, {"font": font})
