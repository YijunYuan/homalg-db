"""Statement-lock review evidence, source hashes and reopening diagnostics."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg.headers import parse_header
from homalg.human import check_human_session, record_human_change, require_human, require_idle
from homalg.io import atomic_write
from homalg.leantext import commands, statement_hashes
from homalg.nodeio import header_mapping, node_path, replace_header
from homalg.review_policy import (
    agent_review_record,
    agent_reviews_allowed,
    require_report_provenance,
)
from homalg.schemas import SchemaStore

REVIEW_STATUSES = {"satisfactory", "partial", "mismatch", "unverified", "needs-adjudication"}


def review_blocks(text: str) -> dict[str, dict[str, str]]:
    """Read each kind's latest verdict; earlier reviews cannot mask a later failure."""
    headings = list(re.finditer(r"(?m)^##\s+(source-fidelity|honesty)\s+[—–-]\s+(.+)$", text))
    output = {}
    for position, heading in enumerate(headings):
        end = headings[position + 1].start() if position + 1 < len(headings) else len(text)
        body = text[heading.end() : end]
        status = re.search(r"(?m)^Status:\s*(\S+)\s*$", body)
        verdict = re.search(r"(?m)^Verdict:\s*(.+)$", body)
        output[heading.group(1)] = {
            "status": status.group(1)
            if status and status.group(1) in REVIEW_STATUSES
            else "unverified",
            "verdict": verdict.group(1) if verdict else "",
            "heading": heading.group(2),
            "body": body,
        }
    return output


def current_declarations(repo: Path, node_id: str) -> dict[str, dict[str, Any]]:
    """Read exported declaration facts; callers must check source freshness."""
    key = node_id.split(".", 1)[0]
    path = repo / "literature" / key / "nodes.json"
    nodes = json.loads(path.read_text())["nodes"]
    node = next((node for node in nodes if node["id"] == node_id), None)
    if node is None or node["derived"] is None:
        raise ValueError(f"{node_id}: export Lean before reviewing fidelity")
    return {declaration["name"]: declaration for declaration in node["derived"]["decl_info"]}


def lock_changes(
    text: str, authored: dict[str, Any], declarations: dict[str, dict[str, Any]]
) -> list[dict[str, str]]:
    """Detect statement/type changes as errors and semantic closure changes as warnings."""
    reviewed = authored.get("fidelity", {}).get("reviewed")
    if not reviewed:
        return []
    current = statement_hashes(text)
    locked = reviewed["decl_hashes"]
    changes = []
    names = set(authored["decls"]) | set(locked)
    for name in sorted(names):
        saved, declaration = locked.get(name, {}), declarations.get(name, {})
        if (
            name not in authored["decls"]
            or current.get(name) != saved.get("statement_sha256")
            or declaration.get("type_hash") != saved.get("type_hash")
        ):
            changes.append(
                {"decl": name, "severity": "error", "reason": "Statement or type changed"}
            )
        elif declaration.get("meaning_hash") != saved.get("meaning_hash"):
            changes.append(
                {"decl": name, "severity": "warning", "reason": "A referenced definition changed"}
            )
    return changes


def review_fidelity(
    repo: Path,
    node_id: str,
    *,
    by: str,
    session: str | None = None,
    author_session: str | None = None,
    human: bool = False,
    note: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Lock only source-aligned, satisfactorily reviewed declarations from a fresh export."""
    if bool(session) == human:
        raise ValueError("Choose exactly one of --session or --human")
    if human:
        check_human_session(f"review-fidelity {node_id}", repo)
    path = node_path(repo, node_id)
    source = path.read_text()
    header = parse_header(source)
    authored = header.metadata
    if not authored["decls"]:
        raise ValueError("A planned/informal node has no statements to lock")
    if not human and authored["fidelity"].get("reviewed", {}).get("kind") == "human":
        raise ValueError("An agent review cannot replace an existing human fidelity record")
    if not human and authored.get("dispute", {}).get("status") == "open":
        raise ValueError(
            "An unresolved mathematical/source dispute requires adjudication before locking"
        )
    independent = not human and agent_reviews_allowed(repo)
    agent_record = None
    if independent:
        agent_record = agent_review_record(
            repo,
            by=by,
            session=session or "",
            author_session=author_session or "",
            now=now,
        )
        if authored["fidelity"]["status"] == "deviates" and any(
            not item.get("what", "").strip() or not item.get("why", "").strip()
            for item in authored["fidelity"].get("deviations", [])
        ):
            raise ValueError("Agent review requires every deviation to be explicitly explained")
    elif authored["fidelity"]["status"] in {"foundation", "deviates"} and not human:
        raise ValueError(
            "Foundation and deviating statements require a human review or enabled policy"
        )
    key, local = node_id.split(".", 1)
    reviews = repo / "literature" / key / "reviews" / f"{local}.md"
    report_text = reviews.read_text()
    if independent:
        require_report_provenance(
            report_text,
            session=session or "",
            author_session=author_session or "",
        )
    blocks = review_blocks(report_text)
    required = ["source-fidelity"]
    if "honesty" in blocks or any(
        command.kind in {"structure", "class", "instance"} for command in commands(source)
    ):
        required.append("honesty")
    for kind in required:
        block = blocks.get(kind, {})
        if block.get("status") != "satisfactory" or not block.get("verdict"):
            raise ValueError(f"Latest {kind} review must have Status: satisfactory and a Verdict")
        if not re.search(r"(?m)^\|.*\|", block["body"]):
            raise ValueError(f"Latest {kind} review must include its comparison table")
    # A fresh build is mandatory: locks must refer to compiled current statements.
    from homalg.leanexport import export_lean

    export_lean(repo, doc=key)
    declarations = current_declarations(repo, node_id)
    hashes = statement_hashes(source)
    if any(name not in hashes or name not in declarations for name in authored["decls"]):
        raise ValueError("A main declaration is missing from the source analysis or Lean export")
    lock = {
        "by": by,
        "kind": "human" if human else "agent",
        "status": "satisfactory",
        "on": (now or datetime.now(UTC)).date().isoformat(),
        "decl_hashes": {
            name: {
                "statement_sha256": hashes[name],
                "type_hash": declarations[name]["type_hash"],
                "meaning_hash": declarations[name]["meaning_hash"],
            }
            for name in authored["decls"]
        },
    }
    if session:
        lock["session"] = session
    if agent_record:
        lock["author_session"] = agent_record["author_session"]
    if note:
        lock["note"] = note
    if human:
        require_human(
            f"review-fidelity {node_id}",
            repo,
            details=json.dumps({"statement": header.sections["Statement"], "lock": lock}, indent=2),
        )
    current = path.read_text()
    if current != source or reviews.read_text() != report_text:
        raise ValueError(
            "The node or report changed during review; review the new source before locking"
        )
    metadata = header_mapping(source, header)
    metadata["fidelity"]["reviewed"] = lock
    updated = replace_header(source, metadata, SchemaStore(repo / "schema"))
    atomic_write(path, updated)
    if human:
        record_human_change(repo, f"review-fidelity {node_id}", [path])
    return lock


def relock_all(repo: Path, *, reason: str) -> dict[str, list[str]]:
    """Refresh toolchain-sensitive hashes only for interfaces whose source locks still match."""
    if not reason.strip():
        raise ValueError("Relocking requires a reason")
    require_idle(repo)
    from homalg.leanexport import export_lean
    from homalg.repository import documents, node_paths

    export_lean(repo)
    schemas = SchemaStore(repo / "schema")
    updates = {}
    result: dict[str, list[str]] = {"updated": [], "changed_statements": []}
    for path in node_paths(repo, documents(repo)):
        source = path.read_text()
        metadata = header_mapping(source)
        reviewed = metadata["fidelity"].get("reviewed")
        if not reviewed:
            continue
        hashes = statement_hashes(source)
        if set(reviewed["decl_hashes"]) != set(metadata["decls"]) or any(
            hashes.get(name) != lock["statement_sha256"]
            for name, lock in reviewed["decl_hashes"].items()
        ):
            result["changed_statements"].append(metadata["id"])
            continue
        declarations = current_declarations(repo, metadata["id"])
        for name, lock in reviewed["decl_hashes"].items():
            if name not in declarations:
                raise ValueError(f"Missing declaration while relocking: {name}")
            lock["type_hash"] = declarations[name]["type_hash"]
            lock["meaning_hash"] = declarations[name]["meaning_hash"]
        updates[path] = replace_header(source, metadata, schemas)
        result["updated"].append(metadata["id"])
    for path, source in updates.items():
        atomic_write(path, source)
        key, local = path.parent.name, path.stem
        review_path = repo / "literature" / key / "reviews" / f"{local}.md"
        previous = review_path.read_text() if review_path.exists() else ""
        atomic_write(
            review_path, previous.rstrip() + f"\n\nRelocked {datetime.now(UTC).date()}: {reason}\n"
        )
    return result


def unlock_fidelity(repo: Path, node_id: str, *, by: str, reason: str) -> None:
    """Remove an obsolete lock while preserving an append-only review trail."""
    if not reason.strip():
        raise ValueError("Unlocking requires a reason")
    path = node_path(repo, node_id)
    text = path.read_text()
    metadata = header_mapping(text)
    metadata["fidelity"].pop("reviewed", None)
    updated = replace_header(text, metadata, SchemaStore(repo / "schema"))
    doc, local = node_id.split(".", 1)
    review_path = repo / "literature" / doc / "reviews" / f"{local}.md"
    previous = review_path.read_text() if review_path.exists() else ""
    atomic_write(
        review_path,
        previous.rstrip() + f"\n\nUnlocked {datetime.now(UTC).date()} by {by}: {reason}\n",
    )
    atomic_write(path, updated)
