"""Frozen author deliveries and read-only recommendations for the ordinary task gates."""

import hashlib
import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg import planning
from homalg.checks import RULES
from homalg.documents import read_document
from homalg.engine import task, tasks
from homalg.headers import parse_header
from homalg.io import atomic_create, json_text
from homalg.leanexport import declaration_map, export_lean, workspace_lock
from homalg.review import (
    freeze_authoring_batch_inputs,
    freeze_authoring_inputs,
    freeze_fidelity_inputs,
)
from homalg.review_policy import valid_agent_review
from homalg.scope import new_node_allowed
from homalg.transcription import status as transcription_status
from homalg.validate import validate_repo

DERIVED_CACHE_RULES = {"nodes-json-fresh", "nodes-json-stale"}


def _local_output(repo: Path, output: Path) -> Path:
    """Keep local evidence out of authored files and reject symlink escapes."""
    path = (repo / output).resolve()
    if (repo / "build").resolve() != repo / "build":
        raise ValueError("Workflow build/ evidence directory must not be a symlink")
    if not path.is_relative_to((repo / "build").resolve()) or path == repo / "build":
        raise ValueError("Workflow evidence must be written below the local build/ directory")
    if path.exists():
        raise ValueError("Workflow evidence already exists; use a new handoff/snapshot path")
    return path


def _contract(record: dict[str, Any]) -> dict[str, Any]:
    info = record["metadata"]["homalg"]
    return {
        "id": record["id"],
        "objective": record.get("objective"),
        "write_set": record.get("write_set", {}),
        "homalg": {key: value for key, value in info.items() if key != "attempts"},
    }


def _node_scope(repo: Path, record: dict[str, Any]) -> set[str]:
    """Include the same legitimate new direct auxiliary leaves as native task scope."""
    explicit = set(record.get("write_set", {}).get("files", []))
    allowed = set(explicit)
    key = record["metadata"]["homalg"]["doc"]
    for path in (repo / "HomAlg" / key).glob("*.lean"):
        relative = path.relative_to(repo).as_posix()
        if relative in explicit:
            continue
        authored = parse_header(path.read_text()).metadata
        if new_node_allowed(relative, authored, record, explicit):
            allowed.add(relative)
    return allowed


def _nodes(
    repo: Path, record: dict[str, Any], node_ids: tuple[str, ...] = ()
) -> dict[str, dict[str, Any]]:
    """Select real formal nodes from an existing immutable statement task scope."""
    info = record["metadata"]["homalg"]
    if info["stage"] not in {"STMT", "CITED", "PROOF"}:
        raise ValueError("Author handoffs require a registered STMT, CITED or PROOF task")
    if len(set(node_ids)) != len(node_ids):
        raise ValueError("Author handoff node selection must be unique")
    nodes = {}
    for name in sorted(_node_scope(repo, record)):
        if not re.fullmatch(r"HomAlg/[A-Za-z0-9_]+/[A-Za-z0-9_]+\.lean", name):
            continue
        expected = name.removeprefix("HomAlg/").removesuffix(".lean").replace("/", ".")
        if node_ids and expected not in node_ids:
            continue
        path = repo / name
        if path.resolve() != path or not path.is_file():
            raise ValueError(f"Task node must be an existing regular local file: {name}")
        authored = parse_header(path.read_text()).metadata
        if authored["id"] != expected or authored["doc"] != info["doc"]:
            raise ValueError(f"Node identity differs from its task path: {name}")
        if "informal" in authored or authored.get("aux", {}).get("pruned"):
            continue
        if not authored.get("decls"):
            raise ValueError(f"{authored['id']}: author delivery needs actual main declarations")
        nodes[name] = authored
    if not nodes:
        raise ValueError("The task has no formal Lean nodes to deliver")
    if node_ids and set(node_ids) != {node["id"] for node in nodes.values()}:
        raise ValueError("Author handoff nodes must be formal nodes inside the task's scope")
    return nodes


def prepare(
    repo: Path, task_id: str, *, author_session: str, out: Path, node_ids: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Compile and freeze one actual author's delivery before independent review."""
    return _prepare_deliveries(
        repo,
        task_id,
        groups=[{"author_session": author_session, "node_ids": node_ids}],
        out=out,
        batch=False,
    )


def prepare_batch(
    repo: Path, task_id: str, *, authors: list[dict[str, Any]], out: Path
) -> dict[str, Any]:
    """Share one fresh export/validation while retaining each actual author's delivery.

    The single immutable output is published only after every selected input has
    been rechecked. It grants no approval and does not cache results across calls.
    """
    return _prepare_deliveries(repo, task_id, groups=authors, out=out, batch=True)


def _prepare_deliveries(
    repo: Path, task_id: str, *, groups: list[dict[str, Any]], out: Path, batch: bool
) -> dict[str, Any]:
    repo = repo.resolve()
    target = _local_output(repo, out)
    if not isinstance(groups, list) or not groups:
        raise ValueError("Author groups must be a nonempty list")
    normalized = []
    for group in groups:
        if not isinstance(group, dict) or set(group) != {"author_session", "node_ids"}:
            raise ValueError("Each author group requires only author_session and node_ids")
        author = group["author_session"]
        ids = group["node_ids"]
        if not isinstance(author, str) or not author.strip():
            raise ValueError("An actual author session is required")
        if not isinstance(ids, (list, tuple)) or not all(isinstance(item, str) for item in ids):
            raise ValueError("Each author group needs an explicit list of node ids")
        if batch and not ids:
            raise ValueError("Batch author groups must explicitly select nonempty node lists")
        normalized.append({"author_session": author.strip(), "node_ids": tuple(ids)})
    if len({group["author_session"] for group in normalized}) != len(normalized):
        raise ValueError("Combine nodes from the same actual author into one group")
    with workspace_lock(repo):
        record = task(repo, task_id)
        contract = _contract(record)
        selections = [_nodes(repo, record, group["node_ids"]) for group in normalized]
        nodes = {}
        for selected in selections:
            if nodes.keys() & selected.keys():
                raise ValueError("Author groups must have disjoint node ownership")
            nodes.update(selected)
        all_ids = tuple(node["id"] for node in nodes.values())
        selected_groups = [
            tuple(node["id"] for node in selected.values()) for selected in selections
        ]
        if batch:
            snapshots, batch_inputs = freeze_authoring_batch_inputs(repo, selected_groups)
        else:
            snapshots = [freeze_authoring_inputs(repo, selected_groups[0])]
            batch_inputs = None
        key = record["metadata"]["homalg"]["doc"]
        raw = export_lean(repo, doc=key, out=repo / "build/workflow-export.json", merge=False)
        # Every group sees the same complete current validation. Only the two
        # derived-cache rules are deferred to the unchanged final acceptance gates.
        findings, skipped, counts = validate_repo(
            repo,
            (key,),
            fast=False,
            export=raw,
            only=tuple(sorted(set(RULES) - DERIVED_CACHE_RULES)),
        )
        task_scope = _node_scope(repo, record)
        pending = []
        validation = []
        for item in findings:
            authored = nodes.get(item.file, {})
            if (
                item.rule == "fidelity-reopened"
                and item.file in task_scope
                and item.file not in nodes
            ):
                authored = parse_header((repo / item.file).read_text()).metadata
            if item.rule == "fidelity-reopened" and valid_agent_review(
                authored.get("fidelity", {}).get("reviewed")
            ):
                pending.append(asdict(item))
            else:
                validation.append(asdict(item))
        exported = declaration_map(raw)
        declarations = {}
        for authored in nodes.values():
            module = exported.get(f"HomAlg.{authored['id']}", {})
            missing = set(authored["decls"]) - module.keys()
            if missing:
                raise ValueError(f"{authored['id']}: compiled main declarations missing: {missing}")
            declarations[authored["id"]] = [module[name] for name in authored["decls"]]
        refreshed = freeze_authoring_batch_inputs(repo, selected_groups)[0] if batch else None
        for position, (selected, snapshot) in enumerate(zip(selections, snapshots, strict=True)):
            selected_ids = tuple(node["id"] for node in selected.values())
            if (
                (
                    refreshed[position]
                    if refreshed is not None
                    else freeze_authoring_inputs(repo, selected_ids)
                )
                != snapshot
                or _contract(task(repo, task_id)) != contract
                or _nodes(repo, record, selected_ids) != selected
            ):
                raise ValueError("Author inputs or task scope changed during the preflight")
        if batch and freeze_authoring_inputs(repo, all_ids) != batch_inputs:
            raise ValueError("Batch author inputs changed during the preflight")
        common = {
            "schema_version": 1,
            "repo": str(repo),
            "task": task_id,
            "contract": contract,
            "created_at": datetime.now(UTC).isoformat(),
            "ready_for_review": not any(item["severity"] == "error" for item in validation),
            "approval": False,
            "task_complete": False,
            "validation": {
                "findings": validation,
                "skipped": sorted(set(skipped) | DERIVED_CACHE_RULES),
                "deferred": sorted(DERIVED_CACHE_RULES),
                "counts": counts,
            },
            "pending_review_renewal": pending,
        }
        raw_sha256 = hashlib.sha256(json_text(raw).encode()).hexdigest()
        deliveries = []
        for group, selected, snapshot in zip(normalized, selections, snapshots, strict=True):
            selected_ids = [node["id"] for node in selected.values()]
            deliveries.append(
                common
                | {
                    "kind": "author-handoff",
                    "author_session": group["author_session"],
                    "node_ids": selected_ids,
                    "author_inputs": snapshot,
                    "compiled": {
                        "fresh_build": True,
                        "raw_sha256": raw_sha256,
                        "declarations": {
                            node_id: declarations[node_id] for node_id in selected_ids
                        },
                    },
                }
            )
        result = (
            (common | {"kind": "author-handoff-batch", "deliveries": deliveries})
            if batch
            else deliveries[0]
        )
        atomic_create(target, json_text(result))
    return result


def verify(repo: Path, handoff: Path, *, author_session: str | None = None) -> dict[str, Any]:
    """Check a successful delivery's task and author input freshness, never its truth."""
    repo = repo.resolve()
    path = (repo / handoff).resolve()
    data = json.loads(path.read_text())
    if data.get("kind") == "author-handoff-batch":
        if data.get("schema_version") != 1 or data.get("repo") != str(repo):
            raise ValueError("Expected an author batch for this workspace")
        if not author_session:
            raise ValueError("Select the actual author with --author-session for a batch handoff")
        deliveries = data.get("deliveries")
        if not isinstance(deliveries, list):
            raise ValueError("Invalid author batch deliveries")
        selected = [
            item
            for item in deliveries
            if isinstance(item, dict) and item.get("author_session") == author_session
        ]
        if len(selected) != 1:
            raise ValueError("The selected author must identify exactly one batch delivery")
        if selected[0].get("task") != data.get("task"):
            raise ValueError("The selected author delivery has a different task")
        data = selected[0]
    if author_session is not None and data.get("author_session") != author_session:
        raise ValueError("The selected author differs from the handoff's actual author")
    if (
        data.get("schema_version") != 1
        or data.get("kind") != "author-handoff"
        or data.get("repo") != str(repo)
        or data.get("ready_for_review") is not True
        or not data.get("author_session", "").strip()
    ):
        raise ValueError("Expected a successful author handoff for this workspace")
    with workspace_lock(repo):
        record = task(repo, data["task"])
        if _contract(record) != data["contract"]:
            raise ValueError("Author handoff task scope changed")
        if [node["id"] for node in _nodes(repo, record, tuple(data["node_ids"])).values()] != data[
            "node_ids"
        ]:
            raise ValueError("Author handoff node selection changed")
        if freeze_authoring_inputs(repo, data["node_ids"]) != data["author_inputs"]:
            raise ValueError("Author handoff is stale; changed inputs need a new delivery/review")
    return data


def review_snapshot(
    repo: Path,
    handoff: Path,
    *,
    out: Path,
    node_ids: tuple[str, ...] = (),
    author_session: str | None = None,
) -> dict[str, Any]:
    """After reports exist, freeze exact review inputs for one batch registration."""
    repo = repo.resolve()
    target = _local_output(repo, out)
    with workspace_lock(repo):
        delivery = verify(repo, handoff, author_session=author_session)
        selected = list(node_ids) or delivery["node_ids"]
        if not set(selected) <= set(delivery["node_ids"]):
            raise ValueError("Review batch exceeds the author handoff's nodes")
        snapshot = freeze_fidelity_inputs(
            repo, selected, expected_author_session=delivery["author_session"]
        )
        # A non-cooperating editor may have changed author inputs while reports were read.
        verify(repo, handoff, author_session=author_session)
        atomic_create(target, json_text(snapshot))
    return snapshot


def next_tasks(repo: Path, key: str, *, proofs: str | None = None) -> dict[str, Any]:
    """Rank the ordinary planner's eligible tasks without creating, editing or compiling."""
    repo = repo.resolve()
    document = read_document(repo, key)
    overlay = repo / ".archon-horizon/overlay" / f"plan-{key}.json"
    prior = json.loads(overlay.read_text()) if overlay.exists() else {}
    proofs = proofs or prior.get("proofs", "included")
    if proofs not in {"deferred", "included"}:
        raise ValueError("Proof mode must be deferred or included")
    chapters = planning.chapter_ranges(document, tuple(prior.get("chapters", [])))
    unit_options = (
        {
            "statement_frontier": prior.get("statement_frontier", False),
            "statement_nodes": tuple(prior.get("statement_nodes", [])),
            "statement_batch_size": prior.get("statement_batch_size", 4),
        }
        if prior.get("statement_frontier") or prior.get("statement_nodes")
        else {}
    )
    proposals, _ = planning.unlocked_tasks(
        repo, key, chapters, persist_transcription=False, **unit_options
    )
    unit_candidates = (
        planning.statement_units(
            repo,
            key,
            chapters,
            tuple(prior.get("statement_nodes", [])),
            batch_size=prior.get("statement_batch_size", 4),
        )
        if unit_options
        else []
    )
    eligible = {record["id"]: record for record in proposals}
    existing = {record["id"]: record for record in tasks(repo, key)}
    offset = document.get("pdf", {}).get("page_offset", 0)
    pages_state = (
        {}
        if document["type"] == "synthetic"
        else transcription_status(repo, key, persist=False)["pages"]
    )
    pending_pages = {
        page
        for record in proposals
        if record["metadata"]["homalg"]["stage"] == "T"
        for page in record["metadata"]["homalg"]["pages"]
        if pages_state.get(f"{page:04}", {}).get("status") != "reviewed"
    }
    chapter_order = {chapter["chapter"]: i for i, chapter in enumerate(chapters)}

    def ranked(record: dict[str, Any]) -> dict[str, Any]:
        info = record["metadata"]["homalg"]
        stage = info["stage"]
        rank = {"STMT": 2, "CITED": 1, "DAG": 3, "INV": 4, "T": 5, "PROOF": 6}[stage]
        if stage == "STMT" and info.get("kind_group") == "definitions":
            rank = 0
        if info.get("granularity") == "node":
            rank -= 1
        chapter = chapter_order.get(info.get("chapter"), len(chapters))
        missing = 0
        if stage == "T":
            intersections = [
                (len(pending_pages & pages), index)
                for index, item in enumerate(chapters)
                for pages in [
                    set(range(item["pages"]["first"] + offset, item["pages"]["last"] + offset + 1))
                ]
                if pages.intersection(info["pages"])
            ]
            missing, chapter = min(intersections, default=(len(pending_pages), chapter))
        return {
            "task": record["id"],
            "stage": stage,
            "chapter": info.get("chapter"),
            "kind_group": info.get("kind_group"),
            "pages": info.get("pages", []),
            "priority": [rank, missing, chapter, min(info.get("pages") or [0])],
            "reason": (
                "Prioritize source batches nearest to completing a chapter prerequisite"
                if stage == "T"
                else "Prioritize ready definitions, cited interfaces and formal statements"
            ),
        }

    ready, unregistered, held, running = [], [], [], []
    for candidate in unit_candidates:
        if candidate["blockers"] and candidate["id"] not in existing:
            held.append(
                {
                    "task": candidate["id"],
                    "status": None,
                    "reason": "Statement unit prerequisites are not met",
                    "blockers": candidate["blockers"],
                }
            )
    for identifier, record in (eligible | existing).items():
        status = existing.get(identifier, {}).get("status")
        if status in {"done", "cancelled"}:
            continue
        if status == "running":
            running.append({"task": identifier, "status": status})
        elif record.get("metadata", {}).get("finalization_hold"):
            held.append(
                {
                    "task": identifier,
                    "status": status,
                    "reason": "Outer-session finalization has not been accepted",
                }
            )
        elif record.get("metadata", {}).get("dispatch_hold"):
            held.append(
                {
                    "task": identifier,
                    "status": status,
                    "reason": record["metadata"]["dispatch_hold"],
                }
            )
        elif proofs == "deferred" and record["metadata"]["homalg"]["stage"] == "PROOF":
            held.append({"task": identifier, "reason": "Proof work is deferred", "status": status})
        elif status not in {None, "queued"}:
            held.append(
                {"task": identifier, "reason": "Preserve existing task status", "status": status}
            )
        elif identifier not in eligible:
            held.append(
                {
                    "task": identifier,
                    "reason": "Current planner prerequisites are not met",
                    "status": status,
                }
            )
        elif status is None:
            unregistered.append(ranked(record))
        else:
            ready.append(ranked(record))

    def order(item: dict[str, Any]) -> tuple:
        return (item["priority"], item["task"])

    return {
        "doc_key": key,
        "proofs": proofs,
        "read_only": True,
        "evidence": "Current source and existing compiled evidence; no build or dispatch",
        "ready": sorted(ready, key=order),
        "requires_plan": sorted(unregistered, key=order),
        "running": running,
        "held": held,
    }
