"""Explicit schema migration registry with preflight validation and reversible file publication."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from homalg.documents import dump_metadata
from homalg.human import require_idle
from homalg.io import atomic_bytes, atomic_write, json_text
from homalg.schemas import SchemaStore, load_yaml

CURRENT_SCHEMA_VERSION = 1
MIGRATIONS: dict[tuple[int, int], Callable[[str, dict[str, Any]], dict[str, Any]]] = {}


def inputs(repo: Path) -> list[tuple[Path, str]]:
    """Enumerate public versioned metadata, excluding private sources and derived build outputs."""
    output = []
    review_policy = repo / "horizon/review-policy.yaml"
    if review_policy.exists():
        output.append((review_policy, "review-policy.schema.json"))
    names = {
        "document.yaml": "document",
        "claim.yaml": "claim",
        "nodes.json": "nodes-file",
        "inventory.yaml": "inventory",
        "retired.yaml": "retired",
    }
    for directory in sorted((repo / "literature").glob("*")):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        for filename, schema in names.items():
            path = directory / filename
            if path.exists():
                output.append((path, f"{schema}.schema.json"))
    for name in ("tags", "concepts", "policy", "foundations-template"):
        path = repo / "taxonomy" / f"{name}.yaml"
        schema = name
        if path.exists():
            output.append((path, f"{schema}.schema.json"))
    for name, schema in (("relations", "relations"), ("evolution", "evolution")):
        for path in sorted((repo / "taxonomy" / name).glob("*.yaml")):
            output.append(
                (
                    path,
                    "relation-reviews.schema.json"
                    if path.name == "_reviews.yaml"
                    else f"{schema}.schema.json",
                )
            )
    return output


def migrate(repo: Path, target: int, *, dry_run: bool = False) -> dict[str, Any]:
    """Apply registered forward migrations only; unknown versions never get silently relabeled."""
    if target != CURRENT_SCHEMA_VERSION:
        raise ValueError(
            f"This release supports schema version {CURRENT_SCHEMA_VERSION}, not {target}"
        )
    require_idle(repo)
    schemas = SchemaStore(repo / "schema")
    writes: dict[Path, str] = {}
    checked = []
    for path, schema in inputs(repo):
        original = path.read_text()
        data = json.loads(original) if path.suffix == ".json" else load_yaml(original)
        version = data.get("schema_version")
        if not isinstance(version, int) or version > target:
            raise ValueError(f"{path}: unsupported source schema version {version}")
        changed = False
        while version < target:
            transform = MIGRATIONS.get((version, version + 1))
            if transform is None:
                raise ValueError(
                    f"{path}: no registered migration from schema {version} to {version + 1}"
                )
            data = transform(schema, data)
            if data.get("schema_version") != version + 1:
                raise ValueError(f"Migration {version} did not produce the required target version")
            version += 1
            changed = True
        errors = schemas.validate(data, schema)
        if errors:
            raise ValueError(f"{path}: {errors[0].message}")
        checked.append(path.relative_to(repo).as_posix())
        if changed:
            writes[path] = json_text(data) if path.suffix == ".json" else dump_metadata(data)
    if not dry_run:
        original_bytes = {path: path.read_bytes() for path in writes}
        try:
            for path, text in writes.items():
                atomic_write(path, text)
        except BaseException:
            for path, data in original_bytes.items():
                atomic_bytes(path, data)
            raise
    return {
        "target_version": target,
        "checked": checked,
        "changed": [str(path.relative_to(repo)) for path in writes],
        "dry_run": dry_run,
    }
