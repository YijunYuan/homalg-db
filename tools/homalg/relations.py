"""Canonical cross-document relations and vocabulary alias resolution."""

import copy
import hashlib
from pathlib import Path
from typing import Any

from homalg.retired import load_retired, resolve_retired, retirement_map
from homalg.schemas import SchemaStore, load_yaml


def canonical_relation(source: str, kind: str, target: str) -> tuple[str, str, str]:
    """Normalize inverse and symmetric relations before identity and deduplication."""
    if kind in {"specializes", "weakens"}:
        source, target = target, source
        kind = {"specializes": "generalizes", "weakens": "strengthens"}[kind]
    if kind in {"same_as", "equivalent_to", "reformulates"} and target < source:
        source, target = target, source
    return source, kind, target


def relation_id(source: str, kind: str, target: str, *, header: bool = False) -> str:
    """Generate the canonical relation id defined by section 12.3."""
    triple = canonical_relation(source, kind, target)
    digest = hashlib.sha1("|".join(triple).encode(), usedforsecurity=False).hexdigest()[:8]
    return f"rel-{'h-' if header else ''}{digest}"


def merged_ids(entries: list[dict[str, Any]]) -> dict[str, str]:
    """Resolve every taxonomy alias, rejecting cycles, duplicates and dangling targets."""
    table = {item["id"]: item for item in entries}
    if len(table) != len(entries):
        raise ValueError("Duplicate taxonomy id")
    resolved = {}
    for key in table:
        current = key
        seen = set()
        while True:
            if current in seen:
                raise ValueError(f"taxonomy-merge-cycle: {' -> '.join([*sorted(seen), current])}")
            if current not in table:
                raise ValueError(f"Unknown taxonomy merge target: {current}")
            seen.add(current)
            target = table[current].get("merged_into")
            if target is None:
                break
            current = target
        resolved[key] = current
    return resolved


def load_relations(
    repo: Path,
    nodes: list[dict[str, Any]],
    schemas: SchemaStore,
    *,
    resolve_aliases: bool = True,
    validate_reviews: bool = True,
) -> list[dict[str, Any]]:
    """Join authored relations with the only authoritative review registry."""
    retired = retirement_map(load_retired(repo, schemas))
    reviews_path = repo / "taxonomy/relations/_reviews.yaml"
    reviews_file = (
        load_yaml(reviews_path.read_text())
        if reviews_path.exists()
        else {
            "schema_version": 1,
            "reviews": {},
        }
    )
    errors = schemas.validate(reviews_file, "relation-reviews.schema.json")
    if errors:
        raise ValueError(f"{reviews_path}: {errors[0].message}")
    reviews = reviews_file["reviews"]
    candidates: list[tuple[dict[str, Any], bool]] = []
    for path in sorted((repo / "taxonomy/relations").glob("[!_]*.yaml")):
        record = load_yaml(path.read_text())
        errors = schemas.validate(record, "relations.schema.json")
        if errors:
            raise ValueError(f"{path}: {errors[0].message}")
        for relation in record["relations"]:
            if relation["review"] != {"status": "unreviewed"}:
                raise ValueError(f"{path}: relation reviews belong in _reviews.yaml")
            candidates.append((copy.deepcopy(relation), False))
    for node in nodes:
        authored = node["authored"]
        for related in authored.get("related", []):
            source, kind, target = canonical_relation(
                node["id"], related["type"], related["target"]
            )
            provenance: dict[str, Any] = {
                "by": "formalizer",
                "on": related["on"],
                "confidence": {"high": 0.9, "medium": 0.6, "low": 0.3}[related["confidence"]],
            }
            if authored.get("authors_of_formalization"):
                provenance["handle"] = authored["authors_of_formalization"][0]
            record = {
                "id": relation_id(source, kind, target, header=True),
                "source": source,
                "type": kind,
                "target": target,
                "provenance": provenance,
                "review": {"status": "unreviewed"},
            }
            if "note" in related:
                record["note"] = related["note"]
            candidates.append((record, True))
    seen = set()
    output = []
    for record, header in candidates:
        source, kind, target = canonical_relation(
            record["source"], record["type"], record["target"]
        )
        expected = relation_id(source, kind, target, header=header)
        if record["id"] != expected:
            raise ValueError(f"relations-valid: expected {expected}, got {record['id']}")
        canonical = record | {
            "source": source,
            "type": kind,
            "target": target,
            "review": reviews.get(expected, {"status": "unreviewed"}),
        }
        from homalg.evolution.reviews import validate_review

        if validate_reviews:
            validate_review(canonical, repo)
        # The permanent authored id and its review key survive a node move.
        # Only the public endpoints/deduplication use the current identities.
        if resolve_aliases:
            source = resolve_retired(source, retired) or source
            target = resolve_retired(target, retired) or target
        source, kind, target = canonical_relation(source, kind, target)
        triple = source, kind, target
        if source == target or triple in seen:
            raise ValueError(f"relations-valid: duplicate or self relation {expected}")
        seen.add(triple)
        record.update(
            source=source,
            type=kind,
            target=target,
            review=reviews.get(expected, {"status": "unreviewed"}),
        )
        output.append(record)
    return sorted(output, key=lambda relation: relation["id"])
