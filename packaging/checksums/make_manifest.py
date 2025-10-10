"""Generate SHA256 manifest for LLM binaries, models, and web UI assets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKSUM_ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = CHECKSUM_ROOT / "manifest.json"
SHA_ROOT = CHECKSUM_ROOT / "sha256"
TARGET_ROOTS = [
    Path("App/bin/llama"),
    Path("App/models/llm"),
    Path("apps/webui/static"),
    Path("apps/webui/templates"),
]


def sha256_digest(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        resolved = (REPO_ROOT / root).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Checksum target missing: {resolved}")
        if not resolved.is_dir():
            raise NotADirectoryError(f"Checksum target is not a directory: {resolved}")
        for file_path in sorted(resolved.rglob("*")):
            if file_path.is_file():
                yield file_path


def write_sha_file(rel_path: Path, digest: str) -> None:
    sha_dir = SHA_ROOT / rel_path.parent
    sha_dir.mkdir(parents=True, exist_ok=True)
    sha_file = sha_dir / f"{rel_path.name}.sha256"
    sha_file.write_text(f"{digest}  {rel_path.as_posix()}\n", encoding="utf-8")


def build_manifest() -> Dict[str, str]:
    manifest: Dict[str, str] = {}
    SHA_ROOT.mkdir(parents=True, exist_ok=True)
    for file_path in iter_files(TARGET_ROOTS):
        rel_path = file_path.relative_to(REPO_ROOT)
        digest = sha256_digest(file_path)
        manifest[rel_path.as_posix()] = digest
        write_sha_file(rel_path, digest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate checksum manifest")
    parser.add_argument(
        "--manifest",
        dest="manifest_path",
        default=MANIFEST_PATH,
        type=Path,
        help="Output manifest path (default: packaging/checksums/manifest.json)",
    )
    args = parser.parse_args()
    manifest = build_manifest()
    args.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_path.write_text(
        json.dumps(dict(sorted(manifest.items())), indent=2),
        encoding="utf-8",
    )
    print(f"Wrote manifest with {len(manifest)} entries to {args.manifest_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
