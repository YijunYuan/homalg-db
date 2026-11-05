"""Deterministic serialization and atomic writes (R7.3)."""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def json_text(value: Any) -> str:
    """Encode reproducible, human-readable JSON with a trailing newline."""
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _atomic_replace(
    path: Path,
    data: bytes,
    *,
    mode: int | None,
    receipt: bool,
) -> dict[str, Any] | None:
    """Publish an owned temporary inode; optionally prove ownership to the caller."""
    if not receipt and path.exists() and path.read_bytes() == data:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode is None:
        mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            staged = os.fstat(stream.fileno())
            os.replace(temporary, path)
            if not receipt:
                return None
            # The fd still identifies OUR inode even if another writer replaces
            # the path before this function returns. Never infer ownership merely
            # because the path happens to contain identical bytes.
            owned = os.fstat(stream.fileno())
            fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
            with path.open("rb") as published:
                current = os.fstat(published.fileno())
                digest = hashlib.file_digest(published, "sha256").hexdigest()
            final = path.stat()
            if (
                path.is_symlink()
                or owned.st_nlink != 1
                or owned.st_mtime_ns != staged.st_mtime_ns
                or digest != hashlib.sha256(data).hexdigest()
                or any(getattr(current, key) != getattr(owned, key) for key in fields)
                or any(getattr(final, key) != getattr(owned, key) for key in fields)
            ):
                raise ValueError(f"Atomic write ownership changed before receipt: {path}")
            return {"sha256": digest, **{key: getattr(owned, key) for key in fields}}
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write(path: Path, text: str) -> None:
    """Replace UTF-8 text atomically, retaining mode and skipping identical bytes."""
    _atomic_replace(path, text.encode("utf-8"), mode=None, receipt=False)


def atomic_bytes(path: Path, data: bytes) -> None:
    """Replace bytes atomically, retaining mode and skipping identical bytes."""
    _atomic_replace(path, data, mode=None, receipt=False)


def atomic_bytes_with_receipt(
    path: Path,
    data: bytes,
    *,
    mode: int | None = None,
) -> dict[str, Any]:
    """Write a new owned inode and return its verified content/identity receipt.

    Unlike the ordinary writers, even identical bytes receive a new inode. Hashing
    is restricted to callers that need a rollback ownership receipt. A failed call
    supplies no ownership proof; callers must not infer it from path bytes alone.
    """
    result = _atomic_replace(path, data, mode=mode, receipt=True)
    assert result is not None
    return result


def atomic_write_with_receipt(
    path: Path,
    text: str,
    *,
    mode: int | None = None,
) -> dict[str, Any]:
    """Text counterpart of atomic_bytes_with_receipt, using exact UTF-8 bytes."""
    return atomic_bytes_with_receipt(path, text.encode("utf-8"), mode=mode)


def atomic_create(path: Path, text: str, *, mode: int = 0o600) -> None:
    """Publish complete local evidence atomically, refusing even concurrent replacement.

    Linking the fully flushed temporary inode provides an atomic no-replace operation.
    The temporary name is then removed; no shared mutable cache or alias is retained.
    Local evidence stays private by default; tracked public records request 0644.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise ValueError(f"Evidence already exists; choose a new path: {path}") from error
    finally:
        temporary.unlink(missing_ok=True)
