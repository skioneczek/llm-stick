# services/retriever/query.py
from __future__ import annotations
import json, math, argparse, datetime, re
from pathlib import Path
from typing import List, Dict, Tuple

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

def extractive_answer(query: str, hits: List[Dict]) -> Tuple[str, List[Dict]]:
    bullets: List[str] = []
    cites: List[Dict] = []
    for h in hits[:3]:
        preview = " ".join(h.get("preview", "").split()[:40]).strip()
        if not preview:
            continue
        bullets.append(f"- {preview} …")
        mtime = datetime.datetime.fromtimestamp(h["mtime"]).strftime("%Y-%m-%d")
        cites.append({"file": h["file"], "date": mtime})

    if not bullets:
        answer = "No matching chunks found offline. Consider adding source documents or refining the question."
        return answer, []

    plan = f'Plan: review retrieved chunks for "{query}" and surface key takeaways.'
    answer_lines = [plan] + bullets
    answer_lines.append('Ask "Sources?" for file names and dates.')
    answer = "\n".join(answer_lines)
    return answer, cites

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
    index_path: Path | str = Path("Data/index.json"),
    sources_only: bool = False,
    client: str | None = None,
    remember: str | None = None,
):
    index_path = Path(index_path)  # <<< normalize here
    if not index_path.exists():
        print("Index not found. Build it first: python -m services.indexer.build_index")
        return
    index = load_index(index_path)
    hits = top_hits(index, query, k=8)
    ans, cites = extractive_answer(query, hits)

    if sources_only:
        _print_sources(cites)
    else:
        print(ans)
        if cites:
            print()
        _print_sources(cites)

    memory_written = False
    if client and remember:
        if "=" not in remember:
            print("\n[Memory] Skipped: --remember must be in key=value format.")
        else:
            key, value = remember.split("=", 1)
            ledger_add(client.strip(), key.strip(), value.strip())
            memory_written = True
            print(f"\n[Memory] Stored '{key.strip()}' for {client.strip()}.")
    elif client or remember:
        print("\n[Memory] Skipped: provide both --client and --remember to store a note.")

    return {"sources": cites, "memory_written": memory_written}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True)
    ap.add_argument("--sources-only", action="store_true", help="Print only the sources list")
    ap.add_argument("--client", default=None, help="Client label for optional memory note")
    ap.add_argument("--remember", default=None, help="Memory entry in key=value form")
    ap.add_argument("--index", default="Data/index.json", help="Path to index.json (default: Data/index.json)")
    args = ap.parse_args()
    run(
        query=args.q,
        index_path=args.index,
        sources_only=args.sources_only,
        client=args.client,
        remember=args.remember,
    )
