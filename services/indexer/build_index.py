# services/indexer/build_index.py
from __future__ import annotations
import os, json, re, time, argparse
from pathlib import Path
from typing import Iterable, Dict, List, Tuple

SUPPORTED = {".txt", ".md", ".docx", ".pdf"}  # .docx/.pdf are optional (skip if libs unavailable)

def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED:
            yield p

_ws = re.compile(r"\W+", re.U)
def tokenize(text: str) -> List[str]:
    return [t for t in _ws.split(text.lower()) if t]

def read_txt(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def read_docx(p: Path) -> str:
    try:
        from docx import Document  # optional
        doc = Document(str(p))
        return "\n".join(para.text for para in doc.paragraphs)
    except Exception:
        return ""  # skip silently if lib not installed

def read_pdf(p: Path) -> str:
    try:
        import PyPDF2  # optional
        text = []
        with open(p, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for pg in reader.pages:
                try:
                    text.append(pg.extract_text() or "")
                except Exception:
                    pass
        return "\n".join(text)
    except Exception:
        return ""  # skip silently if lib not installed

def read_file(p: Path) -> str:
    ext = p.suffix.lower()
    if ext in {".txt", ".md"}:
        return read_txt(p)
    if ext == ".docx":
        return read_docx(p)
    if ext == ".pdf":
        return read_pdf(p)
    return ""

def chunk_text(text: str, target_words=1000, overlap_words=120) -> List[str]:
    words = tokenize(text)
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + target_words]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if len(chunk_words) < target_words:
            break
        i += target_words - overlap_words
    return chunks

def build_index(src_root: Path, out_path: Path) -> None:
    src_root = src_root.resolve()
    docs_meta: List[Dict] = []
    chunks: List[Dict] = []
    df: Dict[str, int] = {}
    total_chunks = 0

    for fp in iter_files(src_root):
        raw = read_file(fp)
        if not raw.strip():
            continue
        ctime = os.path.getmtime(fp)
        meta = {
            "file": str(fp.relative_to(src_root)),
            "mtime": int(ctime),
        }
        doc_chunks = chunk_text(raw, 1000, 120)
        for idx, ch in enumerate(doc_chunks):
            cid = f"{meta['file']}:::{idx}"
            toks = tokenize(ch)
            freqs: Dict[str, int] = {}
            for t in toks:
                if len(t) < 2:  # drop 1-letter tokens
                    continue
                freqs[t] = freqs.get(t, 0) + 1
            for t in freqs.keys():
                df[t] = df.get(t, 0) + 1
            chunks.append({
                "id": cid,
                "file": meta["file"],
                "mtime": meta["mtime"],
                "len": len(toks),
                "freqs": freqs,
                "preview": " ".join(toks[:60])  # for quick UI preview
            })
            total_chunks += 1
        docs_meta.append(meta)

    index = {
        "built_at": int(time.time()),
        "root": str(src_root),
        "chunks": chunks,
        "df": df,
        "N": total_chunks
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index), encoding="utf-8")
    print(f"Indexed {len(chunks)} chunks from {len(docs_meta)} files into {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="stick_root/Samples")
    ap.add_argument("--out", default="Data/index.json")
    args = ap.parse_args()
    build_index(Path(args.src), Path(args.out))
