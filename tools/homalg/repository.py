"""Locate a checkout and enumerate its authored document/node files."""

import re
from pathlib import Path

DOC_KEY = re.compile(r"[A-Z][A-Za-z]*[0-9]{4}[A-Za-z0-9]*")


def find_repo(path: Path | None = None) -> Path:
    """Find the enclosing Lake package or validate an explicitly supplied root."""
    start = (path or Path.cwd()).resolve()
    candidates = [start] if path is not None else [start, *start.parents]
    for candidate in candidates:
        if (candidate / "lakefile.toml").is_file() and (candidate / "schema").is_dir():
            return candidate
    raise ValueError("No HomAlgDB checkout found; use --repo PATH")


def documents(repo: Path, selected: tuple[str, ...] = ()) -> list[str]:
    """List registered documents, rejecting unknown or unsafe selectors."""
    available = sorted(path.parent.name for path in (repo / "literature").glob("*/document.yaml"))
    for key in [*available, *selected]:
        if not DOC_KEY.fullmatch(key):
            raise ValueError(f"Invalid document key: {key}")
    missing = set(selected) - set(available)
    if missing:
        raise ValueError(f"Unknown document(s): {', '.join(sorted(missing))}")
    return list(dict.fromkeys(selected)) if selected else available


def node_paths(repo: Path, keys: list[str]) -> list[Path]:
    """Enumerate flat node files in stable document/name order."""
    return [path for key in sorted(keys) for path in sorted((repo / "HomAlg" / key).glob("*.lean"))]
