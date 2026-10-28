"""Deterministic semantic inputs shared by indexing and local model runs."""

import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg.relations import merged_ids

PROMPT_VERSION = 1
ROOT = Path(__file__).resolve().parents[3]


def canonical_json(value: Any) -> str:
    """The specification's whitespace-free UTF-8 canonical JSON representation."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def semantic_hash(bundle: dict[str, Any]) -> str:
    """Exclude summaries, provenance, prompt and derived current hashes."""
    inputs = {key: bundle[key] for key in ("concept", "documents", "nodes", "relations")}
    return hashlib.sha256(canonical_json(inputs).encode("utf-8")).hexdigest()


def build_bundle(
    index: dict[str, Any],
    concept: str,
    *,
    prompt_version: int = PROMPT_VERSION,
    repo: Path | None = None,
    include_prompt: bool = True,
) -> dict[str, Any]:
    """Build semantic inputs from the index and versioned local prompt/schema templates."""
    aliases = merged_ids(index["concepts"])
    if concept not in aliases:
        raise ValueError(f"Unknown concept: {concept}")
    concept = aliases[concept]
    concept_record = copy.deepcopy(
        next(item for item in index["concepts"] if item["id"] == concept)
    )
    concept_record.pop("current_bundle_sha256", None)
    docs = {item["document"]["doc_key"]: item["document"] for item in index["documents"]}
    nodes = []
    for node in index["nodes"]:
        authored = node["authored"]
        memberships = {
            aliases[value] for group in authored.get("concepts", {}).values() for value in group
        }
        if concept not in memberships:
            continue
        value = {
            "id": node["id"],
            "doc": authored["doc"],
            "year": docs[authored["doc"]]["year"],
            "kind": authored["kind"],
            "label": authored["source"]["label"],
            "statement_md": authored["statement_md"],
            "description_md": authored.get("description_md", ""),
            "lean_type": "\n\n".join(
                f"{decl['name']} : {decl['type']}"
                for decl in node.get("derived", {}).get("decl_info", [])
            ),
            "fidelity": copy.deepcopy(authored["fidelity"]),
            "mathlib": copy.deepcopy(authored.get("mathlib")),
        }
        if "statement_original_md" in authored:
            value["statement_original_md"] = authored["statement_original_md"]
        nodes.append(value)
    nodes.sort(key=lambda item: (item["year"], item["doc"], item["id"]))
    ids = {node["id"] for node in nodes}
    doc_ids = {node["doc"] for node in nodes}
    relations = [
        copy.deepcopy(item)
        for item in index["relations"]
        if item["source"] in ids
        and item["target"] in ids
        and item["review"]["status"] in {"accepted", "rejected"}
    ]
    previous = next(
        (item["summaries"] for item in index["evolution"] if item["concept"] == concept), []
    )
    bundle = {
        "schema_version": 1,
        "concept": concept_record,
        "documents": [
            copy.deepcopy(docs[key])
            for key in sorted(doc_ids, key=lambda key: (docs[key]["year"], key))
        ],
        "nodes": nodes,
        "relations": sorted(relations, key=lambda item: item["id"]),
        "summaries": copy.deepcopy(previous),
        "commit": index["generator"].get("commit", "unknown"),
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "prompt_version": prompt_version,
    }
    bundle["bundle_sha256"] = semantic_hash(bundle)
    if not include_prompt:
        return bundle
    root = repo or ROOT
    template = Path(__file__).parent / "prompts" / f"evolution-v{prompt_version}.md"
    if not template.is_file():
        raise ValueError(f"Unknown prompt version: {prompt_version}")
    schema = (root / "schema/evolution-output.schema.json").read_text(encoding="utf-8").rstrip()
    common = json.loads((root / "schema/common.schema.json").read_text(encoding="utf-8"))["$defs"]
    definitions = {key: common[key] for key in ("NodeId", "DocKey", "SlugId", "RelationType")}
    bundle["prompt"] = (
        template.read_text(encoding="utf-8")
        .replace("{{OUTPUT_SCHEMA}}", schema)
        .replace("{{SHARED_DEFINITIONS}}", canonical_json(definitions))
        .replace("{{BUNDLE}}", canonical_json(bundle))
    )
    return bundle


def summary_status(index: dict[str, Any]) -> list[dict[str, Any]]:
    """Report the latest version per canonical concept, including unchanged inputs."""
    results = []
    for concept in index["concepts"]:
        if concept.get("merged_into"):
            continue
        bundle = build_bundle(index, concept["id"], include_prompt=False)
        latest = max(bundle["summaries"], key=lambda item: item["version"], default=None)
        stale = (
            latest is not None
            and latest["provenance"].get("bundle_sha256") != bundle["bundle_sha256"]
        )
        results.append(
            {
                "concept": concept["id"],
                "summary": "none" if latest is None else "stale" if stale else "current",
                "version": latest["version"] if latest else None,
                "since_commit": latest["provenance"].get("bundle_commit") if latest else None,
                "current_bundle_sha256": bundle["bundle_sha256"],
            }
        )
    return results
