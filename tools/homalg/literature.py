"""Private source checkout and hash-verified PDF rendering, without OCR."""

import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from homalg.documents import dump_metadata, parse_metadata, read_document
from homalg.io import atomic_bytes, atomic_write


def run_git(root: Path, *arguments: str) -> str:
    """Run git without shell interpolation and report failures explicitly."""
    result = subprocess.run(
        ["git", "-C", str(root), *arguments], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise RuntimeError(f"Private literature git operation failed: {result.stderr.strip()}")
    return result.stdout.strip()


def private_root(repo: Path) -> Path:
    """Require the configured local private checkout, never an arbitrary public directory."""
    root = repo / "literature/.private"
    if not (root / ".git").exists():
        raise ValueError(
            "Private literature is unavailable. Configure its URL and run make literature."
        )
    return root


def source_directory(repo: Path, key: str) -> Path:
    """Check document identity and keep source paths inside the private checkout."""
    read_document(repo, key)
    root = private_root(repo).resolve()
    target = root / key
    if not target.resolve().is_relative_to(root):
        raise ValueError("Private source directory escapes its checkout")
    return target


def references_link(repo: Path) -> Path:
    """Connect Horizon's reference path to the existing private checkout."""
    root = private_root(repo)
    link = repo / "references"
    if link.exists() or link.is_symlink():
        if not link.is_symlink() or link.resolve() != root.resolve():
            raise ValueError("references already exists and is not the private literature link")
    else:
        link.symlink_to("literature/.private", target_is_directory=True)
    return link


def ignore_renders(root: Path) -> None:
    """Ensure locally rendered page images can never enter ordinary private commits."""
    ignored = root / ".gitignore"
    lines = ignored.read_text().splitlines() if ignored.exists() else []
    for pattern in ("*/pages/", "*.tmp"):
        if pattern not in lines:
            lines.append(pattern)
    atomic_write(ignored, "\n".join(lines) + "\n")


def checkout(repo: Path) -> Path:
    """Clone or fast-forward the private source repository from local configuration."""
    config = repo / ".homalg/literature-url"
    url = os.environ.get("HOMALG_LITERATURE_REPO", "").strip()
    if not url and config.exists():
        url = config.read_text().splitlines()[0].strip()
    if not url:
        raise ValueError(
            "Set HOMALG_LITERATURE_REPO to the private git URL, or put it on the first line "
            "of .homalg/literature-url (ignored by git)."
        )
    if url.startswith("-"):
        raise ValueError("Invalid literature git URL")
    root = repo / "literature/.private"
    if root.exists():
        private_root(repo)
        if run_git(root, "status", "--porcelain"):
            raise ValueError("Private checkout has local changes; commit them before pulling")
        run_git(root, "pull", "--ff-only")
    else:
        run_git(repo, "clone", "--", url, str(root))
    ignore_renders(root)
    references_link(repo)
    return root


def pdf_path(repo: Path, key: str) -> Path:
    """Resolve the public metadata's basename inside the private document directory."""
    document = read_document(repo, key)
    if "pdf" not in document:
        raise ValueError("Synthetic documents do not have PDFs")
    name = document["pdf"]["file"]
    if Path(name).name != name or name in {"", ".", ".."} or "\\" in name:
        raise ValueError("pdf.file must be a plain filename")
    directory = source_directory(repo, key)
    path = directory / name
    if not path.resolve().is_relative_to(directory.resolve()):
        raise ValueError("PDF path escapes its private document directory")
    return path


def file_hash(path: Path) -> str:
    """Hash binary source bytes without interpreting PDF text."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def add_pdf(repo: Path, key: str, source: Path) -> Path:
    """Copy an exact registered PDF into the private checkout; large files require LFS."""
    document = read_document(repo, key)
    target = pdf_path(repo, key)
    if file_hash(source) != document["pdf"]["sha256"]:
        raise ValueError("PDF SHA-256 differs from document.yaml; no source was copied")
    if target.exists() and file_hash(target) != document["pdf"]["sha256"]:
        raise ValueError("A different private PDF already exists; refusing to overwrite it")
    if source.stat().st_size > 50 * 1024 * 1024:
        root = private_root(repo)
        run_git(root, "lfs", "install", "--local")
        run_git(root, "lfs", "track", str(target.relative_to(root)))
    atomic_bytes(target, source.read_bytes())
    ignore_renders(private_root(repo))
    references_link(repo)
    return target


def page_range(value: str | None, total: int, *, maximum: int | None = None) -> list[int]:
    """Parse PDF page indices, rejecting reversed, empty and out-of-range input."""
    pages: set[int] = set()
    for part in (value or f"1-{total}").split(","):
        if not re.fullmatch(r"[0-9]+(?:-[0-9]+)?", part.strip()):
            raise ValueError("Pages must be PDF indices such as 1-5 or 2,4-6")
        limits = [int(token) for token in part.strip().split("-")]
        first, last = limits[0], limits[-1]
        if not 1 <= first <= last <= total or last > 9999:
            raise ValueError(f"Page range must lie within 1-{min(total, 9999)}")
        pages.update(range(first, last + 1))
    if maximum and len(pages) > maximum:
        raise ValueError(f"Process at most {maximum} pages per transcription batch")
    return sorted(pages)


def update_manifest(repo: Path, key: str, document: dict[str, Any]) -> None:
    """Register page anchors while preserving other reference entries."""
    root = private_root(repo)
    path = root / "manifest.yaml"
    manifest = parse_metadata(path.read_text()) if path.exists() else {"references": []}
    entries = manifest.setdefault("references", [])
    if not isinstance(entries, list):
        raise ValueError("Private manifest.references must be a list")
    entry = next((item for item in entries if item.get("slug") == key), None)
    if entry is None:
        entry = {"slug": key}
        entries.append(entry)
    pdf = document["pdf"]
    entry.update(
        title=document["title"],
        source=next((item["url"] for item in pdf.get("sources", [])), "privately supplied"),
        status="available",
        files=[f"{key}/{pdf['file']}"],
        read=f"Page anchors {key}:page-NNNN (PDF index). page_offset: {pdf.get('page_offset', 0)}",
    )
    atomic_write(path, dump_metadata(manifest))


def ingest_pdf(repo: Path, key: str, *, pages: str | None = None) -> dict[str, Any]:
    """Render 200 dpi images and navigation text after validating source identity."""
    try:
        import pymupdf
    except ImportError as exc:
        raise ValueError(
            "Install ingestion support: uv sync --project tools --extra ingest"
        ) from exc
    document = read_document(repo, key)
    path = pdf_path(repo, key)
    digest = file_hash(path)
    if digest != document["pdf"]["sha256"]:
        raise ValueError("Private PDF SHA-256 differs from document.yaml")
    ignore_renders(private_root(repo))
    if not (path.parent / "pages").resolve().is_relative_to(path.parent.resolve()):
        raise ValueError("Rendered page directory escapes its private document")
    with pymupdf.open(path) as pdf:
        if document["pdf"].get("pages", len(pdf)) != len(pdf):
            raise ValueError("PDF page count differs from document.yaml")
        selected = page_range(pages, len(pdf))
        target = repo / "literature" / key / "ingest.yaml"
        metadata = parse_metadata(target.read_text()) if target.exists() else {}
        if metadata.get("sha256", digest) != digest:
            metadata = {}
        counts = metadata.setdefault("page_characters", {})
        for number in selected:
            page = pdf[number - 1]
            text = page.get_text("text")
            counts[f"{number:04}"] = len(text.strip())
            atomic_bytes(
                path.parent / "pages" / f"page-{number:04}.png",
                page.get_pixmap(dpi=200, alpha=False).tobytes("png"),
            )
            atomic_write(repo / "literature" / key / "text" / f"page-{number:04}.txt", text)
        maximum = max(counts.values(), default=0)
        metadata.update(
            sha256=digest,
            pages=len(pdf),
            page_offset=document["pdf"].get("page_offset", 0),
            text_layer="none" if maximum == 0 else "sparse" if maximum < 100 else "present",
        )
        atomic_write(target, dump_metadata(metadata))
    update_manifest(repo, key, document)
    references_link(repo)
    return {"doc_key": key, "rendered_pages": selected, **metadata}
