"""Dependency maintenance, pruning, status previews and review summaries."""

import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg.documents import dump_metadata
from homalg.headers import code_only, imports_of, parse_header
from homalg.io import atomic_write
from homalg.leantext import sorry_count
from homalg.nodeio import header_mapping, node_path, replace_header
from homalg.repository import documents, node_paths
from homalg.schemas import SchemaStore, load_yaml
from homalg.status import compute_status, status_counts


def fix_deps(repo: Path, key: str, *, output: Path | None = None) -> list[str]:
    """Add verified missing dependencies, keeping statement and proof classification distinct."""
    data = json.loads((repo / "literature" / key / "nodes.json").read_text())
    updates = {}
    schemas = SchemaStore(repo / "schema")
    for node in data["nodes"]:
        derived = node["derived"]
        path = node_path(repo, node["id"])
        source = path.read_text()
        if (
            derived is None
            or hashlib.sha256(path.read_bytes()).hexdigest() != derived["file"]["sha256"]
        ):
            raise ValueError("Dependencies are stale; export Lean before fixing metadata")
        metadata = header_mapping(source)
        if not derived["deps_diff"]["verified_not_declared"]:
            continue
        for dependency in derived["deps_diff"]["verified_not_declared"]:
            kind = "statement" if dependency in derived["verified_deps"]["statement"] else "proof"
            metadata["deps"][kind] = sorted(set(metadata["deps"][kind]) | {dependency})
        destination = output / path.relative_to(repo) if output else path
        updates[destination] = replace_header(source, metadata, schemas)
    for path, text in updates.items():
        atomic_write(path, text)
    return [str(path) for path in updates]


def unused_imports(repo: Path, selected: tuple[str, ...] = ()) -> list[dict[str, str]]:
    """Report unused node and provably redundant Mathlib imports, preserving source routes."""
    output = []
    for key in documents(repo, selected):
        data = json.loads((repo / "literature" / key / "nodes.json").read_text())
        for node in data["nodes"]:
            derived = node["derived"]
            if derived is None:
                raise ValueError("Export Lean before inspecting unused imports")
            source_path = node_path(repo, node["id"])
            source = source_path.read_text()
            if hashlib.sha256(source_path.read_bytes()).hexdigest() != derived["file"]["sha256"]:
                raise ValueError("Dependencies are stale; export Lean before inspecting imports")
            keep = set(
                sum(derived["verified_deps"].values(), [])
                + sum(node["authored"]["deps"].values(), [])
            )
            for dependency in derived["imports"]["nodes"]:
                if dependency not in keep:
                    output.append(
                        {
                            "node": node["id"],
                            "module": "HomAlg." + dependency,
                            "reason": "Neither verified nor declared as a source dependency",
                        }
                    )
            for module in redundant_mathlib_imports(repo, source):
                output.append(
                    {
                        "node": node["id"],
                        "module": module,
                        "reason": "The complete source compiles with this import removed",
                    }
                )
    return output


def redundant_mathlib_imports(repo: Path, source: str) -> list[str]:
    """Probe copies under the shared lock so tactic/notation/instance imports are not guessed."""
    from homalg.leanexport import ExternalToolError, workspace_lock

    candidates = list(
        re.finditer(r"(?m)^[ \t]*import[ \t]+(Mathlib\.[\w.]+)[ \t]*$", code_only(source))
    )
    if not candidates:
        return []
    output = []
    (repo / "build").mkdir(exist_ok=True)
    with (
        workspace_lock(repo),
        tempfile.TemporaryDirectory(prefix="imports-", dir=repo / "build") as directory,
    ):
        path = Path(directory) / "Probe.lean"
        command = [
            "lake",
            "env",
            "lean",
            "-DautoImplicit=false",
            "-DrelaxedAutoImplicit=false",
            str(path),
        ]
        for match in candidates:
            path.write_text(source[: match.start()] + source[match.end() :])
            try:
                result = subprocess.run(
                    command, cwd=repo, capture_output=True, text=True, check=False, timeout=1800
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                raise ExternalToolError(command, str(error)) from error
            if result.returncode == 0:
                output.append(match[1])
            elif result.returncode != 1:
                raise ExternalToolError(command, result.stdout + result.stderr, result.returncode)
    return output


def prune_check(
    repo: Path,
    node_id: str,
    *,
    apply: bool = False,
    moved_to: str | None = None,
    by: str | None = None,
    reason: str = "No remaining users",
) -> dict[str, Any]:
    """Delete only an unreferenced auxiliary/cited node, leaving a permanent id tombstone."""
    path = node_path(repo, node_id)
    local = path.stem
    if not local.startswith(("Aux_", "Cited_")):
        raise ValueError("Only Aux_ and Cited_ nodes can be pruned; bridges are retained")
    source = path.read_text()
    references = []
    for other in node_paths(repo, documents(repo)):
        if other == path:
            continue
        text = other.read_text()
        metadata = parse_header(text).metadata
        ids = sum(metadata.get("deps", {}).values(), [])
        ids += [metadata.get("aux", {}).get("parent"), metadata.get("mathlib", {}).get("bridge")]
        ids += [relation["target"] for relation in metadata.get("related", [])]
        if node_id in ids or f"HomAlg.{node_id}" in imports_of(text):
            references.append(other.relative_to(repo).as_posix())
    for other in (repo / "taxonomy/relations").glob("[!_]*.yaml"):
        for relation in load_yaml(other.read_text())["relations"]:
            if node_id in (relation["source"], relation["target"], relation.get("bridge")):
                references.append(other.relative_to(repo).as_posix())
    result = {
        "node": node_id,
        "can_prune": not references,
        "references": sorted(set(references)),
        "deleted": False,
    }
    if not apply:
        return result
    if references:
        raise ValueError(f"Node is still referenced: {result['references']}")
    if moved_to and (moved_to == node_id or not node_path(repo, moved_to).exists()):
        raise ValueError("Migration target must be a different existing node")
    if by is None:
        from homalg.collaboration import Client

        by = Client(repo).gh("api", "user", "--jq", ".login").strip()
    retired_path = repo / "literature" / path.parent.name / "retired.yaml"
    retired = (
        load_yaml(retired_path.read_text())
        if retired_path.exists()
        else {"schema_version": 1, "retired": []}
    )
    entry = {
        "id": node_id,
        "kind": "moved" if moved_to else "pruned",
        "on": datetime.now(UTC).date().isoformat(),
        "by": by,
        "reason": reason,
    }
    if moved_to:
        entry["moved_to"] = moved_to
    retired["retired"].append(entry)
    errors = SchemaStore(repo / "schema").validate(retired, "retired.schema.json")
    if errors:
        raise ValueError(errors[0].message)
    if path.read_text() != source:
        raise ValueError("Node changed while pruning was prepared")
    atomic_write(retired_path, dump_metadata(retired))
    path.unlink()
    result["deleted"] = True
    return result


def status_preview(
    repo: Path, selected: tuple[str, ...] = (), *, fast: bool = False
) -> dict[str, Any]:
    """Prefer authoritative state; mark source previews as approximate."""
    if not fast:
        from homalg.runtime_state import document_state

        states = [document_state(repo, key) for key in documents(repo, selected)]
        nodes = [node for state in states for node in state["nodes"]]
        return {
            "approx": any(state["approx"] for state in states),
            "counts": status_counts(nodes),
            "nodes": [
                {"id": node["id"], **node["global"], "approx": node["approx"]} for node in nodes
            ],
        }
    nodes = []
    for path in node_paths(repo, documents(repo, selected)):
        source = path.read_text()
        authored = parse_header(source).metadata
        local = (
            "planned" if not authored["decls"] else ("stated" if sorry_count(source) else "proved")
        )
        # Without a fresh export, no lock can establish an authoritative completed headline.
        status, headline = compute_status(authored, {"local_status": local}, {}, [], reopened=True)
        nodes.append(
            {
                "id": authored["id"],
                "authored": authored,
                "global": {"status": status, "headline": headline, "reopened": True},
            }
        )
    return {
        "approx": True,
        "counts": status_counts(nodes),
        "nodes": [{"id": node["id"], **node["global"]} for node in nodes],
    }


def comparison_nodes(
    repo: Path, key: str, base: str | None = None
) -> tuple[str | None, dict[str, Any]]:
    """Read committed local status facts without checking out or modifying the review base."""
    reference = base or os.environ.get("GITHUB_BASE_SHA") or "origin/main"
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options", reference + "^{commit}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        if base:
            raise ValueError(f"Cannot resolve review base {base}")
        return None, {}
    revision = result.stdout.strip()
    result = subprocess.run(
        ["git", "show", f"{revision}:literature/{key}/nodes.json"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        return revision, {}
    return revision, {node["id"]: node for node in json.loads(result.stdout)["nodes"]}


def review_summary(repo: Path, key: str, *, base: str | None = None) -> str:
    """Produce a reviewer-facing metadata/findings/sorry summary without sending a message."""
    from homalg.validate import validate_repo

    findings, skipped, _ = validate_repo(repo, (key,), fast=True)
    lines = [
        f"# Formalization review: {key}",
        "",
        "## Findings",
        "",
        "| Rule | Severity | Location | Message |",
        "| --- | --- | --- | --- |",
    ]
    for finding in findings:
        message = finding.message.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {finding.rule} | {finding.severity} | "
            f"{finding.file}:{finding.line or 1} | {message} |"
        )
    if not findings:
        lines.append("| — | — | — | No findings in the selected check set. |")
    revision, previous = comparison_nodes(repo, key, base)
    current_path = repo / "literature" / key / "nodes.json"
    current = (
        {node["id"]: node for node in json.loads(current_path.read_text())["nodes"]}
        if current_path.exists()
        else {}
    )
    lines += ["", "## Added nodes and status changes", ""]
    if revision:
        lines += [f"Comparison base: `{revision}`. Stored local proof states are shown below.", ""]
        lines += ["| Node | Before | After |", "| --- | --- | --- |"]

        def label(node: dict[str, Any] | None) -> str:
            if node is None:
                return "absent"
            authored = node["authored"]
            local = (node.get("derived") or {}).get("local_status", "not exported")
            locked = "reviewed" if authored["fidelity"].get("reviewed") else "unreviewed"
            return f"{local}; {authored['fidelity']['status']}; {locked}"

        changes = 0
        for identifier in sorted(previous.keys() | current.keys()):
            before, after = label(previous.get(identifier)), label(current.get(identifier))
            if before != after:
                lines.append(f"| `{identifier}` | {before} | {after} |")
                changes += 1
        if not changes:
            lines.append("| — | No stored status changes | — |")
    else:
        lines.append(
            "No comparison base is available; added nodes and before/after states are unknown."
        )
    lines.append(
        "\nThese are document-local exported states, not historical global headline claims. "
        "The findings above report stale generated records."
    )
    lines += ["", "## Source items and deviations", ""]
    sorry = []
    from homalg.leantext import commands

    for path in node_paths(repo, [key]):
        source = path.read_text()
        header = parse_header(source).metadata
        lines.append(
            f"- `{header['id']}`: {header['fidelity']['status']}; "
            f"{len(header['decls'])} main declarations."
        )
        for deviation in header["fidelity"].get("deviations", []):
            lines.append(f"  - {deviation['kind']}: {deviation['what']} ({deviation['why']})")
        sorry.extend(
            command.name or "<anonymous>"
            for command in commands(source)
            if sorry_count(command.text)
        )
    lines += ["", "## Remaining sorry declarations", ""]
    lines.extend(f"- `{name}`" for name in sorry)
    if not sorry:
        lines.append("None found by the source scanner; compiled export remains authoritative.")
    lines += ["", "## Check coverage", "", f"Skipped: {', '.join(skipped) or 'none'}.", ""]
    return "\n".join(lines)
