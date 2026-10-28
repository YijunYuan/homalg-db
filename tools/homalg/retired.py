"""Resolve permanent node tombstones without rewriting authored identities or reviews."""

from pathlib import Path
from typing import Any

from homalg.schemas import SchemaStore, load_yaml


def retirement_map(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Reject reused/ambiguous ids and cycles before a tombstone reaches public output."""
    result = {record["id"]: record for record in records}
    if len(result) != len(records):
        raise ValueError("Duplicate retired node id")
    for identifier in result:
        resolve_retired(identifier, result)
    return result


def resolve_retired(identifier: str, records: dict[str, dict[str, Any]]) -> str | None:
    """Follow moved/merged chains; a pruned endpoint deliberately has no replacement."""
    seen = set()
    while identifier in records:
        if identifier in seen:
            raise ValueError(f"Retired node cycle at {identifier}")
        seen.add(identifier)
        record = records[identifier]
        if record["kind"] == "pruned":
            return None
        identifier = record["moved_to" if record["kind"] == "moved" else "merged_into"]
    return identifier


def load_retired(repo: Path, schemas: SchemaStore | None = None) -> list[dict[str, Any]]:
    """Read schema-checked historical records from every document, including cross-doc moves."""
    schemas = schemas or SchemaStore(repo / "schema")
    records = []
    for path in sorted((repo / "literature").glob("*/retired.yaml")):
        value = load_yaml(path.read_text())
        errors = schemas.validate(value, "retired.schema.json")
        if errors:
            raise ValueError(f"{path}: {errors[0].message}")
        for record in value["retired"]:
            if record["id"].split(".", 1)[0] != path.parent.name:
                raise ValueError(
                    f"Retired id does not belong to {path.parent.name}: {record['id']}"
                )
            records.append(record)
    retirement_map(records)
    return sorted(records, key=lambda record: record["id"])
