"""Extract authored node metadata, preserving local Lean-derived records (R7.5)."""

import json
import tomllib
from pathlib import Path
from typing import Any

from homalg import NODES_JSON_GENERATOR
from homalg.headers import parse_header
from homalg.repository import node_paths
from homalg.schemas import SchemaStore


def extract_document(repo: Path, key: str, schemas: SchemaStore) -> dict[str, Any]:
    """Create a deterministic nodes record without inventing Lean-derived fields."""
    target = repo / "literature" / key / "nodes.json"
    previous = json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
    if previous is not None:
        errors = schemas.validate(previous, "nodes-file.schema.json")
        if errors:
            raise ValueError(f"Cannot preserve invalid {target}: {errors[0].message}")
        if previous["doc_key"] != key:
            raise ValueError(f"{target} belongs to a different document")
    old_nodes = {node["id"]: node for node in previous["nodes"]} if previous else {}
    if previous and len(old_nodes) != len(previous["nodes"]):
        raise ValueError(f"Cannot preserve duplicate node ids in {target}")
    nodes = []
    for path in node_paths(repo, [key]):
        header = parse_header(path.read_text(encoding="utf-8"))
        errors = schemas.validate(header.metadata, "node-header.strict.schema.json")
        if errors:
            raise ValueError(f"{path}:{header.yaml_line}: {errors[0].message}")
        expected_id = f"{key}.{path.stem}"
        if header.metadata["id"] != expected_id or header.metadata["doc"] != key:
            raise ValueError(f"{path}: header id/doc does not match its path")
        nodes.append(
            {
                "id": expected_id,
                "authored": header.authored(),
                "derived": old_nodes.get(expected_id, {}).get("derived"),
            }
        )
    config = tomllib.loads((repo / "lakefile.toml").read_text(encoding="utf-8"))
    mathlib = next(require for require in config["require"] if require["name"] == "mathlib")
    lean = (
        previous["lean"]
        if previous
        else {
            "toolchain": (repo / "lean-toolchain").read_text(encoding="utf-8").strip(),
            "mathlib_rev": mathlib["rev"],
        }
    )
    result = {
        "schema_version": 1,
        "generator": {"name": "homalg", "version": str(NODES_JSON_GENERATOR)},
        "doc_key": key,
        "lean": lean,
        "nodes": nodes,
    }
    errors = schemas.validate(result, "nodes-file.schema.json")
    if errors:
        raise ValueError(f"Cannot extract {key}: {errors[0].message}")
    return result
