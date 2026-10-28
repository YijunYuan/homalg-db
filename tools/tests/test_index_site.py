"""Global status, dependency and static-site contract regressions."""

import copy
import json
from pathlib import Path

import pytest

from homalg.index import assemble_index, dependency_edges, latest_formalization_prs
from homalg.relations import canonical_relation, merged_ids, relation_id
from homalg.schemas import SchemaStore
from homalg.sitedata import build_site_data, check_budgets, schema_for_file
from homalg.status import compute_status, status_counts

ROOT = Path(__file__).resolve().parents[2]
GOOD = Path(__file__).parent / "fixtures/good"


def test_latest_pr_lookup_matches_whole_document_branch(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The newest matching formalization PR is selected without confusing similar document keys."""
    records = [
        {
            "number": 3,
            "created_at": "2026-01-02T00:00:00Z",
            "head": {"ref": "formalize/Fixture2000-alice-1"},
        },
        {
            "number": 9,
            "created_at": "2026-02-02T00:00:00Z",
            "head": {"ref": "formalize/Fixture2000-alice-2"},
        },
        {
            "number": 20,
            "created_at": "2026-03-02T00:00:00Z",
            "head": {"ref": "formalize/Fixture2000a-alice-1"},
        },
        {
            "number": 21,
            "created_at": "2026-04-02T00:00:00Z",
            "head": {"ref": "claim/Fixture2000-alice"},
        },
    ]

    def api(_self: object, endpoint: str) -> list[dict]:
        assert endpoint.startswith("repos/example/homalg-db/pulls?state=all")
        return list(reversed(records))

    monkeypatch.setattr("homalg.collaboration.Client.api", api)
    assert latest_formalization_prs(
        repo, ["Fixture2000"], "https://github.com/example/homalg-db"
    ) == {"Fixture2000": 9}
    assert latest_formalization_prs(repo, ["Fixture2000"], "https://localhost.invalid/local") == {}


def node(
    local: str, *, doc: str = "Fixture2000", status: str = "proved", locked: bool = True
) -> dict:
    """Create an independent contract fixture with one simple theorem declaration."""
    value = copy.deepcopy(json.loads((GOOD / "nodes.json").read_text())["nodes"][0])
    value["id"] = f"{doc}.{local}"
    authored, derived = value["authored"], value["derived"]
    name = f"{doc}.{local.lower()}"
    authored.update(id=value["id"], doc=doc, decls=[name], kind="theorem")
    authored["source"]["label"] = local
    authored["proof_md"] = "By reflexivity."
    derived["local_status"] = status
    derived["file"]["path"] = f"HomAlg/{doc}/{local}.lean"
    derived["decl_info"] = [
        {
            "name": name,
            "kind": "theorem",
            "type": "True",
            "type_sha256": "0" * 64,
            "type_hash": "0" * 16,
            "meaning_hash": "1" * 16,
            "is_prop": True,
            "hollow": False,
            "direct_sorry": status == "stated",
            "type_uses_nodes": [],
            "value_uses_nodes": [],
            "type_uses_external": [],
            "value_uses_external": [],
            "type_uses_external_truncated": False,
            "value_uses_external_truncated": False,
        }
    ]
    if locked:
        authored["fidelity"]["reviewed"] = {
            "by": "fixture-reviewer",
            "kind": "agent",
            "session": "fixture-test",
            "status": "satisfactory",
            "on": "2000-01-01",
            "decl_hashes": {
                name: {
                    "statement_sha256": "2" * 64,
                    "type_hash": "0" * 16,
                    "meaning_hash": "1" * 16,
                }
            },
        }
    return value


def build(
    nodes: list[dict], *, transitive: set[str] | None = None, extra_axioms: set[str] | None = None
) -> dict:
    """Assemble document metadata and raw observations independently from node generation."""
    template = json.loads((GOOD / "document.json").read_text())
    docs = []
    for key in sorted({item["authored"]["doc"] for item in nodes}):
        doc = copy.deepcopy(template)
        doc.update(doc_key=key, year=int(key[-4:]))
        docs.append({"document": doc, "claim": {"state": "unclaimed"}})
    modules = []
    for item in nodes:
        declaration = dict(item["derived"]["decl_info"][0])
        declaration["axioms"] = ["sorryAx"] if item["id"] in (transitive or set()) else []
        if item["id"] in (extra_axioms or set()):
            declaration["axioms"].append("Fixture2000.generated_native_axiom")
        declaration["transitive_sorry"] = "sorryAx" in declaration["axioms"]
        modules.append(
            {"module": "HomAlg." + item["id"], "node_id": item["id"], "decls": [declaration]}
        )
    return assemble_index(
        docs,
        nodes,
        [{"modules": modules}],
        {
            "tags": [{"id": "chain-complex", "label": "Chain complex", "parent": None}],
            "concepts": [{"id": "chain-complex", "name": "Chain complex"}],
        },
        [],
        [],
        commit="fixture",
        repo_url="https://github.com/example/homalg-db",
        lean={"toolchain": "leanprover/lean4:v4.35.0", "mathlib_rev": "v4.35.0"},
    )


def depend(
    user: dict, dependency: dict, *, verified: str = "proof", declared: str = "proof"
) -> None:
    """Add a contract edge with independent declared and verified classifications."""
    user["derived"]["verified_deps"][verified].append(dependency["id"])
    user["derived"]["declared_deps"][declared].append(dependency["id"])
    user["authored"]["deps"][declared].append(dependency["id"])
    user["derived"]["imports"]["nodes"].append(dependency["id"])


def test_internal_sorry_and_cited_sorry_are_distinguished() -> None:
    """Distinguish unresolved internal lemmas from unresolved citations."""
    lemma = node("Lem_1", status="stated")
    theorem = node("Thm_1")
    depend(theorem, lemma)
    indexed = build([lemma, theorem], transitive={lemma["id"], theorem["id"]})
    result = next(item for item in indexed["nodes"] if item["id"] == theorem["id"])
    assert result["global"]["status"] == "proved-pending-deps"
    assert result["global"]["headline"] == "statement-complete"
    assert result["global"]["closure"]["blocked_by"] == [lemma["id"]]
    cited = node("Cited_known", status="stated")
    theorem = node("Thm_1")
    depend(theorem, cited)
    indexed = build([cited, theorem], transitive={cited["id"], theorem["id"]})
    result = next(item for item in indexed["nodes"] if item["id"] == theorem["id"])
    assert result["global"]["status"] == "proved-modulo-citations"
    assert result["global"]["headline"] == "proof-complete"


def test_dispute_confirmation_and_review_reopening_are_orthogonal() -> None:
    """Raising a dispute alone does not erase a valid headline; human confirmation does."""
    value = node("Thm_1")
    value["authored"]["dispute"] = {"status": "open", "kind": "proof", "reason": "A gap"}
    axioms = {value["authored"]["decls"][0]: {"axioms": [], "transitive_sorry": False}}
    assert compute_status(value["authored"], value["derived"], axioms, []) == (
        "disputed",
        "proof-complete",
    )
    assert compute_status(value["authored"], value["derived"], axioms, [], reopened=True) == (
        "disputed",
        "in-progress",
    )
    value["authored"]["dispute"]["confirmed_by"] = "fixture-reviewer"
    assert compute_status(value["authored"], value["derived"], axioms, [])[1] == "error"


def test_nonstandard_axioms_remain_visible() -> None:
    """Completed native evaluation is distinguished from the standard trust base."""
    value = node("Thm_1")
    indexed = build([value], extra_axioms={value["id"]})
    assert indexed["nodes"][0]["global"]["status"] == "proved-with-axioms"
    assert indexed["nodes"][0]["global"]["headline"] == "proof-complete"


def test_edge_kind_prefers_verified_over_declared() -> None:
    """A declared statement dependency used only in a proof is a verified proof edge."""
    first, second = node("Thm_1"), node("Lem_1")
    depend(first, second, verified="proof", declared="statement")
    assert dependency_edges([first, second]) == [
        {
            "from": first["id"],
            "to": second["id"],
            "kind": "proof",
            "verified": True,
            "declared": True,
        }
    ]


def test_node_and_document_cycles_are_rejected_separately() -> None:
    """Acyclic node edges can still form a forbidden projected document cycle."""
    a, b = node("Thm_1"), node("Thm_2")
    depend(a, b)
    depend(b, a)
    with pytest.raises(ValueError, match="deps-acyclic"):
        build([a, b])
    a, b, c, d = (
        node("Thm_1"),
        node("Thm_2"),
        node("Thm_1", doc="Fixture2001"),
        node("Thm_2", doc="Fixture2001"),
    )
    depend(a, c)
    depend(d, b)
    with pytest.raises(ValueError, match="doc-acyclic"):
        build([a, b, c, d])


def test_contract_generation_and_content_hashes() -> None:
    """Every site artifact validates; source-only edits do not perturb graph/search hashes."""
    first, second = node("Thm_1"), node("Lem_1", doc="Fixture2001")
    depend(second, first)
    index = build([first, second])
    schemas = SchemaStore(ROOT / "schema")
    assert not schemas.validate(index, "index.schema.json")
    files = build_site_data(
        index, {first["id"]: "theorem a := True.intro", second["id"]: "theorem b := True.intro"}
    )
    for path, value in files.items():
        assert not schemas.validate(value, schema_for_file(path)), path
    second_doc = files["manifest.json"]["documents"][1]
    bundle = files[second_doc["files"]["document"]]
    assert bundle["external_nodes"][0]["id"] == first["id"]
    changed = build_site_data(index, {first["id"]: "new source", second["id"]: "new source"})
    assert changed["manifest.json"]["documents"] == files["manifest.json"]["documents"]
    assert changed["manifest.json"]["search_hash"] == files["manifest.json"]["search_hash"]
    first["authored"]["statement_md"] = "A different mathematical statement."
    changed = build_site_data(build([first, second]), {first["id"]: "", second["id"]: ""})
    assert changed["manifest.json"]["search_hash"] != files["manifest.json"]["search_hash"]


def test_auxiliary_citation_and_informal_counts_are_separate() -> None:
    """Auxiliary and cited nodes never inflate source-item progress counters."""
    item, auxiliary, cited = node("Thm_1"), node("Aux_Thm_1_step"), node("Cited_known")
    auxiliary["authored"]["aux"] = {
        "parent": item["id"],
        "kind": "lemma",
        "reason": "Test",
        "pruned": True,
    }
    index = build([item, auxiliary, cited])
    counts = status_counts(index["nodes"])
    assert counts["items_total"] == 1 and counts["aux_total"] == 1
    assert counts["headline_counts"]["proof-complete"] == 1
    assert counts["aux_headline_counts"]["proof-complete"] == 0
    assert counts["cited_headline_counts"]["proof-complete"] == 1


def test_relation_identity_uses_normal_form() -> None:
    """Equivalent inverse/symmetric relations must have one review identity."""
    a, b = "Fixture2000.Def_1", "Fixture2001.Def_1"
    assert canonical_relation(a, "specializes", b) == (b, "generalizes", a)
    assert relation_id(a, "specializes", b) == relation_id(b, "generalizes", a)
    assert relation_id(a, "same_as", b) == relation_id(b, "same_as", a)
    assert relation_id(a, "same_as", b, header=True).startswith("rel-h-")


def test_alias_chains_reject_cycles_and_unknown_targets() -> None:
    """Vocabulary normalization cannot silently drop or loop on a malformed merge."""
    assert merged_ids([{"id": "a", "merged_into": "b"}, {"id": "b"}]) == {"a": "b", "b": "b"}
    with pytest.raises(ValueError, match="cycle"):
        merged_ids([{"id": "a", "merged_into": "b"}, {"id": "b", "merged_into": "a"}])
    with pytest.raises(ValueError, match="Unknown"):
        merged_ids([{"id": "a", "merged_into": "b"}])


def test_budget_checks_measure_actual_distribution_bytes(tmp_path: Path) -> None:
    """The total distribution limit includes files outside data shards, such as doc-gen4."""
    repo = tmp_path / "repo"
    (repo / "schema").mkdir(parents=True)
    (repo / "schema/budgets.json").write_text(json.dumps({"site_bytes": 10}))
    output = tmp_path / "dist"
    output.mkdir()
    (output / "docs.html").write_bytes(b"x" * 11)
    assert check_budgets(repo, output, distribution=True)[0]["bytes"] == 11
