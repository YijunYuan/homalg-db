"""Source-faithful dispute lifecycle with guarded confirmation and explicit resolution routes."""

import copy
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg.engine import horizon
from homalg.headers import lex, parse_header
from homalg.human import record_human_change, require_human
from homalg.io import atomic_write
from homalg.leantext import commands
from homalg.nodeio import header_mapping, node_path, replace_header
from homalg.schemas import SchemaStore


def _docstring_marker(source: str, declaration: str, marker: str | None) -> str:
    """Edit the primary docstring, preserving its source-label prefix."""
    command = next((command for command in commands(source) if command.name == declaration), None)
    if command is None or not command.docstring:
        raise ValueError(f"Primary declaration has no source docstring: {declaration}")
    spans = [
        (start, end) for kind, start, end in lex(source) if kind == "doc" and end <= command.start
    ]
    if not spans:
        raise ValueError(f"Cannot locate docstring for {declaration}")
    start, end = spans[-1]
    body = source[start + 3 : end - 2]
    body = re.sub(r"(?m)^\s*(?:STATEMENT|PROOF)-DISPUTED:.*(?:\n|$)", "", body)
    if marker:
        body = body.rstrip() + "\n" + marker + "\n"
    return source[: start + 3] + body + source[end - 2 :]


def _inbox(repo: Path, node_id: str, kind: str, reason: str) -> str:
    """Create the local inbox entry through Horizon's supported command interface."""
    output = horizon(
        repo,
        "inbox",
        "add",
        "--kind",
        "dispute",
        "--to",
        "human",
        "--author",
        "homalg",
        "--node",
        node_id,
        "--body",
        f"{node_id}: {kind} dispute\n\n{reason}",
    )
    match = re.search(r"\bI-[0-9]{4,}\b", output)
    if not match:
        raise RuntimeError("Horizon did not return the new dispute inbox id")
    return match.group()


def open_dispute(
    repo: Path, node_id: str, *, kind: str, reason: str, by: str | None = None
) -> dict[str, Any]:
    """Raise an unconfirmed dispute without weakening the source statement."""
    if kind not in {"statement", "proof"} or not reason.strip():
        raise ValueError("A dispute requires kind statement/proof and a nonempty reason")
    if "/-" in reason or "-/" in reason or "\n" in reason:
        raise ValueError("Use a single-line reason without Lean comment delimiters")
    path = node_path(repo, node_id)
    original = text = path.read_text()
    metadata = header_mapping(text)
    previous = metadata.get("dispute")
    if previous and previous["status"] == "open":
        raise ValueError("This node already has an open dispute")
    if previous:
        metadata.setdefault("dispute_history", []).append(copy.deepcopy(previous))
    dispute = {
        "status": "open",
        "kind": kind,
        "reason": reason,
        "on": datetime.now(UTC).date().isoformat(),
    }
    if by:
        dispute["opened_by"] = by
    metadata["dispute"] = dispute
    if metadata["decls"]:
        text = _docstring_marker(text, metadata["decls"][0], f"{kind.upper()}-DISPUTED: {reason}")
    schemas = SchemaStore(repo / "schema")
    # Validate every prospective source edit before creating an external inbox record.
    replace_header(text, metadata, schemas)
    dispute["inbox"] = _inbox(repo, node_id, kind, reason)
    if path.read_text() != original:
        raise ValueError(f"The node changed; reconcile the new inbox entry {dispute['inbox']}")
    updated = replace_header(text, metadata, schemas)
    atomic_write(path, updated)
    return dispute


def confirm_dispute(repo: Path, node_id: str, *, by: str) -> dict[str, Any]:
    """Human confirmation makes a raised statement/proof dispute a headline error."""
    path = node_path(repo, node_id)
    text = path.read_text()
    metadata = header_mapping(text)
    dispute = metadata.get("dispute", {})
    if dispute.get("status") != "open" or dispute.get("confirmed_by"):
        raise ValueError("Only an unconfirmed open dispute can be confirmed")
    require_human(f"dispute confirm {node_id}", repo, details=json.dumps(dispute, indent=2))
    if path.read_text() != text:
        raise ValueError("The node changed while confirmation was pending")
    dispute.update(confirmed_by=by, confirmed_on=datetime.now(UTC).date().isoformat())
    atomic_write(path, replace_header(text, metadata, SchemaStore(repo / "schema")))
    record_human_change(repo, f"dispute confirm {node_id}", [path])
    return dispute


def resolve_dispute(repo: Path, node_id: str, *, via: str, by: str, note: str) -> dict[str, Any]:
    """Resolve by erratum, proof route, or withdrawal of an unconfirmed report."""
    if not note.strip():
        raise ValueError("Resolution requires a note explaining the evidence")
    path = node_path(repo, node_id)
    text = path.read_text()
    header = parse_header(text)
    metadata = header_mapping(text, header)
    dispute = metadata.get("dispute", {})
    deviations = {item["kind"] for item in metadata["fidelity"].get("deviations", [])}
    if dispute.get("status") != "open":
        raise ValueError("There is no open dispute to resolve")
    if via == "withdrawn":
        if dispute.get("confirmed_by"):
            raise ValueError("A confirmed dispute cannot be withdrawn")
    elif via == "erratum":
        if "erratum" not in deviations or (
            dispute["kind"] == "statement" and not header.sections.get("Statement (corrected)")
        ):
            raise ValueError("An erratum deviation and corrected statement are required")
    elif via == "proof-route":
        if dispute["kind"] != "proof" or "proof-route" not in deviations:
            raise ValueError("A proof-route deviation can resolve only a proof dispute")
    else:
        raise ValueError("Unknown dispute resolution route")
    require_human(
        f"dispute resolve {node_id}",
        repo,
        details=json.dumps({"dispute": dispute, "via": via, "note": note}, indent=2),
    )
    if path.read_text() != text:
        raise ValueError("The node changed while resolution was pending")
    dispute["status"] = "resolved"
    dispute["resolution"] = {
        "via": via,
        "by": by,
        "on": datetime.now(UTC).date().isoformat(),
        "note": note,
    }
    if metadata["decls"]:
        text = _docstring_marker(text, metadata["decls"][0], None)
    atomic_write(path, replace_header(text, metadata, SchemaStore(repo / "schema")))
    record_human_change(repo, f"dispute resolve {node_id}", [path])
    return dispute
