"""Node-level settlement of partially complete statement units.

A statement unit batches independent primaries so that their shared checks run
once. When the exact stage evaluation fails only on some primaries, holding the
passing siblings behind the failing one wastes the whole batch and blocks the
scheduler. Settlement narrows the unit's scope to the primaries that already
pass, re-runs the identical evaluation on the narrowed unit, and releases the
remaining primaries to their own units. No gate is relaxed: the narrowed unit
must pass the same evaluation on its own, and released primaries keep every
obligation in their new units.

Settlement refuses whenever a failure cannot be attributed to a single scoped
primary (document validation, missing export, foundations, cycles), when the
narrowed unit fails on its own, or when nothing would remain.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg.documents import dump_metadata, parse_metadata, read_document
from homalg.engine import horizon, tasks
from homalg.headers import parse_header
from homalg.io import atomic_write
from homalg.repository import node_paths
from homalg.stages import DEFINITION_KINDS

STAGES = {"STMT", "CITED"}
NODE_FAILURE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*\.[A-Za-z][A-Za-z0-9_]*): ")
LEAN = re.compile(r"HomAlg/([A-Za-z][A-Za-z0-9_]*)/([A-Za-z][A-Za-z0-9_]*)\.lean")
REVIEW = re.compile(r"literature/([A-Za-z][A-Za-z0-9_]*)/reviews/([A-Za-z][A-Za-z0-9_]*)\.md")
ACTIVE = {"queued", "running", "blocked"}

Evaluator = Callable[[dict[str, Any]], dict[str, Any]]


def _headers(repo: Path, key: str) -> dict[str, dict[str, Any]]:
    return {
        header.metadata["id"]: header.metadata
        for path in node_paths(repo, [key])
        for header in [parse_header(path.read_text())]
    }


CUSTOM = object()


def _extension(repo: Path, record: dict[str, Any]) -> str | object:
    """``""`` for a plain generated objective, the appended text, or ``CUSTOM``.

    New tasks carry the digest of their generated objective. Older tasks are
    recognized only when nothing follows the template's closing line except the
    generated author-group appendix. ``CUSTOM`` marks an objective whose additions
    cannot be separated from the template, such as a fully rewritten one.
    """
    from homalg.planning import AUTHOR_GROUPS_FOOTER, AUTHOR_GROUPS_HEADER, TEMPLATES

    objective = record.get("objective") or ""
    info = record.get("metadata", {}).get("homalg", {})
    recorded = info.get("objective_sha256")
    if recorded:
        return "" if hashlib.sha256(objective.encode()).hexdigest() == recorded else CUSTOM
    template = repo / "horizon/tasks" / f"{TEMPLATES.get(info.get('stage'), '')}.md"
    lines = (
        [line.strip() for line in template.read_text().splitlines() if line.strip()]
        if template.is_file()
        else []
    )
    tail = lines[-1] if lines and "{" not in lines[-1] else None
    if not tail or tail not in objective:
        return CUSTOM
    rest = objective[objective.rindex(tail) + len(tail) :]
    groups = (
        re.escape(AUTHOR_GROUPS_HEADER.strip()) + r".*?" + re.escape(AUTHOR_GROUPS_FOOTER.strip())
    )
    return re.sub(groups, "", rest, count=1, flags=re.S).strip()


def objective_extension(repo: Path, record: dict[str, Any]) -> str:
    """Guidance a released node should carry: appended text, or a pointer to the source."""
    extension = _extension(repo, record)
    pointer = f"The source objective may hold further context: horizon task show {record.get('id')}"
    if extension is CUSTOM:
        return pointer
    return f"{extension}\n{pointer}" if extension else ""


def auto_eligible(repo: Path, record: dict[str, Any]) -> bool:
    """Only plain generated units settle or close without an explicit operator choice."""
    return _extension(repo, record) == ""


def inheritance(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Guidance and inbox context each released primary carries into its next unit."""
    inherited: dict[str, dict[str, Any]] = {}
    for record in records:
        for entry in record.get("metadata", {}).get("homalg", {}).get("settlements", []):
            carried = entry.get("inherit")
            if not carried:
                continue
            for primary in entry.get("released", {}):
                inherited[primary] = carried
    return inherited


def guidance_text(sources: list[dict[str, Any]]) -> str:
    """One labelled block per distinct source; empty when nothing was carried."""
    blocks = []
    seen = set()
    for source in sources:
        text = (source.get("guidance") or "").strip()
        if not text or (source.get("source"), text) in seen:
            continue
        seen.add((source.get("source"), text))
        blocks.append(
            f"Guidance inherited from {source.get('source')} when it was settled by node. "
            "It applies to this unit's nodes where relevant and grants no new scope:\n" + text
        )
    return "\n\n".join(blocks)


def _file_node(path: str) -> str | None:
    match = LEAN.fullmatch(path) or REVIEW.fullmatch(path)
    return f"{match.group(1)}.{match.group(2)}" if match else None


def _primary_of(identifier: str, primaries: set[str], headers: dict[str, dict]) -> str | None:
    seen = set()
    while identifier not in primaries:
        if identifier in seen or identifier not in headers:
            return None
        seen.add(identifier)
        identifier = headers[identifier].get("aux", {}).get("parent", "")
    return identifier


def primaries(record: dict[str, Any], headers: dict[str, dict]) -> list[str]:
    info = record["metadata"]["homalg"]
    explicit = info.get("primary_nodes")
    if explicit:
        return list(explicit)
    return [
        identifier
        for identifier in info.get("node_ids", [])
        if "aux" not in headers.get(identifier, {})
    ]


def attribute(
    failures: list[str], primary_ids: list[str], headers: dict[str, dict]
) -> tuple[dict[str, list[str]], list[str]]:
    """Split failures into per-primary failures and unattributable global failures."""
    scoped: dict[str, list[str]] = {}
    unattributed = []
    owned = set(primary_ids)
    for failure in failures:
        match = NODE_FAILURE.match(failure)
        primary = (
            _primary_of(match.group(1), owned, headers)
            if match and match.group(1) in headers
            else None
        )
        if primary is None:
            unattributed.append(failure)
        else:
            scoped.setdefault(primary, []).append(failure)
    return scoped, unattributed


def narrowed_record(
    record: dict[str, Any], keep: set[str], headers: dict[str, dict]
) -> tuple[dict[str, Any], list[str]]:
    """Return the record restricted to kept primaries and the released file list."""
    narrowed = copy.deepcopy(record)
    info = narrowed["metadata"]["homalg"]
    all_primaries = set(primaries(record, headers))
    files = record.get("write_set", {}).get("files", [])
    kept_files, released = [], []
    for path in files:
        identifier = _file_node(path)
        owner = _primary_of(identifier, all_primaries, headers) if identifier else None
        (released if owner is not None and owner not in keep else kept_files).append(path)
    narrowed.setdefault("write_set", {})["files"] = kept_files
    if isinstance(narrowed.get("scope"), dict) and "files" in narrowed["scope"]:
        narrowed["scope"]["files"] = [
            path for path in narrowed["scope"]["files"] if path not in set(released)
        ]
    node_ids = [
        identifier
        for identifier in info.get("node_ids", [])
        if _primary_of(identifier, all_primaries, headers) in keep
    ]
    info["node_ids"] = node_ids
    info["primary_nodes"] = [
        identifier for identifier in primaries(record, headers) if identifier in keep
    ]
    groups = []
    for group in info.get("author_groups", []):
        members = [
            identifier
            for identifier in group.get("node_ids", [])
            if _primary_of(identifier, all_primaries, headers) in keep
        ]
        if members:
            primary = group.get("primary") if group.get("primary") in members else members[0]
            groups.append({**group, "primary": primary, "node_ids": members})
    if "author_groups" in info:
        info["author_groups"] = groups
    pages = sorted(
        {
            page
            for identifier in node_ids
            for page in headers.get(identifier, {}).get("source", {}).get("pages", [])
            if isinstance(page, int)
        }
    )
    if pages:
        info["pages"] = pages
    kinds = [headers.get(identifier, {}).get("kind") for identifier in info["primary_nodes"]]
    if kinds:
        info["kind_group"] = (
            "definitions" if all(kind in DEFINITION_KINDS for kind in kinds) else "items"
        )
    return narrowed, released


def plan_settlement(
    repo: Path,
    record: dict[str, Any],
    evaluation: dict[str, Any],
    evaluate: Evaluator,
    *,
    headers: dict[str, dict] | None = None,
) -> dict[str, Any]:
    """Compute a settlement without writing anything; ``applicable`` says whether it holds."""
    info = record.get("metadata", {}).get("homalg", {})
    outcome: dict[str, Any] = {"task": record.get("id"), "applicable": False}
    if info.get("granularity") != "node" or info.get("stage") not in STAGES:
        return {**outcome, "reason": "not a node-granular statement unit"}
    if evaluation.get("complete"):
        return {**outcome, "reason": "evaluation already complete"}
    headers = headers if headers is not None else _headers(repo, info["doc"])
    primary_ids = primaries(record, headers)
    scoped, unattributed = attribute(evaluation.get("failures", []), primary_ids, headers)
    if unattributed:
        return {**outcome, "reason": "unattributable failures", "unattributed": unattributed}
    keep = {identifier for identifier in primary_ids if identifier not in scoped}
    if not keep:
        return {**outcome, "reason": "no primary passes the stage evaluation"}
    if not scoped:
        return {**outcome, "reason": "incomplete evaluation without recorded failures"}
    narrowed, released_files = narrowed_record(record, keep, headers)
    check = evaluate(narrowed)
    if not check.get("complete"):
        return {
            **outcome,
            "reason": "narrowed unit does not pass on its own",
            "narrowed_failures": check.get("failures", []),
        }
    released = {
        primary: sorted(
            identifier
            for identifier in info.get("node_ids", [])
            if _primary_of(identifier, set(primary_ids), headers) == primary
        )
        or [primary]
        for primary in primary_ids
        if primary in scoped
    }
    review_failed = {}
    if info.get("phase") == "review":
        # Remember which delivery failed, so the node goes back to its author instead
        # of being sent to review again unchanged.
        for primary in released:
            entry = next(
                (item for item in info.get("handoffs", []) if primary in item.get("node_ids", [])),
                None,
            )
            if entry is not None:
                review_failed[primary] = Path(entry["path"]).stem
    return {
        **outcome,
        "applicable": True,
        "review_failed": review_failed,
        "retained": sorted(keep),
        "released": released,
        "released_files": released_files,
        "failures": scoped,
        "narrowed": narrowed,
        "evaluation": check,
    }


def apply_settlement(
    repo: Path,
    plan: dict[str, Any],
    *,
    interval: tuple[str, str] | None = None,
    actor: str = "homalg",
) -> dict[str, Any]:
    """Write the narrowed scope and its audit record; the caller sets the task status."""
    path = repo / ".archon-horizon/tasks/items" / f"{plan['task']}.yaml"
    current = parse_metadata(path.read_text())
    narrowed = plan["narrowed"]
    entry = {
        "at": datetime.now(UTC).isoformat(),
        "actor": actor,
        "retained": plan["retained"],
        "released": plan["released"],
        "released_files": plan["released_files"],
        "failures": plan["failures"],
    }
    if plan.get("review_failed"):
        entry["review_failed"] = plan["review_failed"]
    if interval:
        entry["interval"] = list(interval)
    guidance = objective_extension(repo, current)
    refs = list(current.get("inbox_refs") or [])
    if guidance or refs:
        entry["inherit"] = {"source": plan["task"], "guidance": guidance, "inbox_refs": refs}
    info = copy.deepcopy(narrowed["metadata"]["homalg"])
    info.setdefault("settlements", list(current["metadata"]["homalg"].get("settlements", [])))
    info["settlements"] = [*info["settlements"], entry]
    current["metadata"]["homalg"] = info
    current["write_set"] = {**current.get("write_set", {}), **narrowed["write_set"]}
    if isinstance(current.get("scope"), dict) and "files" in current["scope"]:
        current["scope"]["files"] = narrowed["scope"]["files"]
    atomic_write(path, dump_metadata(current))
    return entry


def released_scope(record: dict[str, Any], since: str, until: str) -> set[str]:
    """Files this exact session interval owned before a settlement narrowed the task."""
    info = record.get("metadata", {}).get("homalg", {})
    return {
        path
        for entry in info.get("settlements", [])
        if entry.get("interval") == [since, until]
        for path in entry.get("released_files", [])
    }


def covering_tasks(repo: Path, key: str) -> dict[str, list[str]]:
    """Map each node to the active tasks whose scope names it."""
    covered: dict[str, list[str]] = {}
    for record in tasks(repo, key):
        if record.get("status") not in ACTIVE:
            continue
        for identifier in record.get("metadata", {}).get("homalg", {}).get("node_ids", []):
            covered.setdefault(identifier, []).append(record["id"])
    return covered


def ensure_units(
    repo: Path,
    key: str,
    released: dict[str, list[str]],
    *,
    source: dict[str, Any],
    login: str,
) -> list[str]:
    """Safety net after planning: give each ready, uncovered released primary its own unit.

    Planning normally creates these units itself, and creates units for released
    primaries with unmet prerequisites only once those prerequisites are accepted.
    This never creates a runnable unit for a primary that still has frontier
    blockers, and never duplicates a primary an active task already covers.
    """
    from homalg import planning
    from homalg.statement_frontier import StatementFrontier

    covered = covering_tasks(repo, key)
    records = tasks(repo, key)
    existing = {record["id"] for record in records}
    inherited = inheritance(records)
    document = read_document(repo, key)
    frontier = StatementFrontier(repo, key)
    headers = {identifier: header.metadata for identifier, header in frontier.headers.items()}
    info = source["metadata"]["homalg"]
    created = []
    for primary in released:
        if primary in covered or primary not in headers:
            continue
        group = frontier.group(primary)
        if frontier.blockers(group) or all(frontier.settled_statement(i) for i in group):
            continue
        local = primary.split(".", 1)[1]
        identifier = f"{key}.{info['stage']}.Unit_{local}"
        suffix = 2
        while identifier in existing:
            identifier = f"{key}.{info['stage']}.Unit_{local}_r{suffix}"
            suffix += 1
        node = headers[primary]
        files = sorted(
            [f"HomAlg/{value.replace('.', '/', 1)}.lean" for value in group]
            + [f"literature/{key}/reviews/{value.split('.', 1)[1]}.md" for value in group]
        )
        unit_info = {
            "doc": key,
            "stage": info["stage"],
            "chapter": node.get("source", {}).get("chapter", info.get("chapter")),
            "section": node.get("source", {}).get("section"),
            "attempts": 0,
            "pages": node.get("source", {}).get("pages", info.get("pages", [])),
            "granularity": "node",
            "phase": "author",
            "kind_group": "definitions" if node.get("kind") in DEFINITION_KINDS else "theorems",
            "node_ids": group,
            "primary_nodes": [primary],
            "released_from": source["id"],
        }
        carried = inherited.get(primary, {})
        planning.create_task(
            repo,
            {
                "id": identifier,
                "metadata": {"homalg": unit_info, "roadmap_status_sync": False},
                "node_ids": group,
                "roadmap_refs": source.get("roadmap_refs") or [f"{key}.{info['stage']}"],
                "write_set": {"files": files},
            },
            login=login,
            document=document,
            guidance=guidance_text([carried]) if carried else "",
            inbox_refs=carried.get("inbox_refs") or list(source.get("inbox_refs", [])),
        )
        existing.add(identifier)
        created.append(identifier)
    return created


def _set_status(repo: Path, task_id: str, status: str) -> None:
    horizon(repo, "task", "set", task_id, "--status", status, "--author", "homalg", "--json")


def _record_closure(repo: Path, task_id: str, evaluation: dict[str, Any]) -> None:
    path = repo / ".archon-horizon/tasks/items" / f"{task_id}.yaml"
    current = parse_metadata(path.read_text())
    current["metadata"]["homalg"]["evidence_closure"] = {
        "at": datetime.now(UTC).isoformat(),
        "actor": "homalg",
        "stage": evaluation.get("stage"),
        "complete": True,
    }
    atomic_write(path, dump_metadata(current))


def _legacy_unit(record: dict[str, Any]) -> bool:
    info = record.get("metadata", {}).get("homalg", {})
    return (
        info.get("granularity") == "node"
        and info.get("stage") == "STMT"
        and info.get("phase") is None
        and record.get("status") in {"queued", "blocked"}
    )


def _record_replan(repo: Path, record: dict[str, Any], headers: dict[str, dict]) -> None:
    """Release every primary of a legacy unit to planning, keeping its guidance."""
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    current = parse_metadata(path.read_text())
    info = current["metadata"]["homalg"]
    primary_ids = primaries(current, headers)
    released = {
        primary: [
            node_id
            for node_id in info.get("node_ids", [])
            if _primary_of(node_id, set(primary_ids), headers) == primary
        ]
        or [primary]
        for primary in primary_ids
    }
    entry: dict[str, Any] = {
        "at": datetime.now(UTC).isoformat(),
        "actor": "homalg",
        "replanned": True,
        "retained": [],
        "released": released,
        "released_files": [],
        "failures": {},
    }
    guidance = objective_extension(repo, current)
    refs = list(current.get("inbox_refs") or [])
    if guidance or refs:
        entry["inherit"] = {"source": record["id"], "guidance": guidance, "inbox_refs": refs}
    info["settlements"] = [*info.get("settlements", []), entry]
    atomic_write(path, dump_metadata(current))


def settle_document(
    repo: Path,
    key: str,
    *,
    task_ids: tuple[str, ...] = (),
    apply: bool = False,
    refresh_export: bool = False,
    replan: bool = False,
) -> dict[str, Any]:
    """Close tasks already satisfied by current evidence and settle partial statement units.

    ``replan`` additionally cancels the remaining queued or blocked statement units
    planned before authoring and review were separated, handing their unsettled
    nodes back to planning, which recreates them as larger author units. Accepted
    nodes stay accepted; guidance and inbox references carry over.

    Without ``task_ids`` only plain generated tasks are considered: a task whose
    objective was extended may carry obligations its stage gate does not capture,
    so closing or narrowing it is an explicit operator choice. Dry run by default.
    Every decision is computed in one read phase over
    memoized, change-checked facts before anything is written. ``apply`` requires
    an idle engine because it rewrites task scopes and statuses that a running
    session or hook could otherwise race.
    """
    from homalg import planning, stages
    from homalg.engine import settings
    from homalg.human import require_idle
    from homalg.planning_facts import PlanningFacts

    if apply:
        require_idle(repo)
    if refresh_export:
        stages.refresh(repo, key)
    headers = _headers(repo, key)
    facts = PlanningFacts(repo)
    selected = set(task_ids)

    def evaluate(record: dict[str, Any]) -> dict[str, Any]:
        return stages.evaluate(
            repo, record, refresh_exports=False, persist_transcription=False, facts=facts
        )

    actions, plans = [], {}
    for record in tasks(repo, key):
        if selected and record["id"] not in selected:
            continue
        if record.get("status") not in {"queued", "blocked"}:
            continue
        info = record.get("metadata", {}).get("homalg", {})
        if record.get("metadata", {}).get("dispatch_hold") and not info.get("granularity"):
            # Chapter aggregates wait for unit acceptance; they are not executable work.
            continue
        if info.get("stage") == "PROOF":
            continue
        if not selected and not auto_eligible(repo, record):
            actions.append(
                {
                    "task": record["id"],
                    "action": "none",
                    "reason": "objective has extra obligations; select it with --task",
                }
            )
            continue
        evaluation = evaluate(record)
        if evaluation["complete"]:
            actions.append({"task": record["id"], "action": "close", "status": record["status"]})
            plans[record["id"]] = evaluation
            continue
        plan = plan_settlement(repo, record, evaluation, evaluate, headers=headers)
        summary = {
            name: value for name, value in plan.items() if name not in {"narrowed", "evaluation"}
        }
        if not plan["applicable"]:
            if replan and _legacy_unit(record):
                actions.append({"task": record["id"], "action": "replan", **summary})
                plans[record["id"]] = record
                continue
            actions.append({"task": record["id"], "action": "none", **summary})
            continue
        actions.append({"task": record["id"], "action": "settle", **summary})
        plans[record["id"]] = plan
    created: list[str] = []
    if apply and plans:
        for item in actions:
            if item["action"] == "close":
                _record_closure(repo, item["task"], plans[item["task"]])
                _set_status(repo, item["task"], "done")
            elif item["action"] == "settle":
                apply_settlement(repo, plans[item["task"]])
                _set_status(repo, item["task"], "done")
            elif item["action"] == "replan":
                _record_replan(repo, plans[item["task"]], headers)
                _set_status(repo, item["task"], "cancelled")
        prior_plan = repo / f".archon-horizon/overlay/plan-{key}.json"
        prior = json.loads(prior_plan.read_text()) if prior_plan.exists() else {}
        result = planning.plan(repo, key, advance=True, no_claim=prior.get("no_claim", False))
        created.extend(result.get("created_tasks", []))
        login = settings(repo).get("login") or ""
        for item in actions:
            if item["action"] != "settle":
                continue
            source = next(record for record in tasks(repo, key) if record["id"] == item["task"])
            created.extend(ensure_units(repo, key, item["released"], source=source, login=login))
    return {
        "doc_key": key,
        "applied": apply,
        "actions": actions,
        "created_tasks": created,
    }
