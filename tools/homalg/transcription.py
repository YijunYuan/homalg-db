"""Page-level visual transcription evidence with hash-aware review states."""

import fcntl
import re
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg.documents import read_document, read_metadata, write_metadata
from homalg.human import require_human
from homalg.literature import file_hash, page_range, source_directory
from homalg.review import REVIEW_STATUSES
from homalg.schemas import SchemaStore


@contextmanager
def page_lock(repo: Path, key: str) -> Iterator[None]:
    """Serialize metadata edits without placing lock artifacts in private source history."""
    path = repo / ".homalg/locks" / f"transcription-{key}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def load(repo: Path, key: str) -> tuple[Path, dict[str, Any]]:
    """Read validated page evidence bound to the registered PDF identity."""
    document = read_document(repo, key)
    if "pdf" not in document or "pages" not in document["pdf"]:
        raise ValueError("Transcription requires a registered PDF with a page count")
    path = source_directory(repo, key) / "transcription.yaml"
    value = (
        read_metadata(path, "transcription.schema.json", SchemaStore(repo / "schema"))
        if path.exists()
        else {
            "schema_version": 1,
            "doc_key": key,
            "pdf_sha256": document["pdf"]["sha256"],
            "pages": {},
        }
    )
    if value["pdf_sha256"] != document["pdf"]["sha256"] or value["doc_key"] != key:
        raise ValueError("Transcription metadata belongs to a different PDF/document")
    total = document["pdf"]["pages"]
    if total > 9999 or any(not 1 <= int(page) <= total for page in value["pages"]):
        raise ValueError("Transcription page indices exceed the registered PDF")
    for number in range(1, total + 1):
        value["pages"].setdefault(f"{number:04}", {"status": "todo"})
    return path, value


def save(repo: Path, path: Path, data: dict[str, Any]) -> None:
    """Validate and atomically publish page states."""
    write_metadata(path, data, "transcription.schema.json", SchemaStore(repo / "schema"))


def current_page(path: Path, number: int) -> tuple[Path, str]:
    """Require a private page file with the visual-transcriber provenance header."""
    page = path.parent / "tex" / f"page-{number:04}.tex"
    if not page.resolve().is_relative_to(path.parent.resolve()):
        raise ValueError("Transcription file escapes its private document")
    text = page.read_text()
    for field in ("source", "pdf_page", "retrieved", "transcribed_by"):
        match = re.search(rf"(?m)^%\s*{field}:\s*(\S[^\n]*)$", text)
        if not match:
            raise ValueError(f"{page.name}: missing %{field}: provenance header")
        if field == "pdf_page" and match.group(1).strip() not in {str(number), f"{number:04}"}:
            raise ValueError(f"{page.name}: pdf_page header does not match its filename")
    if not re.sub(r"(?m)^%.*$", "", text).strip():
        raise ValueError(f"{page.name}: empty transcription")
    return page, file_hash(page)


def reconcile(path: Path, data: dict[str, Any]) -> list[str]:
    """Reopen reviewed pages whose bytes no longer match their satisfactory evidence."""
    changed = []
    for number, record in data["pages"].items():
        page = path.parent / "tex" / f"page-{number}.tex"
        digest = file_hash(page) if page.is_file() else None
        if record["status"] == "reviewed" and digest != record.get("file_sha256"):
            record["status"] = "transcribed"
            changed.append(number)
        elif record["status"] == "reviewed":
            reviews = record.get("reviews", [])
            if (
                not reviews
                or reviews[-1]["status"] != "satisfactory"
                or reviews[-1]["file_sha256"] != digest
            ):
                record["status"] = "transcribed"
                changed.append(number)
    return changed


def status(repo: Path, key: str, *, persist: bool = True) -> dict[str, Any]:
    """Report current hash-checked states and pending ranges; optionally persist reopenings."""
    with page_lock(repo, key):
        path, data = load(repo, key)
        changed = reconcile(path, data)
        if persist and changed:
            save(repo, path, data)
        counts = dict.fromkeys(("todo", "transcribed", "reviewed", "disputed"), 0)
        counts.update(Counter(record["status"] for record in data["pages"].values()))
        return {
            "doc_key": key,
            "counts": counts,
            "changed_after_review": changed,
            "pending_review": [
                number
                for number, record in data["pages"].items()
                if record["status"] == "transcribed"
            ],
            "pages": data["pages"],
        }


def land(
    repo: Path,
    key: str,
    *,
    pages: str,
    session: str,
    engine: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Record delivered page files while preserving prior review history."""
    if not session.strip():
        raise ValueError("Landing requires a transcription session id")
    with page_lock(repo, key):
        path, data = load(repo, key)
        selected = page_range(pages, len(data["pages"]), maximum=5)
        hashes = {number: current_page(path, number)[1] for number in selected}
        if any(data["pages"][f"{number:04}"]["status"] == "disputed" for number in selected):
            raise ValueError("Disputed pages require human resolution before being landed again")
        for number, digest in hashes.items():
            author = {"session": session, "at": datetime.now(UTC).isoformat()}
            if engine:
                author["engine"] = engine
            if model:
                author["model"] = model
            data["pages"][f"{number:04}"].update(
                status="transcribed", transcribed_by=author, file_sha256=digest
            )
        save(repo, path, data)
    return {"doc_key": key, "landed": selected}


def parse_finding(text: str) -> dict[str, str]:
    """Parse kind: where: severity: note without truncating colons within the note."""
    parts = [part.strip() for part in text.split(":", 3)]
    if len(parts) != 4 or not all(parts):
        raise ValueError("Use finding 'kind: where: error|warning: note'")
    return dict(zip(("kind", "where", "severity", "note"), parts, strict=True))


def review(
    repo: Path,
    key: str,
    *,
    pages: str,
    verdict: str,
    by: str,
    findings: tuple[str, ...] = (),
    human: bool = False,
    note: str = "",
) -> dict[str, Any]:
    """Append review evidence; satisfactory evidence applies only to exact delivered bytes."""
    if verdict not in REVIEW_STATUSES or not by.strip():
        raise ValueError("A known review status and reviewer identity are required")
    path, snapshot = load(repo, key)
    selected = page_range(pages, len(snapshot["pages"]), maximum=1 if human else 5)
    if human:
        if not note.strip() or snapshot["pages"][f"{selected[0]:04}"]["status"] != "disputed":
            raise ValueError("Human resolution requires a disputed page and an explanatory note")
        require_human(
            f"transcription resolve {key}", repo, details=f"Pages {pages}: {verdict}\n{note}"
        )
    with page_lock(repo, key):
        path, data = load(repo, key)
        if human and data != snapshot:
            raise ValueError("Transcription changed while human confirmation was pending")
        for number in selected:
            record = data["pages"][f"{number:04}"]
            _, digest = current_page(path, number)
            if "transcribed_by" not in record or record["status"] == "todo":
                raise ValueError("Land page files before reviewing them")
            if not human and by == record["transcribed_by"]["session"]:
                raise ValueError("Transcription review requires a different reviewer session")
            if record["status"] == "disputed" and not human:
                raise ValueError("Only a human can resolve a disputed page")
            if digest != record.get("file_sha256") and not human:
                raise ValueError("Page bytes changed since landing; land them again before review")
            evidence = {
                "status": verdict,
                "by": by,
                "at": datetime.now(UTC).isoformat(),
                "file_sha256": digest,
                "kind": "human" if human else "agent",
                "findings": [parse_finding(value) for value in findings],
            }
            if note:
                evidence["findings"].append(
                    {
                        "kind": "other",
                        "where": f"page-{number:04}",
                        "severity": "warning",
                        "note": note,
                    }
                )
            record.setdefault("reviews", []).append(evidence)
            record["file_sha256"] = digest
            record["status"] = (
                "reviewed"
                if verdict == "satisfactory"
                else "disputed"
                if verdict == "needs-adjudication"
                else "transcribed"
            )
        # Validate before requesting a local human adjudication entry.
        errors = SchemaStore(repo / "schema").validate(data, "transcription.schema.json")
        if errors:
            raise ValueError(errors[0].message)
        if verdict == "needs-adjudication":
            from homalg.engine import horizon

            horizon(
                repo,
                "inbox",
                "add",
                "--kind",
                "conversation",
                "--to",
                "human",
                "--author",
                "homalg",
                "--body",
                f"{key}: transcription adjudication required\n\n"
                f"Review the unresolved source disagreement on PDF pages {pages}. "
                "The private transcription metadata records the reviewer and reason.",
            )
        save(repo, path, data)
    return {"doc_key": key, "reviewed_pages": selected, "review_status": verdict}
