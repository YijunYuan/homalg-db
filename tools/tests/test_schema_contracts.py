"""Contract tests for bootstrap schemas, published data shapes and vocabulary."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from homalg.schemas import SchemaStore, load_yaml

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
GOOD = FIXTURES / "good"


@pytest.fixture(scope="module")
def schemas() -> SchemaStore:
    """Load the complete local contract graph once per test module."""
    return SchemaStore(ROOT / "schema")


def read_json(path: Path) -> Any:
    """Read a contract example without YAML's scalar conversions."""
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_graph_is_valid_and_every_reference_resolves(schemas: SchemaStore) -> None:
    """Even unused schema branches must resolve without a network fetch."""
    schemas.check_schemas()

    def references(value: Any) -> list[str]:
        if isinstance(value, dict):
            return ([value["$ref"]] if "$ref" in value else []) + [
                reference for item in value.values() for reference in references(item)
            ]
        if isinstance(value, list):
            return [reference for item in value for reference in references(item)]
        return []

    for schema in schemas.schemas.values():
        resolver = schemas.registry.resolver(base_uri=schema["$id"])
        for reference in references(schema):
            resolver.lookup(reference)


@pytest.mark.parametrize(
    ("file", "schema"),
    [
        ("document.json", "document.schema.json"),
        ("claim.json", "claim.schema.json"),
        ("node-header.json", "node-header.strict.schema.json"),
        ("nodes.json", "nodes-file.schema.json"),
        ("index.json", "index.schema.json"),
        ("evolution-output.json", "evolution-output.schema.json"),
        *[
            (f"site/{name}.json", f"site/{name}.schema.json")
            for name in (
                "manifest",
                "document-bundle",
                "node-record",
                "search",
                "taxonomy",
                "global-graph",
                "global-dag",
                "evolution",
                "health",
            )
        ],
    ],
)
def test_positive_contract_examples(schemas: SchemaStore, file: str, schema: str) -> None:
    """Hand-authored examples are independent of the forthcoming data generators."""
    assert schemas.validate(read_json(GOOD / file), schema) == []


@pytest.mark.parametrize(
    ("directory", "file", "schema", "validator"),
    [
        ("schema-date-time", "claim.json", "claim.schema.json", "format"),
        ("schema-uri", "document.json", "document.schema.json", "format"),
        (
            "schema-header",
            "node-header.json",
            "node-header.strict.schema.json",
            "unevaluatedProperties",
        ),
    ],
)
def test_negative_contract_examples(
    schemas: SchemaStore,
    directory: str,
    file: str,
    schema: str,
    validator: str,
) -> None:
    """Formats and authored/derived separation must be real validation gates."""
    errors = schemas.validate(read_json(FIXTURES / "bad" / directory / file), schema)
    assert any(error.validator == validator for error in errors)


@pytest.mark.parametrize("field", ["commit", "generated_at"])
def test_committed_nodes_reject_volatile_generator_fields(
    schemas: SchemaStore,
    field: str,
) -> None:
    """Committed nodes must remain stable across runs and commits."""
    nodes = read_json(GOOD / "nodes.json")
    nodes["generator"][field] = "2000-01-01T00:00:00Z" if field == "generated_at" else "abc"
    assert schemas.validate(nodes, "nodes-file.schema.json")


@pytest.mark.parametrize("field", ["axioms", "transitive_sorry", "status"])
def test_committed_nodes_reject_global_derived_fields(schemas: SchemaStore, field: str) -> None:
    """Cross-document closure belongs only in the ephemeral index."""
    nodes = read_json(GOOD / "nodes.json")
    nodes["nodes"][0]["derived"][field] = [] if field == "axioms" else True
    assert schemas.validate(nodes, "nodes-file.schema.json")


@pytest.mark.parametrize("field", ["status", "axioms", "module", "statement_md"])
def test_authored_headers_reject_generated_fields(schemas: SchemaStore, field: str) -> None:
    """The strict header rejects both computed fields and extracted Markdown fields."""
    header = read_json(GOOD / "node-header.json")
    header[field] = "unexpected"
    assert schemas.validate(header, "node-header.strict.schema.json")


def test_dispute_resolution_constraints(schemas: SchemaStore) -> None:
    """Confirmed disputes cannot be withdrawn; statements cannot use proof-route."""
    header = read_json(GOOD / "node-header.json")
    dispute = {
        "status": "resolved",
        "kind": "statement",
        "reason": "Synthetic correction",
        "confirmed_by": "fixture-reviewer",
        "confirmed_on": "2000-01-01",
        "resolution": {"via": "erratum", "by": "fixture-reviewer", "on": "2000-01-02"},
    }
    header["dispute"] = dispute
    assert not schemas.validate(header, "node-header.strict.schema.json")
    for via in ("withdrawn", "proof-route"):
        changed = copy.deepcopy(header)
        changed["dispute"]["resolution"]["via"] = via
        assert schemas.validate(changed, "node-header.strict.schema.json")


def test_site_evolution_requires_computed_staleness(schemas: SchemaStore) -> None:
    """The normative site contract adds per-summary staleness to stored summaries."""
    evolution = read_json(GOOD / "site/evolution.json")
    summary = {
        "version": 1,
        "provenance": {"by": "human", "on": "2000-01-01"},
        "narrative_md": "A synthetic summary.",
        "stages": [],
        "review": {"status": "unreviewed"},
    }
    evolution["summaries"].append(summary)
    assert schemas.validate(evolution, "site/evolution.schema.json")
    summary["stale"] = False
    assert not schemas.validate(evolution, "site/evolution.schema.json")


def test_site_bundle_excludes_bibtex(schemas: SchemaStore) -> None:
    """The lightweight site document record must not carry the full bibliography."""
    bundle = read_json(GOOD / "site/document-bundle.json")
    bundle["document"]["bibtex"] = "@misc{fixture}"
    assert schemas.validate(bundle, "site/document-bundle.schema.json")


def test_taxonomy_contracts_and_references(schemas: SchemaStore) -> None:
    """The initial vocabulary is unique, acyclic and linked only to existing entries."""
    taxonomy = ROOT / "taxonomy"
    documents = {}
    for stem in ("tags", "concepts", "policy", "foundations-template", "relation-reviews"):
        path = taxonomy / (
            "relations/_reviews.yaml" if stem == "relation-reviews" else f"{stem}.yaml"
        )
        documents[stem] = load_yaml(path.read_text(encoding="utf-8"))
        assert not schemas.validate(documents[stem], f"{stem}.schema.json")
    tags = {item["id"]: item for item in documents["tags"]["tags"]}
    assert len(tags) == len(documents["tags"]["tags"]) == 109
    for key in tags:
        seen = set()
        current = key
        while current is not None:
            assert current in tags
            assert current not in seen
            seen.add(current)
            current = tags[current]["parent"]
    concepts = {item["id"]: item for item in documents["concepts"]["concepts"]}
    assert len(concepts) == len(documents["concepts"]["concepts"]) == 10
    for item in concepts.values():
        assert set(item.get("related_tags", ())) <= tags.keys()
        assert set(item.get("parents", ())) <= concepts.keys()
    entries = documents["foundations-template"]["entries"]
    assert len(entries) == 6
    assert any(item.get("note") == "unital — check the document before keeping" for item in entries)
    assert all("status" not in item and "confirmed_by" not in item for item in entries)
