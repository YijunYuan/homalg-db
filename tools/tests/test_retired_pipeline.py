"""Historical node identities remain useful through the index, site and local API."""

import json
from pathlib import Path

import pytest

from homalg.documents import dump_metadata
from homalg.localdb import Database, build_artifacts_db
from homalg.relations import load_relations, relation_id
from homalg.retired import load_retired, resolve_retired, retirement_map
from homalg.schemas import SchemaStore
from homalg.sitedata import build_site_data

ROOT = Path(__file__).resolve().parents[2]


def tombstone(identifier, target=None, *, kind="moved"):
    value = {
        "id": identifier,
        "kind": kind,
        "by": "fixture-reviewer",
        "on": "2001-01-01",
        "reason": "Synthetic historical identity regression.",
    }
    if target is not None:
        value["moved_to" if kind == "moved" else "merged_into"] = target
    return value


def save_retired(repo, records):
    (repo / "literature/Fixture2000/retired.yaml").write_text(
        dump_metadata({"schema_version": 1, "retired": records})
    )


def test_retirement_chains_cycles_and_invalid_registry(repo):
    records = [
        tombstone("Fixture2000.Aux_Old", "Fixture2000.Aux_Middle"),
        tombstone("Fixture2000.Aux_Middle", "Fixture2000.Def_1", kind="merged"),
    ]
    save_retired(repo, records)
    table = retirement_map(load_retired(repo))
    assert resolve_retired("Fixture2000.Aux_Old", table) == "Fixture2000.Def_1"
    records.append(tombstone("Fixture2000.Def_1", kind="pruned"))
    assert resolve_retired("Fixture2000.Aux_Old", retirement_map(records)) is None
    records[-1] = tombstone("Fixture2000.Def_1", "Fixture2000.Aux_Old")
    with pytest.raises(ValueError, match="cycle"):
        retirement_map(records)
    with pytest.raises(ValueError, match="Duplicate"):
        retirement_map(records[:1] * 2)
    save_retired(repo, [tombstone("Fixture2001.Aux_Old", kind="pruned")])
    with pytest.raises(ValueError, match="does not belong"):
        load_retired(repo)


def test_relation_aliases_keep_review_identity_and_reject_resolved_duplicates(repo):
    old, current, other = "Fixture2000.Aux_Old", "Fixture2000.Def_1", "Fixture2001.Def_1"
    save_retired(repo, [tombstone(old, current)])
    identifier = relation_id(old, "precursor_of", other)
    record = {
        "id": identifier,
        "source": old,
        "type": "precursor_of",
        "target": other,
        "provenance": {"by": "formalizer", "on": "2001-01-01"},
        "review": {"status": "unreviewed"},
    }
    path = repo / "taxonomy/relations/Fixture2000.yaml"
    path.write_text(dump_metadata({"schema_version": 1, "relations": [record]}))
    decision = {"status": "accepted", "by": "fixture-reviewer", "on": "2001-01-02"}
    (repo / "taxonomy/relations/_reviews.yaml").write_text(
        dump_metadata({"schema_version": 1, "reviews": {identifier: decision}})
    )
    resolved = load_relations(repo, [], SchemaStore(repo / "schema"))[0]
    assert resolved["source"] == current
    assert resolved["id"] == identifier and resolved["review"] == decision
    duplicate = record | {"source": current, "id": relation_id(current, "precursor_of", other)}
    path.write_text(dump_metadata({"schema_version": 1, "relations": [record, duplicate]}))
    with pytest.raises(ValueError, match="duplicate"):
        load_relations(repo, [], SchemaStore(repo / "schema"))


def test_site_and_sqlite_resolve_aliases_and_preserve_pruned_reasons(tmp_path):
    index = json.loads((ROOT / "tools/tests/fixtures/good/index.json").read_text())
    index["generator"]["commit"] = "fixture"
    current = index["nodes"][0]["id"]
    old, removed, missing = (
        "Fixture2000.Aux_Old",
        "Fixture2000.Aux_Removed",
        "Fixture2000.Aux_Missing",
    )
    index["retired"] = [
        tombstone(old, current),
        tombstone(removed, kind="pruned"),
        tombstone(missing, "Fixture2000.Aux_Absent"),
    ]
    index["tags"].append(
        {
            "id": "old-basic",
            "label": "Old basic",
            "parent": None,
            "merged_into": index["tags"][0]["id"],
        }
    )
    index["concepts"].append(
        {"id": "old-complex", "name": "Old complex", "merged_into": "chain-complex"}
    )
    artifacts = build_site_data(index, {current: "-- synthetic source"})
    store = SchemaStore(ROOT / "schema")
    assert not store.validate(index, "index.schema.json")
    assert not store.validate(artifacts["manifest.json"], "site/manifest.schema.json")
    assert artifacts["manifest.json"]["retired"] == index["retired"]
    db = tmp_path / "snapshot.sqlite"
    build_artifacts_db(artifacts, db)
    database = Database(db)
    assert database.node(old) == database.node(current)
    assert database.neighbors(old) == database.neighbors(current)
    assert database.search({"tags": "old-basic"}) == database.search(
        {"tags": index["tags"][0]["id"]}
    )
    assert database.search({"concepts": "old-complex"}) == database.search(
        {"concepts": "chain-complex"}
    )
    for identifier in (removed, missing):
        with pytest.raises(KeyError):
            database.node(identifier)
