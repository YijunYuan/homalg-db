"""Deterministic serialization and atomic writes (R7.3)."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def json_text(value: Any) -> str:
    """Encode reproducible, human-readable JSON with a trailing newline."""
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def atomic_write(path: Path, text: str) -> None:
    """Replace a file atomically, retaining its mode and skipping identical writes."""
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o644)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_bytes(path: Path, data: bytes) -> None:
    """Atomically replace binary artifacts without changing identical files."""
    if path.exists() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
