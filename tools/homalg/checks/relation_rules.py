"""Canonical relation identities, historical references and reviewed evolution records."""

from homalg.checks.context import Context, Finding
from homalg.checks.text_rules import finding
from homalg.relations import canonical_relation, relation_id
from homalg.schemas import load_yaml


def record_changed(ctx: Context, path: str, record: dict, *, field: str, key: str) -> bool:
    """Only changed records become blocking when historic node references dangle."""
    if not ctx.pr or path not in ctx.changed_paths:
        return False
    before = ctx.base_sources.get(path)
    if before is None:
        return True
    try:
        previous = load_yaml(before)
        old = next(
            (item for item in previous.get(field, []) if item.get(key) == record.get(key)), None
        )
        return old != record
    except (ValueError, AttributeError, TypeError):
        return True


def relations_valid(ctx: Context) -> list[Finding]:
    """Check canonical ids and duplicate/self edges across both file and header relations."""
    result = []
    seen = {}
    nodes = ctx.node_headers()
    for path, record, header in ctx.relation_records:
        source, kind, target = canonical_relation(
            record["source"], record["type"], record["target"]
        )
        expected = relation_id(source, kind, target, header=header)
        if record["id"] != expected:
            result.append(
                finding(
                    "relations-valid", path, f"Relation id must be {expected}, got {record['id']}"
                )
            )
        try:
            resolved = ctx.resolve_node(source), kind, ctx.resolve_node(target)
        except ValueError as error:
            result.append(finding("relations-valid", path, str(error)))
            continue
        if resolved[0] == resolved[2]:
            result.append(
                finding("relations-valid", path, "A relation cannot link a node to itself")
            )
        normalized = canonical_relation(*resolved)
        if normalized in seen:
            result.append(
                finding(
                    "relations-valid",
                    path,
                    f"Duplicate canonical relation also recorded in {seen[normalized]}",
                )
            )
        seen[normalized] = path
        for endpoint in (resolved[0], resolved[2]):
            if endpoint not in ctx.existing_nodes:
                changed = (
                    path in ctx.changed_paths
                    if header
                    else record_changed(ctx, path, record, field="relations", key="id")
                )
                blocking = bool(ctx.pr) and changed
                result.append(
                    finding(
                        "relations-valid" if blocking else "relation-dangling",
                        path,
                        f"Relation endpoint does not exist: {endpoint}",
                        severity="error" if blocking else "warning",
                    )
                )
        bridge = record.get("bridge")
        if bridge:
            candidate = nodes.get(bridge)
            if candidate is None or candidate.metadata.get("aux", {}).get("kind") != "bridge":
                result.append(
                    finding(
                        "relations-valid", path, "Relation bridge must be an existing bridge node"
                    )
                )
        if not record.get("provenance", {}).get("on"):
            result.append(
                finding("relations-valid", path, "Relation provenance requires a source date")
            )
    return result


def relation_review(ctx: Context) -> list[Finding]:
    """Only the owner-protected review registry can accept or reject a relation."""
    return [
        finding(
            "relation-review",
            path,
            "Relation files must carry only review: {status: unreviewed}; "
            "decisions belong in _reviews.yaml",
        )
        for path, record, header in ctx.relation_records
        if not header and record.get("review") != {"status": "unreviewed"}
    ]


def relation_reviews_valid(ctx: Context) -> list[Finding]:
    """Stale review ids remain auditable but are visible warnings."""
    known = {
        relation_id(record["source"], record["type"], record["target"], header=header)
        for _, record, header in ctx.relation_records
    }
    return [
        finding(
            "relation-reviews-valid",
            "taxonomy/relations/_reviews.yaml",
            f"Review refers to a missing canonical relation: {identifier}",
            severity="warning",
        )
        for identifier in ctx.relation_reviews.get("reviews", {})
        if identifier not in known
    ]


def relations_year_order(ctx: Context) -> list[Finding]:
    """Historical direction mistakes are warnings because editions may postdate their results."""
    result = []
    for path, record, _ in ctx.relation_records:
        source, target = record["source"].split(".")[0], record["target"].split(".")[0]
        if source not in ctx.all_docs or target not in ctx.all_docs:
            continue
        source_year, target_year = ctx.all_docs[source]["year"], ctx.all_docs[target]["year"]
        if (record["type"] == "precursor_of" and source_year > target_year) or (
            record["type"] in {"cites", "corrects"} and target_year > source_year
        ):
            result.append(
                finding(
                    "relations-year-order",
                    path,
                    f"{record['type']} has unexpected publication-year direction "
                    f"({source_year}, {target_year})",
                    severity="warning",
                )
            )
    return result


def evolution_valid(ctx: Context) -> list[Finding]:
    """Retain historical summaries while blocking newly introduced hallucinated nodes."""
    result = []
    concepts = {entry["id"] for entry in ctx.taxonomy.get("concepts", {}).get("concepts", [])}
    for path, record in ctx.evolution_files.items():
        if record["concept"] not in concepts:
            result.append(
                finding(
                    "evolution-valid", path, "Evolution concept must exist in the concept registry"
                )
            )
        versions = [summary["version"] for summary in record["summaries"]]
        if len(set(versions)) != len(versions):
            result.append(finding("evolution-valid", path, "Summary versions must be unique"))
        for summary in record["summaries"]:
            if not summary["provenance"].get("bundle_sha256"):
                result.append(
                    finding(
                        "evolution-valid", path, "Every summary requires provenance.bundle_sha256"
                    )
                )
            endpoints = {node for stage in summary["stages"] for node in stage["nodes"]}
            for relation in summary.get("proposed_relations", []):
                endpoints.update((relation["source"], relation["target"]))
            for identifier in endpoints:
                try:
                    target = ctx.resolve_node(identifier)
                except ValueError as error:
                    result.append(finding("evolution-valid", path, str(error)))
                    continue
                if target not in ctx.existing_nodes:
                    blocking = record_changed(ctx, path, summary, field="summaries", key="version")
                    result.append(
                        finding(
                            "evolution-valid" if blocking else "evolution-dangling",
                            path,
                            f"Summary version {summary['version']} references "
                            f"missing node {identifier}",
                            severity="error" if blocking else "warning",
                        )
                    )
            for stage in summary["stages"]:
                if stage["doc"] not in ctx.all_docs or any(
                    node.split(".")[0] != stage["doc"] for node in stage["nodes"]
                ):
                    result.append(
                        finding(
                            "evolution-valid",
                            path,
                            f"Stage {stage['period']} has an unregistered document "
                            "or nodes from a different document",
                        )
                    )
    return result
