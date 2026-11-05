"""Separate authoring from review for node-granular statement work.

An author unit (``phase: author``) writes, compiles and delivers statements; it is
complete when every node it owns is covered by a current, compiled author handoff.
A review unit (``phase: review``) independently reviews and registers delivered
nodes; it carries the ordinary statement gate (current satisfactory locks).

Each primary node is in exactly one derived state:

* ``settled``: a current satisfactory statement lock exists;
* ``active``: an open task already covers it;
* ``awaiting_review``: a current delivery exists and has not failed review;
* ``parked``: delivered but held, by an open dispute or by repeated review failure;
* ``needs_author``: anything else. Planning gives it a new author unit.

Nothing here relaxes a gate. A stale delivery (any input it depends on changed)
simply returns its nodes to authoring.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from homalg.engine import tasks

AUTHOR = "author"
REVIEW = "review"
OPEN = {"queued", "running", "blocked"}
MAX_REVIEW_FAILURES = 2


def phase(record: dict[str, Any]) -> str | None:
    return record.get("metadata", {}).get("homalg", {}).get("phase")


def handoff_digest(path: str) -> str:
    return Path(path).stem


@dataclass
class Delivery:
    task: str
    path: str
    author_session: str
    node_ids: list[str]
    created_at: str
    data: dict[str, Any] = field(repr=False)
    batch: bool = False


class Deliveries:
    """Recorded author deliveries and their freshness, read once per call."""

    def __init__(self, repo: Path, records: list[dict[str, Any]] | None = None):
        from homalg import workflow
        from homalg.review import _AuthoringContextReads

        self.repo = repo
        self.records = records if records is not None else None
        self._fresh: dict[tuple[str, str], bool] = {}
        self._reads = _AuthoringContextReads()
        self.by_task: dict[str, list[Delivery]] = {}
        for record in self.records or []:
            if phase(record) != AUTHOR:
                continue
            items = []
            for path, handoff in workflow.task_handoffs(repo, record["id"]):
                for item in workflow.deliveries(handoff):
                    items.append(
                        Delivery(
                            task=record["id"],
                            path=path,
                            author_session=item.get("author_session", ""),
                            node_ids=list(item.get("node_ids", [])),
                            created_at=handoff.get("created_at", ""),
                            data=item,
                            batch=handoff.get("kind") == "author-handoff-batch",
                        )
                    )
            self.by_task[record["id"]] = items

    def fresh(self, delivery: Delivery) -> bool:
        """Current inputs still equal the delivered ones (cached per call)."""
        from homalg import workflow

        key = (delivery.path, delivery.author_session)
        if key not in self._fresh:
            try:
                workflow.verify(
                    self.repo,
                    Path(delivery.path),
                    author_session=delivery.author_session if delivery.batch else None,
                    _reads=self._reads,
                )
                self._fresh[key] = True
            except (OSError, ValueError, KeyError):
                self._fresh[key] = False
        return self._fresh[key]

    def latest(self, node_id: str, task_id: str | None = None) -> Delivery | None:
        """The newest recorded delivery that includes the node."""
        candidates = [
            delivery
            for owner, items in self.by_task.items()
            if task_id is None or owner == task_id
            for delivery in items
            if node_id in delivery.node_ids
        ]
        return max(candidates, key=lambda item: item.created_at) if candidates else None


def group_ids(headers: dict[str, Any], primary: str) -> list[str]:
    """A primary node and its unpruned auxiliary children, present now."""
    return [
        primary,
        *sorted(
            node_id
            for node_id, header in headers.items()
            if header.metadata.get("aux", {}).get("parent") == primary
            and not header.metadata.get("aux", {}).get("pruned")
        ),
    ]


def author_failures(repo: Path, record: dict[str, Any]) -> list[str]:
    """Why an author unit is not yet complete, one node-attributed line per gap."""
    from homalg.headers import parse_header
    from homalg.repository import node_paths

    info = record["metadata"]["homalg"]
    key = info["doc"]
    headers = {
        header.metadata["id"]: header
        for path in node_paths(repo, [key])
        for header in [parse_header(path.read_text())]
    }
    primaries = info.get("primary_nodes") or [
        node_id
        for node_id in info.get("node_ids", [])
        if node_id in headers and "aux" not in headers[node_id].metadata
    ]
    deliveries = Deliveries(repo, [record])
    failures = []
    for primary in primaries:
        for node_id in group_ids(headers, primary):
            header = headers.get(node_id)
            if header is None:
                failures.append(f"{node_id}: node metadata is missing")
                continue
            node = header.metadata
            if "informal" in node or node.get("aux", {}).get("pruned"):
                continue
            if not node.get("decls"):
                failures.append(f"{node_id}: fresh main declarations are required")
                continue
            delivery = deliveries.latest(node_id, record["id"])
            if delivery is None or not deliveries.fresh(delivery):
                failures.append(f"{node_id}: a current author handoff is required")
                continue
            compiled = delivery.data.get("compiled", {}).get("declarations", {}).get(node_id, [])
            names = {item.get("name") for item in compiled if isinstance(item, dict)}
            if names and not set(node["decls"]) <= names:
                failures.append(f"{node_id}: the handoff does not cover every main declaration")
    return sorted(set(failures))


def review_failures(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Per primary node, the handoff digests whose review failed, oldest first."""
    failed: dict[str, list[str]] = {}
    for record in records:
        if phase(record) != REVIEW:
            continue
        for entry in record.get("metadata", {}).get("homalg", {}).get("settlements", []):
            for primary, digest in (entry.get("review_failed") or {}).items():
                failed.setdefault(primary, []).append(digest)
    return failed


def node_states(
    repo: Path,
    key: str,
    frontier: Any,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Derive the state of every formal primary node of a document."""
    records = records if records is not None else tasks(repo, key)
    active: dict[str, str] = {}
    for record in records:
        if record.get("status") not in OPEN:
            continue
        info = record.get("metadata", {}).get("homalg", {})
        if info.get("granularity") != "node":
            continue
        for node_id in info.get("primary_nodes") or info.get("node_ids", []):
            active.setdefault(node_id, record["id"])
    deliveries = Deliveries(repo, records)
    failed = review_failures(records)
    states: dict[str, dict[str, Any]] = {}
    for node_id, header in frontier.headers.items():
        node = header.metadata
        if "aux" in node or "informal" in node or "cited" in node:
            continue
        if frontier.settled_statement(node_id):
            states[node_id] = {"state": "settled"}
            continue
        if node_id in active:
            states[node_id] = {"state": "active", "task": active[node_id]}
            continue
        delivery = deliveries.latest(node_id)
        current = delivery is not None and deliveries.fresh(delivery)
        if current and node.get("dispute", {}).get("status") == "open":
            states[node_id] = {"state": "parked", "reason": "open dispute", "delivery": delivery}
            continue
        history = failed.get(node_id, [])
        if len(history) >= MAX_REVIEW_FAILURES:
            states[node_id] = {"state": "parked", "reason": "repeated review failure"}
            continue
        if current and handoff_digest(delivery.path) not in history:
            states[node_id] = {"state": "awaiting_review", "delivery": delivery}
            continue
        states[node_id] = {"state": "needs_author"}
    return states


def review_units(
    repo: Path,
    key: str,
    chapters: list[dict[str, Any]],
    *,
    frontier: Any,
    batch_size: int = 16,
    records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Propose review units for delivered nodes, keeping each author delivery whole."""
    records = records if records is not None else tasks(repo, key)
    selected = {chapter["chapter"] for chapter in chapters}
    states = node_states(repo, key, frontier, records)
    waiting: dict[tuple[str, str], dict[str, Any]] = {}
    for node_id, state in states.items():
        if state["state"] != "awaiting_review":
            continue
        chapter = frontier.headers[node_id].metadata["source"].get("chapter")
        if chapter not in selected:
            continue
        delivery = state["delivery"]
        slot = waiting.setdefault(
            (delivery.path, delivery.author_session),
            {"delivery": delivery, "chapter": chapter, "primaries": []},
        )
        slot["primaries"].append(node_id)
    order = {node_id: index for index, node_id in enumerate(frontier.headers)}
    slots = sorted(waiting.values(), key=lambda item: min(order[n] for n in item["primaries"]))
    batches: list[list[dict[str, Any]]] = []
    for slot in slots:
        for batch in batches:
            if (
                batch[0]["chapter"] == slot["chapter"]
                and sum(len(item["primaries"]) for item in batch) + len(slot["primaries"])
                <= batch_size
            ):
                batch.append(slot)
                break
        else:
            batches.append([slot])
    proposals = []
    for batch in batches:
        primaries = sorted(
            {node_id for item in batch for node_id in item["primaries"]}, key=order.get
        )
        node_ids = [
            node_id
            for primary in primaries
            for node_id in group_ids(frontier.headers, primary)
            if node_id in frontier.headers
        ]
        handoffs = [
            {
                "task": item["delivery"].task,
                "path": item["delivery"].path,
                "author_session": item["delivery"].author_session,
                "node_ids": sorted(set(item["delivery"].node_ids) & set(node_ids)),
            }
            for item in batch
        ]
        digest = hashlib.sha256("\0".join(primaries).encode()).hexdigest()[:12]
        pages = sorted(
            {
                page
                for node_id in node_ids
                for page in frontier.headers[node_id].metadata["source"].get("pages", [])
                if isinstance(page, int)
            }
        )
        files = sorted(
            [f"HomAlg/{value.replace('.', '/', 1)}.lean" for value in node_ids]
            + [f"literature/{key}/reviews/{value.split('.', 1)[1]}.md" for value in node_ids]
        )
        proposals.append(
            {
                "id": f"{key}.STMT.Review_{digest}",
                "metadata": {
                    "roadmap_status_sync": False,
                    "homalg": {
                        "doc": key,
                        "stage": "STMT",
                        "phase": REVIEW,
                        "chapter": batch[0]["chapter"],
                        "section": None,
                        "attempts": 0,
                        "pages": pages,
                        "granularity": "node",
                        "kind_group": "items",
                        "node_ids": node_ids,
                        "primary_nodes": primaries,
                        "handoffs": handoffs,
                    },
                },
                "node_ids": node_ids,
                "roadmap_refs": [f"{key}.STMT"],
                "write_set": {"files": files},
                "blockers": [],
            }
        )
    return proposals
