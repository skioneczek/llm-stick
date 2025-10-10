"""Offline llama.cpp wrapper CLI for the LLM Stick project."""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from . import invoke as invoke_lib

ROOT = Path(__file__).resolve().parent.parent.parent
PROFILES_PATH = Path(__file__).resolve().parent / "profiles.json"
MANIFEST_PATH = ROOT / "packaging" / "checksums" / "manifest.json"
EXIT_MISSING_ASSET = 2


def load_profiles() -> Dict[str, dict]:
    if not PROFILES_PATH.exists():
        raise FileNotFoundError(f"Missing profiles file at {PROFILES_PATH}")

    with PROFILES_PATH.open("r", encoding="utf-8") as handle:
        content = json.load(handle)

    if not isinstance(content, dict):
        raise ValueError("profiles.json must contain an object mapping names to profiles")

    return content


def select_profile(profiles: Dict[str, dict], requested: Optional[str]) -> Tuple[str, dict]:
    if requested:
        profile = profiles.get(requested)
        if profile is None:
            available = ", ".join(sorted(profiles.keys())) or "<none>"
            raise KeyError(f"Unknown profile '{requested}'. Available: {available}")
        return requested, profile

    defaults = [name for name, data in profiles.items() if data.get("default")]
    if len(defaults) == 1:
        name = defaults[0]
        return name, profiles[name]

    raise RuntimeError("No profile name provided and default profile is ambiguous or missing")


def resolve_rel_path(rel_value: str) -> Path:
    """Resolve OS-specific relative paths like "llama.exe|llama"."""
    if "|" in rel_value:
        windows_part, _, other_part = rel_value.partition("|")
        chosen = windows_part if platform.system().lower().startswith("win") else other_part
    else:
        chosen = rel_value

    chosen = chosen.strip()
    if not chosen:
        raise ValueError(f"Invalid relative path specification: '{rel_value}'")

    parts = [segment for segment in chosen.replace("\\", "/").split("/") if segment]
    return ROOT.joinpath(*parts)


def ensure_asset(path: Path, asset_kind: str, profile_name: str) -> None:
    if path.exists():
        return
    drop_hint = "App/bin/llama/" if asset_kind == "binary" else "App/models/llm/"
    message = (
        f"LLM {asset_kind} missing for profile '{profile_name}'.\n"
        f"Expected path: {path}\n"
        f"Action: Drop the required file under '{drop_hint}' and retry."
    )
    print(message, file=sys.stderr)
    sys.exit(EXIT_MISSING_ASSET)


def load_manifest() -> Optional[Dict[str, str]]:
    if not MANIFEST_PATH.exists():
        return None

    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, dict):
        return {str(key): str(value) for key, value in data.items()}

    if isinstance(data, list):
        manifest: Dict[str, str] = {}
        for item in data:
            if isinstance(item, dict) and "path" in item and "sha256" in item:
                manifest[str(item["path"])] = str(item["sha256"])
        return manifest

    raise ValueError("checksum manifest must be an object or list of {path, sha256}")


def observed_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checksums(profile_name: str, assets: Iterable[Path]) -> None:
    manifest = load_manifest()
    if manifest is None:
        print(
            "LLM checksum manifest missing. Run packaging/checksums/make_manifest.py before invoking the wrapper.",
            file=sys.stderr,
        )
        sys.exit(EXIT_MISSING_ASSET)

    problems = []
    for asset in assets:
        rel_key_options = {
            asset.relative_to(ROOT).as_posix(),
            str(asset.relative_to(ROOT)),
        }
        manifest_entry = None
        for key in rel_key_options:
            if key in manifest:
                manifest_entry = manifest[key]
                break

        if manifest_entry is None:
            problems.append(f"No checksum entry for {asset}")
            continue

        actual = observed_sha256(asset)
        if actual.lower() != manifest_entry.lower():
            problems.append(
                "Checksum mismatch for "
                f"{asset} (expected {manifest_entry}, observed {actual})"
            )

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        sys.exit(EXIT_MISSING_ASSET)

    print(f"LLM assets verified (sha256 ok): {profile_name}")


def build_command(profile: dict, binary_path: Path, model_path: Path, prompt: str) -> list[str]:
    cmd = [str(binary_path), "--model", str(model_path), "--prompt", prompt]

    ctx_size = profile.get("ctx")
    if ctx_size:
        cmd.extend(["--ctx-size", str(ctx_size)])

    gpu_layers = profile.get("gpu_layers")
    if gpu_layers is not None:
        cmd.extend(["--n-gpu-layers", str(gpu_layers)])

    threads_env = profile.get("threads_env")
    if threads_env:
        threads_value = os.getenv(threads_env)
        if threads_value:
            cmd.extend(["--threads", str(threads_value)])

    extra_params = profile.get("params", [])
    if extra_params:
        cmd.extend([str(item) for item in extra_params])

    return cmd


def run_profile(profile_name: str, profile: dict, prompt: str) -> None:
    binary_path = resolve_rel_path(profile["bin_rel"])
    model_path = resolve_rel_path(profile["model_rel"])

    ensure_asset(binary_path, "binary", profile_name)
    ensure_asset(model_path, "model", profile_name)

    verify_checksums(profile_name, [binary_path, model_path])

    command = build_command(profile, binary_path, model_path, prompt)
    try:
        result = invoke_lib.invoke(
            command,
            prompt,
            profile_name=profile_name,
            stdout_sink=lambda chunk: (sys.stdout.write(chunk), sys.stdout.flush()),
            stderr_sink=lambda chunk: (sys.stderr.write(chunk), sys.stderr.flush()),
        )
    except FileNotFoundError as exc:
        print(f"Failed to start llama.cpp binary: {exc}", file=sys.stderr)
        sys.exit(EXIT_MISSING_ASSET)

    if result.returncode != 0:
        print(f"llama.cpp exited with status {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)


def list_profiles(profiles: Dict[str, dict]) -> None:
    for name, data in sorted(profiles.items()):
        default_mark = " (default)" if data.get("default") else ""
        label = data.get("label", "")
        print(f"{name}{default_mark}: {label}")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline llama.cpp wrapper for the LLM Stick"
    )
    parser.add_argument("--list-profiles", action="store_true", help="List available profiles")
    parser.add_argument("--run", action="store_true", help="Execute a profile against a prompt")
    parser.add_argument("--profile", help="Profile name to use (defaults to flagged default)")
    parser.add_argument("--prompt", help="Prompt text for llama.cpp")
    args = parser.parse_args(argv)

    if not args.list_profiles and not args.run:
        parser.error("Specify --list-profiles or --run")

    if args.run and not args.prompt:
        parser.error("--prompt is required when using --run")

    return args


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_args(argv)
    profiles = load_profiles()

    if args.list_profiles:
        list_profiles(profiles)
        if not args.run:
            return

    profile_name, profile = select_profile(profiles, args.profile)

    if args.run:
        run_profile(profile_name, profile, args.prompt)


if __name__ == "__main__":
    main()
