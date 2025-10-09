# services/retriever/query.py
from __future__ import annotations
import json, math, argparse, datetime, re
from pathlib import Path
from typing import List, Dict

from services.indexer.source import get_current_source, index_path_for_source, slug_for_source
from services.ingest.registry import get_client
from services.memory.ledger import add as ledger_add

_ws = re.compile(r"\W+", re.U)
def toks(s: str) -> List[str]:
    return [t for t in _ws.split(s.lower()) if t]

def load_index(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))

def bm25_score(query_terms: List[str], chunk, df, N, k1=1.5, b=0.75, avgdl: float | None = None) -> float:
    # chunk["freqs"] dict; chunk["len"]
    if avgdl is None: avgdl = 1000.0
    score = 0.0
    dl = max(1, chunk["len"])
    for term in query_terms:
        f = chunk["freqs"].get(term, 0)
        if f == 0: 
            continue
        n = df.get(term, 0) or 1
        idf = math.log((N - n + 0.5) / (n + 0.5) + 1.0)
        denom = f + k1 * (1 - b + b * (dl / avgdl))
        score += idf * ((f * (k1 + 1)) / denom)
    return score

def top_hits(index: Dict, query: str, k: int = 8) -> List[Dict]:
    q = [t for t in toks(query) if len(t) > 1]
    chunks = index["chunks"]
    N = index["N"] or 1
    # naive avgdl
    avgdl = max(1.0, sum(c["len"] for c in chunks)/N)
    scored = []
    for c in chunks:
        s = bm25_score(q, c, index["df"], N, avgdl=avgdl)
        if s > 0:
            scored.append((s, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [dict(score=round(s, 4), **c) for s, c in scored[:k]]

def extractive_answer(query: str, hits: List[Dict]) -> Dict[str, object]:
    bullets: List[str] = []
    cites: List[Dict] = []
    for h in hits[:3]:
        preview = " ".join(h.get("preview", "").split()[:40]).strip()
        if not preview:
            continue
        bullets.append(f"{preview} …")
        mtime = datetime.datetime.fromtimestamp(h["mtime"]).strftime("%Y-%m-%d")
        cites.append({"file": h["file"], "date": mtime})

    if not bullets:
        plan = f'Plan: review archives for "{query}" and ingest missing documents before answering.'
        answer_text = "\n".join(
            [
                plan,
                "- No matching chunks found offline. Consider adding source documents or refining the question.",
                'Ask "Sources?" for file names and dates.',
            ]
        )
        return {
            "plan": plan,
            "bullets": [],
            "citations": [],
            "answer_text": answer_text,
        }

    plan = f'Plan: review retrieved chunks for "{query}" and surface key takeaways.'
    answer_lines = [plan] + [f"- {b}" for b in bullets]
    answer_lines.append('Ask "Sources?" for file names and dates.')
    answer_text = "\n".join(answer_lines)
    return {
        "plan": plan,
        "bullets": bullets,
        "citations": cites,
        "answer_text": answer_text,
    }

def _print_sources(cites: List[Dict]):
    if cites:
        print("Sources:")
        for c in cites:
            print(f"- {c['file']} (modified {c['date']})")
    else:
        print("Sources:")
        print("- None (no matching documents found)")


def run(
    query: str,
    index_path: Path | str | None = None,
    sources_only: bool = False,
    client: str | None = None,
    remember: str | None = None,
    use_client: str | None = None,
    source_override: Path | str | None = None,
    suppress_output: bool = False,
):
    source_entry = None
    if use_client:
        source_entry = get_client(use_client)
        if not source_entry:
            if not suppress_output:
                print(f"Client registry entry not found: {use_client}")
            return
        source_path_str = source_entry.get("source")
        index_path_str = source_entry.get("index_path")
        if not source_path_str or not index_path_str:
            if not suppress_output:
                print(f"Incomplete registry entry for client: {use_client}")
            return
        source_path = Path(source_path_str).expanduser()
        source_slug = source_entry.get("slug") or use_client
        resolved_index = Path(index_path_str).expanduser()
    else:
        if source_override is not None:
            source_path = Path(source_override).expanduser()
        else:
            source_path = get_current_source()
        source_slug = slug_for_source(source_path)
        resolved_index = (
            Path(index_path)
            if index_path is not None
            else index_path_for_source(source_path)
        )

    if not resolved_index.exists():
        msg = "Index not found; please build index for the selected folder."
        if use_client:
            msg = f"Index not found for client {use_client}; ensure ingest completed."
        if not suppress_output:
            print(msg)
        return

    if resolved_index.suffix == ".enc":
        if not suppress_output:
            print(f"Encrypted index detected at {resolved_index}. Decryption not yet implemented.")
        return

    index = load_index(resolved_index)
    hits = top_hits(index, query, k=8)
    answer_data = extractive_answer(query, hits)
    plan = answer_data.get("plan")
    bullets = answer_data.get("bullets", [])
    cites = answer_data.get("citations", [])
    answer_text = answer_data.get("answer_text", "")

    if sources_only:
        if not suppress_output:
            _print_sources(cites)
    else:
        if not suppress_output:
            print(answer_text)
            if cites:
                print()
            _print_sources(cites)

    memory_written = False
    if client and remember:
        if "=" not in remember:
            if not suppress_output:
                print("\n[Memory] Skipped: --remember must be in key=value format.")
        else:
            key, value = remember.split("=", 1)
            ledger_add(
                client.strip(),
                key.strip(),
                value.strip(),
                source_slug=source_slug,
                client_slug=use_client,
            )
            memory_written = True
            if not suppress_output:
                print(f"\n[Memory] Stored '{key.strip()}' for {client.strip()} (source {source_slug}).")
    elif client or remember:
        if not suppress_output:
            print("\n[Memory] Skipped: provide both --client and --remember to store a note.")

    return {
        "sources": cites,
        "memory_written": memory_written,
        "source_path": str(source_path),
        "source_slug": source_slug,
        "client_slug": use_client or None,
        "index_path": str(resolved_index),
        "plan": plan,
        "bullets": bullets,
        "answer_text": answer_text,
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True)
    ap.add_argument("--sources-only", action="store_true", help="Print only the sources list")
    ap.add_argument("--client", default=None, help="Client label for optional memory note")
    ap.add_argument("--remember", default=None, help="Memory entry in key=value form")
    ap.add_argument(
        "--index",
        default=None,
        help="Override index path (defaults to active source index)",
    )
    ap.add_argument(
        "--show-active-source",
        action="store_true",
        help="Print the active source path and index, then exit",
    )
    ap.add_argument(
        "--use-client",
        default=None,
        help="Use the ingest registry entry for the specified client slug",
    )
    args = ap.parse_args()

    if args.show_active_source:
        if args.use_client:
            entry = get_client(args.use_client)
            if not entry:
                print(f"Client registry entry not found: {args.use_client}")
                raise SystemExit(1)
            print(f"Client slug: {args.use_client}")
            print(f"Source path: {entry.get('source')}")
            print(f"Index file: {entry.get('index_path')}")
            print(f"Storage mode: {entry.get('storage_mode')}")
            print(f"OCR available: {entry.get('ocr_available')}")
        else:
            current = get_current_source()
            slug = slug_for_source(current)
            index_file = (
                Path(args.index)
                if args.index is not None
                else index_path_for_source(current)
            )
            print(f"Active source: {current}")
            print(f"Source slug: {slug}")
            print(f"Index file: {index_file}")
        raise SystemExit(0)

    run(
        query=args.q,
        index_path=args.index,
        sources_only=args.sources_only,
        client=args.client,
        remember=args.remember,
        use_client=args.use_client,
    )
