"""Call-local reuse retains scope semantics; every identity and publication here is fictional."""

import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from test_claims import claim, status
from test_engine_integration import fake_engine

from homalg import claims, planning, workflow
from homalg.blueprint import source_order
from homalg.checks.context import Context
from homalg.checks.text_rules import out_of_scope
from homalg.documents import read_document
from homalg.headers import parse_header
from homalg.nodeio import header_mapping, replace_header
from homalg.repository import node_paths
from homalg.schemas import SchemaStore

ROOT = Path(__file__).resolve().parents[2]


def git(repo, *args, text=None):
    return subprocess.run(
        ["git", *args], cwd=repo, input=text, text=True, capture_output=True, check=True
    ).stdout.strip()


def initialize(repo):
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Fictional test author")
    git(repo, "config", "user.email", "fixture@example.invalid")


def publish(repo, key, value):
    """Create a real local status history without touching an index or working source."""
    ref = f"refs/remotes/origin/status/{key}"
    blob = git(repo, "hash-object", "-w", "--stdin", text=value)
    tree = git(repo, "mktree", text=f"100644 blob {blob}\tstatus.json\n")
    parent = claims.status_history_commit(repo, key)
    commit = git(repo, "commit-tree", tree, *(["-p", parent] if parent else []), text="Fixture\n")
    git(repo, "update-ref", ref, commit)
    return commit


def context(repo, key="Example2000", count=4):
    ctx = Context(repo, SchemaStore(repo / "schema"), now="2026-01-20T00:00:00Z")
    ctx.claims[key] = claim()
    ctx.claims[key]["claims"][0]["scope"]["chapters"] = ["99"]
    template = parse_header((repo / "HomAlg/Fixture2000/Thm_1.lean").read_text())
    for number in range(count):
        h = copy.deepcopy(template)
        h.metadata["doc"] = key
        ctx.valid_headers[f"HomAlg/{key}/Thm_{number}.lean"] = h
    return ctx


def test_history_is_once_per_context_doc_and_claim_decisions_stay_live(repo, monkeypatch):
    initialize(repo)
    commit = publish(repo, "Example2000", json.dumps(status("2026-01-10T00:00:00Z")))
    ctx = context(repo)
    calls = []
    original = subprocess.run

    def counted(argv, **kwargs):
        calls.append(argv)
        return original(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", counted)
    assert len(out_of_scope(ctx)) == 4
    assert len(calls) == 4  # presence, resolve, immutable log, one publication
    assert calls[2][3] == commit
    assert ctx.status_histories["Example2000"][0] == commit
    ctx.claims["Example2000"]["claims"][0]["scope"]["chapters"] = ["1"]
    assert not out_of_scope(ctx)
    ctx.claims["Example2000"]["claims"][0]["scope"]["chapters"] = ["99"]
    ctx.taxonomy["policy"] = {"claim_activity_grace_days": 1}
    assert not out_of_scope(ctx)  # expiry is recomputed, not cached
    ctx.taxonomy["policy"]["claim_activity_grace_days"] = 14
    ctx.now = "2026-02-01T00:00:00Z"
    assert not out_of_scope(ctx)
    ctx.now = "2026-01-20T00:00:00Z"
    ctx.base_sources[next(iter(ctx.valid_headers))] = ""
    assert len(out_of_scope(ctx)) == 3  # tracked-node semantics remain unchanged
    assert len(calls) == 4


def test_history_pins_ref_and_new_context_observes_ref_and_schema_changes(repo):
    initialize(repo)
    first = publish(repo, "Example2000", json.dumps(status("2026-01-10T00:00:00Z")))
    old = context(repo)
    assert len(old.status_history("Example2000")) == 1
    second = publish(repo, "Example2000", json.dumps(status("2026-01-19T00:00:00Z")))
    assert old.status_histories["Example2000"][0] == first
    assert len(old.status_history("Example2000")) == 1
    fresh = context(repo)
    assert len(fresh.status_history("Example2000")) == 2
    assert fresh.status_histories["Example2000"][0] == second
    other_schema = context(repo)
    other_schema.schemas.schemas["run-status.schema.json"]["properties"]["holder"]["const"] = "bob"
    assert other_schema.status_history("Example2000") == []
    assert len(fresh.status_history("Example2000")) == 2


def test_ref_advance_during_read_cannot_mix_histories(repo, monkeypatch):
    initialize(repo)
    first = publish(repo, "Example2000", json.dumps(status("2026-01-10T00:00:00Z")))
    second = publish(repo, "Example2000", json.dumps(status("2026-01-19T00:00:00Z")))
    ref = "refs/remotes/origin/status/Example2000"
    git(repo, "update-ref", ref, first)
    original = subprocess.run

    def advance(argv, **kwargs):
        if argv[1:3] == ["log", "--format=%H"]:
            assert argv[3] == first
            original(["git", "update-ref", ref, second], cwd=repo, check=True)
        return original(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", advance)
    assert [x["generated_at"] for x in claims.load_status_history(repo, "Example2000")] == [
        "2026-01-10T00:00:00Z"
    ]


def test_missing_history_independent_docs_and_repository_contexts(repo, tmp_path):
    initialize(repo)
    ctx = context(repo)
    assert ctx.status_history("Example2000") == []
    publish(repo, "Example2000", json.dumps(status("2026-01-10T00:00:00Z")))
    other = status("2026-01-09T00:00:00Z") | {"doc_key": "Other2000"}
    publish(repo, "Other2000", json.dumps(other))
    assert ctx.status_history("Example2000") == []  # absence was pinned in this context
    assert ctx.status_history("Other2000") == [other]
    assert len(context(repo).status_history("Example2000")) == 1
    second_repo = tmp_path / "independent"
    second_repo.mkdir()
    initialize(second_repo)
    independent = Context(second_repo, SchemaStore(repo / "schema"))
    assert independent.status_history("Example2000") == []


@pytest.mark.parametrize("payload", ["not JSON", "[]", '{"doc_key":"Example2000"}'])
def test_invalid_publications_are_still_ignored(repo, payload):
    initialize(repo)
    publish(repo, "Example2000", payload)
    assert claims.load_status_history(repo, "Example2000") == []
    assert not out_of_scope(context(repo))  # no invalid activity extension


def test_history_errors_and_malformed_claims_are_not_hidden(repo, monkeypatch):
    initialize(repo)
    with pytest.raises(ValueError, match="document key"):
        claims.load_status_history(repo, "../escape")
    with pytest.raises(ValueError, match="immutable"):
        claims.load_status_history(repo, "Example2000", commit="HEAD")
    with pytest.raises(subprocess.CalledProcessError):
        claims.load_status_history(repo, "Example2000", commit="0" * 40)
    ctx = context(repo)
    ctx.now = "2026-01-05T00:00:00Z"
    monkeypatch.setattr(
        claims, "status_history_commit", lambda *args: (_ for _ in ()).throw(ValueError("bad ref"))
    )
    assert len(out_of_scope(ctx)) == 4  # existing ValueError fallback, not skipped scope checks
    ctx.claims["Example2000"]["claims"][0]["expires_at"] = "not a timestamp"
    with pytest.raises(ValueError):
        out_of_scope(ctx)


def reference_scope(repo, key, chapter, group):
    """The original uncached selection, retained as an independent behavioral oracle."""
    nodes = [parse_header(p.read_text()).metadata for p in node_paths(repo, [key])]
    primary = [
        n
        for n in nodes
        if "aux" not in n
        and (chapter is None or n["source"].get("chapter") == chapter)
        and (group == "cited") == ("cited" in n)
    ]
    if group in {"definitions", "theorems"}:
        primary = [
            n
            for n in primary
            if (n["kind"] in planning.DEFINITION_KINDS) == (group == "definitions")
        ]
    selected = {n["id"] for n in primary}
    return source_order(
        repo,
        key,
        [n for n in nodes if n["id"] in selected or n.get("aux", {}).get("parent") in selected],
    )


@pytest.mark.parametrize(
    "stage,group",
    [
        ("T", None),
        ("INV", None),
        ("DAG", None),
        ("STMT", "definitions"),
        ("STMT", "theorems"),
        ("CITED", "cited"),
        ("PROOF", None),
    ],
)
def test_every_stage_preserves_scope_node_ids_and_created_objective(
    repo, monkeypatch, stage, group
):
    shutil.copytree(ROOT / "horizon", repo / "horizon")
    index = planning.AuthoredNodeIndex(repo, "Fixture2000")
    expected_nodes = reference_scope(repo, "Fixture2000", "1", group)
    assert index.select("1", group) == expected_nodes
    plain = planning.proposed_task(
        repo, "Fixture2000", stage, 1, chapter="1", pages=[1, 2], kind_group=group
    )
    indexed = planning.proposed_task(
        repo, "Fixture2000", stage, 1, chapter="1", pages=[1, 2], kind_group=group, node_index=index
    )
    assert indexed == plain
    assert indexed["node_ids"] == [n["id"] for n in expected_nodes]
    assert indexed["node_ids"]  # especially T/INV: templates consume node_list
    monkeypatch.setattr(planning, "horizon", fake_engine)
    document = read_document(repo, "Fixture2000")
    planning.create_task(repo, plain, login="fictional", document=document)
    path = repo / f".archon-horizon/tasks/items/{plain['id']}.yaml"
    before = path.read_bytes()
    path.unlink()
    planning.create_task(repo, indexed, login="fictional", document=document)
    assert path.read_bytes() == before


def test_one_index_per_planning_call_and_fresh_sources_on_next_call(repo, monkeypatch):
    document = read_document(repo, "Fixture2000")
    count = 0
    original = planning.parse_header

    def parse(text):
        nonlocal count
        count += 1
        return original(text)

    monkeypatch.setattr(planning, "parse_header", parse)
    paths = node_paths(repo, ["Fixture2000"])
    first, _ = planning.unlocked_tasks(
        repo, "Fixture2000", document["structure"], persist_transcription=False
    )
    assert count == len(paths)
    source = (repo / "HomAlg/Fixture2000/Def_1.lean").read_text()
    (repo / "HomAlg/Fixture2000/Def_99.lean").write_text(source.replace("Def_1", "Def_99"))
    second, _ = planning.unlocked_tasks(
        repo, "Fixture2000", document["structure"], persist_transcription=False
    )
    assert count == len(paths) * 2 + 1
    assert "Fixture2000.Def_99" not in first[0]["node_ids"]
    assert "Fixture2000.Def_99" in second[0]["node_ids"]


def test_index_order_fresh_inventory_and_document_isolation(repo):
    path = repo / "literature/Fixture2000/inventory.yaml"
    selected = ["Fixture2000.Def_2", "Fixture2000.Def_1"]
    # Put two definitions at the same coordinate so occurrence order determines the tie.
    for name in selected:
        p = repo / f"HomAlg/Fixture2000/{name.split('.')[1]}.lean"
        source = p.read_text()
        metadata = header_mapping(source)
        metadata["source"]["pages"] = [1]
        p.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))

    def inventory(names):
        path.write_text(json.dumps({"pages": {"0001": {"items": [{"node": n} for n in names]}}}))

    inventory(selected)
    old = planning.AuthoredNodeIndex(repo, "Fixture2000")
    assert [n["id"] for n in old.select(None, "definitions") if n["id"] in selected] == selected
    inventory(list(reversed(selected)))
    fresh = planning.scope_nodes(repo, "Fixture2000", None, "definitions")
    assert [n["id"] for n in fresh if n["id"] in selected] == list(reversed(selected))
    assert [n["id"] for n in old.select(None, "definitions") if n["id"] in selected] == selected
    with pytest.raises(ValueError, match="another repository/document"):
        planning.proposed_task(repo, "Fixture2001", "INV", 1, node_index=old)


def test_index_rejects_malformed_source_and_inventory_on_new_calls(repo):
    path = repo / "literature/Fixture2000/inventory.yaml"
    path.write_text("pages: [broken")
    with pytest.raises(ValueError):
        planning.AuthoredNodeIndex(repo, "Fixture2000")
    path.unlink()
    (repo / "HomAlg/Fixture2000/Def_1.lean").write_text("/- missing header")
    with pytest.raises(ValueError):
        planning.AuthoredNodeIndex(repo, "Fixture2000")


def test_workflow_next_readonly_with_real_index_and_deferred_proofs(repo):
    from test_workflow import register

    record = register(repo, stage="INV", status="blocked")
    register(repo, stage="PROOF", status="running")
    before = {p: p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    result = workflow.next_tasks(repo, "Fixture2000", proofs="deferred")
    assert {p: p.read_bytes() for p in repo.rglob("*") if p.is_file()} == before
    assert any(x["task"] == record["id"] and x["status"] == "blocked" for x in result["held"])
    assert result["running"] == [{"task": "Fixture2000.PROOF.1", "status": "running"}]
