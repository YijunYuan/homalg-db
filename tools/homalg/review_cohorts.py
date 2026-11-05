"""Agent-only union registration with exact per-node author/reviewer identities."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from homalg import review, workflow
from homalg.engine import task
from homalg.io import atomic_create, json_text
from homalg.leanexport import declaration_map, export_lean, file_fingerprint, workspace_lock
from homalg.nodeio import header_mapping, replace_header
from homalg.repository import canonical_root
from homalg.review_policy import agent_review_record
from homalg.schemas import SchemaStore

MANIFEST_KIND = "fidelity-review-cohorts"
SNAPSHOT_KIND = "fidelity-cohort-input-snapshot"


def _fields(value: Any, required: set[str], optional: set[str] = frozenset()) -> None:
    if (
        not isinstance(value, dict)
        or not required <= value.keys()
        or value.keys() - required - optional
    ):
        raise ValueError("Invalid cohort contract fields")


def _version(value: dict, kind: str) -> None:
    if (
        type(value.get("schema_version")) is not int
        or value["schema_version"] != 1
        or value.get("kind") != kind
    ):
        raise ValueError("Unsupported cohort contract kind/version")


@dataclass(frozen=True)
class Cohort:
    by: str
    session: str
    author_session: str
    node_ids: tuple[str, ...]
    note: str = ""

    def record(self) -> dict[str, Any]:
        return asdict(self) | {"node_ids": list(self.node_ids)}


def _cohorts(repo: Path, manifest: Any) -> list[Cohort]:
    _fields(manifest, {"schema_version", "kind", "cohorts"})
    _version(manifest, MANIFEST_KIND)
    if not isinstance(manifest["cohorts"], list) or not manifest["cohorts"]:
        raise ValueError("A review manifest needs nonempty cohorts")
    login = SchemaStore(repo / "schema").schemas["common.schema.json"]["$defs"]["Login"]
    result = []
    for entry in manifest["cohorts"]:
        _fields(entry, {"by", "session", "author_session", "node_ids"}, {"note"})
        if not all(
            isinstance(entry[name], str) and entry[name].strip()
            for name in ("by", "session", "author_session")
        ):
            raise ValueError("Cohorts require actual nonempty reviewer and author identities")
        if not Draft202012Validator(login).is_valid(entry["by"]):
            raise ValueError("Cohort by must be a valid short reviewer identifier")
        if not isinstance(entry.get("note", ""), str) or not isinstance(entry["node_ids"], list):
            raise ValueError("Invalid cohort note or node list")
        if not all(isinstance(node, str) for node in entry["node_ids"]):
            raise ValueError("Cohort node ids must be strings")
        ids = review._batch_ids(entry["node_ids"])
        cohort = Cohort(
            entry["by"],
            entry["session"].strip(),
            entry["author_session"].strip(),
            tuple(ids),
            entry.get("note", ""),
        )
        agent_review_record(
            repo, by=cohort.by, session=cohort.session, author_session=cohort.author_session
        )
        result.append(cohort)
    review._batch_ids([node for cohort in result for node in cohort.node_ids])
    return result


def _read(repo: Path, name: str | Path) -> tuple[dict, dict]:
    if not isinstance(name, (str, Path)):
        raise ValueError("Evidence path must name a regular local build file")
    path = repo / name
    build = repo / "build"
    if (
        path != path.resolve()
        or build.resolve() != build
        or not path.is_relative_to(build)
        or not path.is_file()
    ):
        raise ValueError("Cohort evidence must be a regular file inside this repository's build/")
    fingerprint = file_fingerprint(path)
    data = json.loads(path.read_text())
    if file_fingerprint(path) != fingerprint:
        raise ValueError("Cohort evidence changed while reading")
    return data, {"path": str(path.relative_to(repo)), "fingerprint": fingerprint}


def _reference(repo: Path, reference: Any) -> dict:
    _fields(reference, {"path", "fingerprint"})
    data, actual = _read(repo, reference["path"])
    if actual != reference:
        raise ValueError("Cohort evidence changed or snapshot is stale")
    return data


def _binding(repo: Path, handoff: dict, cohorts: list[Cohort]) -> tuple[dict, list[dict]]:
    common = {
        "schema_version",
        "kind",
        "repo",
        "task",
        "contract",
        "ready_for_review",
        "approval",
        "task_complete",
    }
    optional = {"created_at", "validation", "pending_review_renewal", "workspace", "recorded"}
    _fields(handoff, common | {"deliveries"}, optional)
    _version(handoff, "author-handoff-batch")
    workspace = handoff.get("workspace") or handoff.get("repo")
    if (
        workspace not in {str(repo), canonical_root(repo)}
        or handoff.get("ready_for_review") is not True
        or handoff.get("approval") is not False
        or handoff.get("task_complete") is not False
    ):
        raise ValueError("Expected a successful author handoff batch for this repository")
    record = task(repo, handoff["task"])
    portable = all(
        isinstance(item, dict) and item.get("author_inputs", {}).get("schema_version") == 2
        for item in handoff.get("deliveries") or [{}]
    )
    if portable:
        # Settlement may narrow the author task later; judge the delivery by its own scope.
        contract = handoff.get("contract") or {}
        if record["id"] != contract.get("id"):
            raise ValueError("Author handoff names a different task")
        record = {
            "id": contract["id"],
            "write_set": contract["write_set"],
            "metadata": {"homalg": contract["homalg"]},
        }
    elif workflow._contract(record) != handoff.get("contract"):
        raise ValueError("Author handoff task scope changed")
    deliveries = handoff.get("deliveries")
    if not isinstance(deliveries, list) or not deliveries:
        raise ValueError("Author handoff has no deliveries")
    authors = {}
    for delivery in deliveries:
        if (
            not isinstance(delivery, dict)
            or not isinstance(delivery.get("author_session"), str)
            or not delivery["author_session"].strip()
        ):
            raise ValueError("Invalid author delivery")
        author = delivery["author_session"]
        if author in authors:
            raise ValueError("Author handoff contains duplicate author sessions")
        authors[author] = delivery
    selected = {}
    for cohort in cohorts:
        selected.setdefault(cohort.author_session, []).extend(cohort.node_ids)
    chosen = []
    for author, ids in selected.items():
        delivery = authors.get(author)
        if delivery is None:
            raise ValueError("Cohort author is absent from the actual handoff")
        _fields(
            delivery,
            common | {"author_session", "node_ids", "author_inputs", "compiled"},
            optional,
        )
        _version(delivery, "author-handoff")
        if (
            any(delivery.get(key) != handoff.get(key) for key in ("repo", "task", "contract"))
            or delivery.get("ready_for_review") is not True
            or delivery.get("approval") is not False
            or delivery.get("task_complete") is not False
        ):
            raise ValueError("Cohort delivery differs from its handoff")
        owned = delivery.get("node_ids")
        if not isinstance(owned, list) or not all(isinstance(node, str) for node in owned):
            raise ValueError("Invalid delivery node ids")
        review._batch_ids(owned)
        if set(ids) != set(owned):
            raise ValueError("Cohorts must cover each included author's complete delivery")
        nodes = workflow._nodes(repo, record, tuple(owned))
        if [node["id"] for node in nodes.values()] != owned:
            raise ValueError("Author delivery node scope changed")
        chosen.append(delivery)
    return record, chosen


def _author_inputs(repo: Path, deliveries: list[dict]) -> dict:
    snapshots, union = review.freeze_authoring_batch_inputs(
        repo, [item["node_ids"] for item in deliveries]
    )
    if any(
        snapshot != delivery.get("author_inputs")
        for snapshot, delivery in zip(snapshots, deliveries, strict=True)
    ):
        raise ValueError("Author delivery is stale; current inputs require reassessment")
    return union


def _prepare(repo: Path, cohorts: list[Cohort], now: datetime | None) -> list[tuple[Cohort, dict]]:
    return [
        (
            cohort,
            review._prepare_review(
                repo,
                node,
                by=cohort.by,
                session=cohort.session,
                author_session=cohort.author_session,
                human=False,
                now=now,
            ),
        )
        for cohort in cohorts
        for node in cohort.node_ids
    ]


def _unchanged(prepared: list[tuple[Cohort, dict]]) -> None:
    if any(
        item["path"].read_text() != item["source"]
        or item["report_path"].read_text() != item["report"]
        for _, item in prepared
    ):
        raise ValueError("The node or report changed during cohort review")


def _guard(repo: Path, references: list[dict], task_id: str, contract: dict) -> None:
    for reference in references:
        _reference(repo, reference)
    if workflow._contract(task(repo, task_id)) != contract:
        raise ValueError("Cohort task scope changed")


def snapshot(repo: Path, handoff: Path, *, manifest: Path, out: Path) -> dict:
    """Freeze real multi-author reports; create no approval, export or lock."""
    repo = repo.resolve()
    target = workflow._local_output(repo, out)
    with workspace_lock(repo):
        review._require_finished_transactions(repo)
        manifest_data, manifest_ref = _read(repo, manifest)
        cohorts = _cohorts(repo, manifest_data)
        handoff_data, handoff_ref = _read(repo, handoff)
        record, deliveries = _binding(repo, handoff_data, cohorts)
        prepared = _prepare(repo, cohorts, None)
        author_inputs = _author_inputs(repo, deliveries)
        ids = [item["id"] for _, item in prepared]
        frozen = review.freeze_fidelity_inputs(repo, ids)
        _unchanged(prepared)
        if review.freeze_authoring_inputs(repo, ids) != author_inputs:
            raise ValueError("Batch author inputs changed while freezing cohort reports")
        review._assert_snapshot(repo, ids, frozen)
        _guard(repo, [manifest_ref, handoff_ref], record["id"], workflow._contract(record))
        result = {
            "schema_version": 1,
            "kind": SNAPSHOT_KIND,
            "repo": str(repo),
            "task": record["id"],
            "contract": workflow._contract(record),
            "handoff": handoff_ref,
            "manifest": manifest_ref,
            "cohorts": [cohort.record() for cohort in cohorts],
            "inputs": frozen,
            "approval": False,
            "task_complete": False,
        }
        atomic_create(target, json_text(result))
        return result


def register(repo: Path, snapshot_path: Path, *, now: datetime | None = None) -> dict[str, dict]:
    """Register all cohorts with one fresh export and one guarded union transaction."""
    repo = repo.resolve()
    with workspace_lock(repo):
        review._require_finished_transactions(repo)
        bundle, bundle_ref = _read(repo, snapshot_path)
        _fields(
            bundle,
            {
                "schema_version",
                "kind",
                "repo",
                "task",
                "contract",
                "handoff",
                "manifest",
                "cohorts",
                "inputs",
                "approval",
                "task_complete",
            },
        )
        _version(bundle, SNAPSHOT_KIND)
        if (
            bundle["repo"] != str(repo)
            or bundle["approval"] is not False
            or bundle["task_complete"] is not False
        ):
            raise ValueError("Invalid cohort snapshot repository or approval fields")
        cohorts = _cohorts(
            repo, {"schema_version": 1, "kind": MANIFEST_KIND, "cohorts": bundle["cohorts"]}
        )
        actual = _cohorts(repo, _reference(repo, bundle["manifest"]))
        if cohorts != actual:
            raise ValueError("Cohort identities differ from their frozen manifest")
        record, deliveries = _binding(repo, _reference(repo, bundle["handoff"]), cohorts)
        if record["id"] != bundle["task"] or workflow._contract(record) != bundle["contract"]:
            raise ValueError("Cohort snapshot task scope changed")
        prepared = _prepare(repo, cohorts, now)
        author_inputs = _author_inputs(repo, deliveries)
        ids = [item["id"] for _, item in prepared]
        frozen = review.freeze_fidelity_inputs(repo, ids)
        if frozen != bundle["inputs"]:
            raise ValueError("Review inputs changed or cohort snapshot is stale")
        _unchanged(prepared)

        def guard() -> None:
            _guard(
                repo,
                [bundle_ref, bundle["manifest"], bundle["handoff"]],
                record["id"],
                bundle["contract"],
            )

        guard()
        raw = export_lean(
            repo,
            doc=ids[0].split(".", 1)[0],
            out=repo / "build/registration-export.json",
            merge=False,
            modules=[f"HomAlg.{node_id}" for node_id in ids],
        )
        export_path = repo / "literature" / ids[0].split(".", 1)[0] / "nodes.json"
        exported_files = {str(export_path): file_fingerprint(export_path)}
        exported = declaration_map(raw)
        review._assert_snapshot(repo, ids, frozen)
        if review.freeze_authoring_inputs(repo, ids) != author_inputs:
            raise ValueError("Batch author inputs changed during cohort registration")
        guard()
        schemas = SchemaStore(repo / "schema")
        locks, updates = {}, []
        for cohort, item in prepared:
            lock = review._review_lock(
                item,
                exported,
                by=cohort.by,
                session=cohort.session,
                human=False,
                note=cohort.note,
                now=now,
            )
            metadata = header_mapping(item["source"], item["header"])
            metadata["fidelity"]["reviewed"] = lock
            locks[item["id"]] = lock
            updates.append(
                {
                    "path": str(item["path"]),
                    "before": item["source"],
                    "after": replace_header(item["source"], metadata, schemas),
                }
            )
        review._write_batch(
            repo,
            ids,
            frozen,
            updates,
            exported_files,
            extra_guard=guard,
            evidence={"kind": SNAPSHOT_KIND, "snapshot": bundle_ref, "cohorts": bundle["cohorts"]},
        )
        return locks
