"""Validate model evidence before atomically importing unreviewed proposals."""

import copy
import json
import re
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg.documents import dump_metadata
from homalg.evolution.bundle import semantic_hash
from homalg.io import atomic_write
from homalg.relations import canonical_relation, load_relations, relation_id
from homalg.schemas import SchemaStore, load_yaml

NODE_MENTION = re.compile(
    r"\b[A-Z][A-Za-z]*[0-9]{4}[A-Za-z0-9]*\.[A-Z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*\b"
)


class EvolutionError(ValueError):
    """A validation failure that must leave authored files unchanged."""


def validate(store: SchemaStore, value: Any, schema: str) -> None:
    errors = store.validate(value, schema)
    if errors:
        raise EvolutionError(f"{schema}: {errors[0].json_path}: {errors[0].message}")


@contextmanager
def write_lock(repo: Path):
    """Serialize version allocation and relation appends across local commands."""
    import fcntl

    path = repo / ".homalg/evolution.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def commit_files(changes: dict[Path, str]) -> None:
    """Validate before entering here; roll back completed replacements on write failure."""
    before = {path: path.read_text(encoding="utf-8") if path.exists() else None for path in changes}
    written = []
    try:
        for path, text in changes.items():
            atomic_write(path, text)
            written.append(path)
    except Exception:
        for path in reversed(written):
            if before[path] is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, before[path])
        raise


def validate_output(repo: Path, output: dict[str, Any], bundle: dict[str, Any]) -> None:
    """Catch schema violations, unknown ids/documents, rejected triples and tampered inputs."""
    store = SchemaStore(repo / "schema")
    validate(store, output, "evolution-output.schema.json")
    if output["concept"] != bundle.get("concept", {}).get("id"):
        raise EvolutionError("Output concept does not match bundle concept")
    if bundle.get("bundle_sha256") != semantic_hash(bundle):
        raise EvolutionError("Bundle semantic hash is invalid; regenerate the bundle")
    nodes = {node["id"]: node for node in bundle["nodes"]}
    docs = {doc["doc_key"] for doc in bundle["documents"]}
    references = set(NODE_MENTION.findall(json.dumps(output, ensure_ascii=False)))
    references.update(node for stage in output["stages"] for node in stage["nodes"])
    for relation in output["proposed_relations"]:
        references.update((relation["source"], relation["target"]))
        if relation["source"] == relation["target"]:
            raise EvolutionError("Self relations are forbidden")
    unknown = references - nodes.keys()
    if unknown:
        raise EvolutionError("Unknown node ids: " + ", ".join(sorted(unknown)))
    for stage in output["stages"]:
        if stage["doc"] not in docs:
            raise EvolutionError(f"Unknown stage document: {stage['doc']}")
        if any(nodes[node]["doc"] != stage["doc"] for node in stage["nodes"]):
            raise EvolutionError(f"Stage nodes do not belong to {stage['doc']}")


def import_output(
    repo: Path,
    output: dict[str, Any],
    bundle: dict[str, Any],
    *,
    model: str,
    by: str | None = None,
    provider: str | None = None,
    usage: dict[str, int] | None = None,
    cost: float | None = None,
    max_cost: float | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append a new summary version and only previously unknown normalized relations."""
    validate_output(repo, output, bundle)
    stamp = (now or datetime.now(UTC)).date().isoformat()
    concept = output["concept"]
    summary_path = repo / "taxonomy/evolution" / f"{concept}.yaml"
    relations_path = repo / "taxonomy/relations" / f"llm-{stamp}.yaml"
    store = SchemaStore(repo / "schema")
    with write_lock(repo):
        summaries = (
            load_yaml(summary_path.read_text())
            if summary_path.exists()
            else {"schema_version": 1, "concept": concept, "summaries": []}
        )
        validate(store, summaries, "evolution.schema.json")
        if summaries["concept"] != concept:
            raise EvolutionError("Existing summary file has a different concept")
        # Read current authored relations, including headers, rather than trusting an old bundle.
        nodes = []
        for path in sorted((repo / "literature").glob("*/nodes.json")):
            nodes.extend(json.loads(path.read_text())["nodes"])
        all_relations = load_relations(repo, nodes, store)
        known = {
            canonical_relation(item["source"], item["type"], item["target"])
            for item in all_relations
        }
        known.update(
            canonical_relation(item["source"], item["type"], item["target"])
            for item in bundle["relations"]
        )
        relation_file = (
            load_yaml(relations_path.read_text())
            if relations_path.exists()
            else {"schema_version": 1, "relations": []}
        )
        validate(store, relation_file, "relations.schema.json")
        provenance = {
            "by": "llm",
            "model": model,
            "on": stamp,
            "prompt_version": bundle["prompt_version"],
            "bundle_commit": bundle["commit"],
            "bundle_sha256": bundle["bundle_sha256"],
        }
        for key, value in {
            "handle": by,
            "provider": provider,
            "usage": usage,
            "cost_usd": cost,
            "max_cost_usd": max_cost,
        }.items():
            if value is not None:
                provenance[key] = value
        version = max((item["version"] for item in summaries["summaries"]), default=0) + 1
        summary = {key: copy.deepcopy(value) for key, value in output.items() if key != "concept"}
        summary.update(version=version, provenance=provenance, review={"status": "unreviewed"})
        summaries["summaries"].append(summary)
        added, skipped = [], []
        for relation in output["proposed_relations"]:
            source, kind, target = triple = canonical_relation(
                relation["source"], relation["type"], relation["target"]
            )
            identifier = relation_id(*triple)
            if triple in known:
                skipped.append(identifier)
                continue
            known.add(triple)
            relation_provenance = {**provenance, "evidence": relation["evidence"]}
            if "confidence" in relation:
                relation_provenance["confidence"] = relation["confidence"]
            relation_file["relations"].append(
                {
                    "id": identifier,
                    "source": source,
                    "type": kind,
                    "target": target,
                    "provenance": relation_provenance,
                    "review": {"status": "unreviewed"},
                }
            )
            added.append(identifier)
        validate(store, summaries, "evolution.schema.json")
        validate(store, relation_file, "relations.schema.json")
        changes = {summary_path: dump_metadata(summaries)}
        if added:
            changes[relations_path] = dump_metadata(relation_file)
        commit_files(changes)
    return {
        "concept": concept,
        "version": version,
        "summary_file": str(summary_path),
        "relations_added": added,
        "relations_skipped": sorted(set(skipped)),
    }


def review(
    repo: Path,
    *,
    status: str,
    by: str,
    relation: str | None = None,
    concept: str | None = None,
    version: int | None = None,
    note: str | None = None,
    now: datetime | None = None,
    session: str | None = None,
    author_session: str | None = None,
    report: Path | None = None,
) -> dict[str, Any]:
    """Write a review in its protected registry; PR approval remains CODEOWNERS' responsibility."""
    if status not in {"accepted", "rejected"}:
        raise EvolutionError("Choose accepted or rejected")
    agent = any(value is not None for value in (session, author_session, report))
    if agent and not all((session, author_session, report)):
        raise EvolutionError("Agent review requires --session, --author-session and --report")
    from homalg.evolution.reviews import independent_review

    store = SchemaStore(repo / "schema")
    record = {"status": status, "by": by, "on": (now or datetime.now(UTC)).date().isoformat()}
    if note:
        record["note"] = note
    with write_lock(repo):
        if relation:
            nodes = []
            for path in sorted((repo / "literature").glob("*/nodes.json")):
                nodes.extend(json.loads(path.read_text())["nodes"])
            candidates = {
                item["id"]: item
                for item in load_relations(
                    repo, nodes, store, resolve_aliases=False, validate_reviews=False
                )
            }
            if relation not in candidates:
                raise EvolutionError(f"Unknown relation: {relation}")
            if agent:
                record = independent_review(
                    repo,
                    candidates[relation],
                    relation,
                    status=status,
                    by=by,
                    session=session,
                    author_session=author_session,
                    report=report,
                    note=note,
                )
            path = repo / "taxonomy/relations/_reviews.yaml"
            value = (
                load_yaml(path.read_text())
                if path.exists()
                else {"schema_version": 1, "reviews": {}}
            )
            value["reviews"][relation] = record
            schema = "relation-reviews.schema.json"
        else:
            if not concept or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", concept):
                raise EvolutionError("A valid concept is required for summary review")
            path = repo / "taxonomy/evolution" / f"{concept}.yaml"
            if not path.exists():
                raise EvolutionError(f"Unknown summary: {concept}")
            value = load_yaml(path.read_text())
            target = next((item for item in value["summaries"] if item["version"] == version), None)
            if target is None:
                raise EvolutionError(f"Unknown summary version: {version}")
            if agent:
                record = independent_review(
                    repo,
                    target,
                    f"{concept}:{version}",
                    status=status,
                    by=by,
                    session=session,
                    author_session=author_session,
                    report=report,
                    note=note,
                )
            target["review"] = record
            schema = "evolution.schema.json"
        validate(store, value, schema)
        atomic_write(path, dump_metadata(value))
    return {"file": str(path), "review": record}
