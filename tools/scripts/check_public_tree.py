#!/usr/bin/env python3
"""Read-only publication preflight over tracked and normally addable Git paths."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

PRIVATE_ROOTS = {"references", ".archon-horizon", ".homalg", ".codex", ".claude"}
PRIVATE_ROOT_FILES = {"config.yaml", ".mcp.json", ".env"}


def private_path(name: str) -> bool:
    """Reject private source/runtime paths even if someone force-added an ignored file."""
    path = Path(name)
    parts = path.parts
    return bool(parts) and (
        parts[0] in PRIVATE_ROOTS
        or name in PRIVATE_ROOT_FILES
        or path.suffix.lower() == ".pdf"
        or (
            parts[0] == "literature"
            and (
                len(parts) > 1
                and parts[1] == ".private"
                or len(parts) > 2
                and parts[2] in {"text", "pages", "ingest.yaml"}
            )
        )
        or (path.name.startswith(".env.") and path.name not in {".env.example", ".env.sample"})
    )


def check(repo: Path) -> dict:
    """Inspect paths without staging, committing, publishing or printing private content."""
    repo = repo.resolve()
    process = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    candidates = sorted(set(filter(None, process.stdout.split("\0"))))
    findings = []
    for name in candidates:
        path = repo / name
        if private_path(name):
            findings.append({"path": name, "reason": "private path or PDF is public/addable"})
        elif path.is_symlink():
            target = path.resolve()
            if not target.is_relative_to(repo) or private_path(target.relative_to(repo).as_posix()):
                findings.append(
                    {"path": name, "reason": "symlink exposes an external/private target"}
                )
    return {
        "repository": str(repo),
        "candidate_files": len(candidates),
        "findings": findings,
        "ok": not findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    options = parser.parse_args()
    result = check(options.repo)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
