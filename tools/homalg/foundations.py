"""Draft, inspect and individually confirm a document's explicit foundation boundary."""

import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from homalg.documents import read_document, write_metadata
from homalg.human import record_human_change, require_human
from homalg.review_policy import agent_review_record, foundation_hash, require_report_provenance
from homalg.schemas import SchemaStore, load_yaml


def draft(repo: Path, key: str) -> list[dict[str, Any]]:
    """Copy suggestions into an empty boundary, preserving existing evidence and approvals."""
    document = read_document(repo, key)
    if document.get("foundations"):
        return document["foundations"]
    template = load_yaml((repo / "taxonomy/foundations-template.yaml").read_text())
    entries = [copy.deepcopy(entry) | {"status": "draft"} for entry in template["entries"]]
    document["foundations"] = entries
    write_metadata(
        repo / "literature" / key / "document.yaml",
        document,
        "document.schema.json",
        SchemaStore(repo / "schema"),
    )
    return entries


def confirm(repo: Path, key: str, index: int, *, by: str) -> dict[str, Any]:
    """Approve precisely one proposed, evidenced entry after the shared human guard."""
    document = read_document(repo, key)
    entries = document.get("foundations", [])
    if index < 1 or index > len(entries):
        raise ValueError(f"Foundation index must be between 1 and {len(entries)}")
    entry = entries[index - 1]
    if entry["status"] != "proposed" or not entry.get("evidence", "").strip():
        raise ValueError("Only a proposed entry with source evidence can be confirmed")
    require_human(
        f"foundations confirm {key} {index}",
        repo,
        details=json.dumps(entry, indent=2, ensure_ascii=False),
    )
    # Compare after interactive approval; another process may have modified the document.
    current = read_document(repo, key)
    if current != document:
        raise ValueError("The foundation boundary changed while confirmation was pending")
    entry["status"] = "confirmed"
    entry["confirmed_by"] = by
    path = repo / "literature" / key / "document.yaml"
    write_metadata(path, document, "document.schema.json", SchemaStore(repo / "schema"))
    record_human_change(repo, f"foundations confirm {key} {index}", [path])
    return entry


def review(
    repo: Path,
    key: str,
    index: int,
    *,
    by: str,
    session: str,
    author_session: str,
    report: Path | None = None,
    note: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Confirm one source-evidenced foundation through an explicitly independent agent review."""
    from homalg.review import review_blocks

    record = agent_review_record(
        repo,
        by=by,
        session=session,
        author_session=author_session,
        note=note,
        now=now,
    )
    document = read_document(repo, key)
    entries = document.get("foundations", [])
    if index < 1 or index > len(entries):
        raise ValueError(f"Foundation index must be between 1 and {len(entries)}")
    entry = entries[index - 1]
    if entry.get("confirmed_by"):
        raise ValueError("An agent review cannot replace an existing human foundation confirmation")
    if entry["status"] not in {"proposed", "confirmed"} or not entry.get("evidence", "").strip():
        raise ValueError("Only a proposed entry with source evidence can be reviewed")
    report = report or repo / "literature" / key / "reviews/foundations.md"
    report = report if report.is_absolute() else repo / report
    text = report.read_text()
    require_report_provenance(text, session=session, author_session=author_session)
    blocks = review_blocks(text)
    block = blocks.get("source-fidelity", {})
    if (
        block.get("status") != "satisfactory"
        or not block.get("verdict")
        or "|" not in block.get("body", "")
        or entry["notion"].casefold() not in block.get("body", "").casefold()
    ):
        raise ValueError(
            "Foundation report needs a satisfactory comparison table naming this notion"
        )
    if any(value["status"] != "satisfactory" for value in blocks.values()):
        raise ValueError("Unresolved review disagreement requires adjudication before confirmation")
    record["content_sha256"] = foundation_hash(entry)
    if read_document(repo, key) != document or report.read_text() != text:
        raise ValueError(
            "Foundation content or review report changed while review was being recorded"
        )
    entry["status"] = "confirmed"
    entry["confirmation"] = record
    path = repo / "literature" / key / "document.yaml"
    write_metadata(path, document, "document.schema.json", SchemaStore(repo / "schema"))
    return entry
