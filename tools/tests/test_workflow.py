"""Author handoffs preserve real gate boundaries; all review identities here are fictional."""

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner
from test_engine_integration import fake_engine

from homalg import leanexport, planning, workflow
from homalg.cli import cli
from homalg.documents import dump_metadata
from homalg.leantext import statement_hashes
from homalg.nodeio import header_mapping, replace_header
from homalg.schemas import SchemaStore

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = Path(__file__).parent / "golden/fixture-export.json"


def register(repo: Path, stage: str = "STMT", status: str = "queued", number: int = 1) -> dict:
    record = planning.proposed_task(
        repo, "Fixture2000", stage, number, chapter="1", kind_group="theorems"
    )
    record["write_set"]["files"] = ["HomAlg/Fixture2000/Thm_1.lean"]
    record["status"] = status
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_metadata(record))
    return record


@pytest.fixture
def author(repo: Path, monkeypatch: pytest.MonkeyPatch):
    record = register(repo)
    calls = []

    def run(_repo, command):
        calls.append(command)
        return "" if command[1] == "build" else GOLDEN.read_text()

    # Replace only the external compiler boundary, retaining exporter and all validation rules.
    monkeypatch.setattr(leanexport, "run_tool", run)
    return repo, record, calls


def deliver(repo: Path, record: dict) -> dict:
    return workflow.prepare(
        repo,
        record["id"],
        author_session="fictional-author",
        out=Path("build/handoff.json"),
        node_ids=("Fixture2000.Thm_1",),
    )


def test_prepare_real_validation_fresh_export_and_no_task_mutation(author) -> None:
    repo, record, calls = author
    before = {path: path.read_bytes() for path in repo.rglob("*") if path.is_file()}
    data = deliver(repo, record)
    assert data["ready_for_review"], data["validation"]
    assert [command[1] for command in calls] == ["build", "exe"]
    assert not data["approval"] and not data["task_complete"]
    assert data["compiled"]["declarations"]["Fixture2000.Thm_1"]
    assert "claim-author" in data["validation"]["skipped"]
    assert data["validation"]["deferred"] == ["nodes-json-fresh", "nodes-json-stale"]
    assert all(path.read_bytes() == text for path, text in before.items())
    assert workflow.verify(repo, Path("build/handoff.json")) == data
    assert len(calls) == 2  # Freshness verification makes no new compile claim.


def two_authors(repo: Path, record: dict) -> list[dict]:
    record["write_set"]["files"].append("HomAlg/Fixture2000/Lem_1.lean")
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    path.write_text(dump_metadata(record))
    return [
        {"author_session": "fictional-author-a", "node_ids": ["Fixture2000.Thm_1"]},
        {"author_session": "fictional-author-b", "node_ids": ["Fixture2000.Lem_1"]},
    ]


def test_batch_preserves_separate_authors_and_full_validation_with_one_fresh_build(author):
    repo, record, calls = author
    authors = two_authors(repo, record)
    data = workflow.prepare_batch(repo, record["id"], authors=authors, out=Path("build/batch.json"))
    assert [command[1] for command in calls] == ["build", "exe"]
    assert data["ready_for_review"] and not data["approval"] and not data["task_complete"]
    for group, delivery in zip(authors, data["deliveries"], strict=True):
        assert delivery["author_session"] == group["author_session"]
        assert delivery["node_ids"] == group["node_ids"]
        assert set(delivery["compiled"]["declarations"]) == set(group["node_ids"])
        assert (
            workflow.verify(repo, Path("build/batch.json"), author_session=group["author_session"])
            == delivery
        )
        single = workflow.prepare(
            repo,
            record["id"],
            author_session=group["author_session"],
            node_ids=tuple(group["node_ids"]),
            out=Path(f"build/{group['author_session']}.json"),
        )
        assert {k: v for k, v in single.items() if k != "created_at"} == {
            k: v for k, v in delivery.items() if k != "created_at"
        }
    with pytest.raises(ValueError, match="Select the actual author"):
        workflow.verify(repo, Path("build/batch.json"))
    with pytest.raises(ValueError, match="exactly one"):
        workflow.verify(repo, Path("build/batch.json"), author_session="fictional-impostor")
    with pytest.raises(ValueError, match="exceeds"):
        workflow.review_snapshot(
            repo,
            Path("build/batch.json"),
            author_session="fictional-author-a",
            node_ids=("Fixture2000.Lem_1",),
            out=Path("build/bad-snapshot.json"),
        )


@pytest.mark.parametrize("bad", ["overlap", "scope", "same-author", "empty", "unknown-field"])
def test_batch_rejects_invalid_ownership_before_compilation(author, bad):
    repo, record, calls = author
    authors = two_authors(repo, record)
    if bad == "overlap":
        authors[1]["node_ids"] = authors[0]["node_ids"]
    elif bad == "scope":
        authors[1]["node_ids"] = ["Fixture2000.Def_1"]
    elif bad == "same-author":
        authors[1]["author_session"] = authors[0]["author_session"]
    elif bad == "empty":
        authors[1]["node_ids"] = []
    else:
        authors[1]["approval"] = True
    with pytest.raises(ValueError):
        workflow.prepare_batch(repo, record["id"], authors=authors, out=Path("build/bad.json"))
    assert not calls and not (repo / "build/bad.json").exists()


def test_batch_keeps_global_validation_errors_in_every_delivery(author):
    repo, record, _ = author
    authors = two_authors(repo, record)
    path = repo / "HomAlg/Fixture2000/Def_1.lean"
    source = path.read_text()
    metadata = header_mapping(source)
    metadata["id"] = "Fixture2000.Wrong"
    path.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))
    assert path.read_text() != source
    data = workflow.prepare_batch(
        repo, record["id"], authors=authors, out=Path("build/invalid.json")
    )
    assert not data["ready_for_review"]
    for delivery in data["deliveries"]:
        assert delivery["validation"] == data["validation"]
        assert not delivery["ready_for_review"]
        with pytest.raises(ValueError, match="successful author handoff"):
            workflow.verify(
                repo, Path("build/invalid.json"), author_session=delivery["author_session"]
            )


def test_batch_concurrent_change_to_one_author_publishes_no_partial_delivery(author, monkeypatch):
    repo, record, _ = author
    authors = two_authors(repo, record)
    path = repo / "HomAlg/Fixture2000/Lem_1.lean"

    def edit(_repo, command):
        path.write_text(path.read_text() + "\n-- Concurrent edit\n")
        return "" if command[1] == "build" else GOLDEN.read_text()

    monkeypatch.setattr(leanexport, "run_tool", edit)
    with pytest.raises(ValueError, match="changed"):
        workflow.prepare_batch(repo, record["id"], authors=authors, out=Path("build/batch.json"))
    assert not (repo / "build/batch.json").exists()


def test_batch_cli_preserves_author_selection(author):
    repo, record, calls = author
    authors = two_authors(repo, record)
    manifest = repo / "authors.json"
    manifest.write_text(json.dumps(authors))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "workflow",
            "prepare-batch",
            record["id"],
            "--repo",
            str(repo),
            "--json",
            "--authors",
            str(manifest),
            "--out",
            "build/batch.json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert len(calls) == 2
    result = runner.invoke(
        cli,
        [
            "workflow",
            "verify",
            str(repo / "build/batch.json"),
            "--repo",
            str(repo),
            "--json",
            "--author-session",
            "fictional-author-b",
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"]["node_ids"] == ["Fixture2000.Lem_1"]


def test_default_delivery_includes_direct_auxiliaries_but_not_unrelated_nodes(author):
    repo, record, _ = author
    path = repo / "HomAlg/Fixture2000/Aux_Thm_1_step.lean"
    source = path.read_text()
    metadata = header_mapping(source)
    metadata["aux"]["pruned"] = False
    path.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))
    data = workflow.prepare(
        repo, record["id"], author_session="fictional-author", out=Path("build/all.json")
    )
    assert data["node_ids"] == ["Fixture2000.Aux_Thm_1_step", "Fixture2000.Thm_1"]
    assert "Fixture2000.Bridge_Def_1_mathlib" not in data["node_ids"]
    workflow.verify(repo, Path("build/all.json"))
    with pytest.raises(ValueError, match="scope"):
        workflow.prepare(
            repo,
            record["id"],
            author_session="fictional-author",
            out=Path("build/bad.json"),
            node_ids=("Fixture2000.Thm_1", "Fixture2000.Def_1"),
        )


def test_review_subset_cannot_exceed_author_delivery(author):
    repo, record, _ = author
    deliver(repo, record)
    with pytest.raises(ValueError, match="exceeds"):
        workflow.review_snapshot(
            repo,
            Path("build/handoff.json"),
            out=Path("build/bad.json"),
            node_ids=("Fixture2000.Lem_1",),
        )


def test_task_scope_growth_keeps_a_portable_delivery_valid(author) -> None:
    """A delivery is judged by the scope it was made under and its exact inputs.

    Settlement narrows author tasks after delivery, so later scope edits must not
    invalidate it; changes to the delivered nodes or their dependencies still do.
    """
    repo, record, _ = author
    data = deliver(repo, record)
    record["write_set"]["files"].append("HomAlg/Fixture2000/Lem_1.lean")
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    path.write_text(dump_metadata(record))
    assert workflow.verify(repo, Path("build/handoff.json")) == data


@pytest.mark.parametrize("changed", ["node", "dependency", "toolchain", "policy"])
def test_changes_invalidate_delivery(author, changed: str) -> None:
    repo, record, _ = author
    deliver(repo, record)
    if changed == "scope":
        record["write_set"]["files"].append("HomAlg/Fixture2000/Lem_1.lean")
        path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
        path.write_text(dump_metadata(record))
    elif changed == "policy":
        path = repo / "horizon/review-policy.yaml"
        path.parent.mkdir(exist_ok=True)
        path.write_text("schema_version: 1\nallow_independent_agent_reviews: true\n")
    else:
        path = (
            repo
            / {
                "node": "HomAlg/Fixture2000/Thm_1.lean",
                "dependency": "HomAlg/Fixture2000/Def_1.lean",
                "toolchain": "lean-toolchain",
            }[changed]
        )
        path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="changed|stale"):
        workflow.verify(repo, Path("build/handoff.json"))


def test_late_reports_do_not_stale_author_handoff_but_bind_final_snapshot(author) -> None:
    repo, record, _ = author
    deliver(repo, record)
    report = repo / "literature/Fixture2000/reviews/Thm_1.md"
    report.parent.mkdir(exist_ok=True)
    report.write_text("Fictional unfinished review; no approval.\n")
    workflow.verify(repo, Path("build/handoff.json"))
    snapshot = workflow.review_snapshot(
        repo, Path("build/handoff.json"), out=Path("build/review-snapshot.json")
    )
    assert snapshot == json.loads((repo / "build/review-snapshot.json").read_text())
    assert str(report) in json.dumps(snapshot)
    report.write_text("Fictional modified review; still no approval.\n")
    from homalg.review import freeze_fidelity_inputs

    assert (
        freeze_fidelity_inputs(
            repo, ["Fixture2000.Thm_1"], expected_author_session="fictional-author"
        )
        != snapshot
    )
    workflow.verify(repo, Path("build/handoff.json"))


def test_pending_or_incomplete_nodes_cannot_be_frozen(author) -> None:
    repo, record, calls = author
    path = repo / "HomAlg/Fixture2000/Thm_1.lean"
    source = path.read_text()
    metadata = header_mapping(source)
    metadata["decls"] = []
    path.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))
    with pytest.raises(ValueError, match="actual main declarations"):
        deliver(repo, record)
    assert not calls
    register(repo, stage="INV")
    with pytest.raises(ValueError, match="STMT, CITED or PROOF"):
        workflow.prepare(
            repo, "Fixture2000.INV.1", author_session="fictional", out=Path("build/invalid.json")
        )


def test_failed_structural_validation_is_retained_but_not_reviewable(author) -> None:
    repo, record, _ = author
    path = repo / "HomAlg/Fixture2000/Thm_1.lean"
    path.write_text(path.read_text().replace("## Statement", "## Missing statement"))
    data = deliver(repo, record)
    assert not data["ready_for_review"]
    assert any(item["severity"] == "error" for item in data["validation"]["findings"])
    with pytest.raises(ValueError, match="successful author handoff"):
        workflow.verify(repo, Path("build/handoff.json"))


@pytest.mark.parametrize("kind,ready", [("agent", True), ("human", False)])
def test_only_agent_lock_renewal_can_be_pending_in_author_preflight(author, kind, ready):
    repo, record, _ = author
    policy = repo / "horizon/review-policy.yaml"
    policy.parent.mkdir(exist_ok=True)
    policy.write_text("schema_version: 1\nallow_independent_agent_reviews: true\n")
    path = repo / "HomAlg/Fixture2000/Thm_1.lean"
    source = path.read_text()
    metadata = header_mapping(source)
    hashes = statement_hashes(source)
    lock = {
        "kind": kind,
        "by": "fictional-reviewer",
        "on": "2026-01-01",
        "status": "satisfactory",
        "decl_hashes": {
            name: {
                "statement_sha256": hashes[name],
                "type_hash": "0" * 16,
                "meaning_hash": "0" * 16,
            }
            for name in metadata["decls"]
        },
    }
    if kind == "agent":
        lock.update(session="fictional-reviewer", author_session="fictional-author")
    metadata["fidelity"]["reviewed"] = lock
    path.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))
    data = deliver(repo, record)
    assert data["ready_for_review"] is ready, data["validation"]
    assert bool(data["pending_review_renewal"]) is ready
    assert header_mapping(path.read_text())["fidelity"]["reviewed"] == lock


def test_concurrent_edit_during_build_leaves_no_handoff(author, monkeypatch) -> None:
    repo, record, _ = author
    path = repo / "HomAlg/Fixture2000/Thm_1.lean"

    def edit(_repo, command):
        path.write_text(path.read_text() + "\n-- Concurrent edit\n")
        return "" if command[1] == "build" else GOLDEN.read_text()

    monkeypatch.setattr(leanexport, "run_tool", edit)
    with pytest.raises(ValueError, match="changed"):
        deliver(repo, record)
    assert not (repo / "build/handoff.json").exists()


def test_evidence_cannot_overwrite_source_or_previous_delivery(author) -> None:
    repo, record, _ = author
    with pytest.raises(ValueError, match="build/"):
        workflow.prepare(repo, record["id"], author_session="fictional", out=Path("HomAlg.lean"))
    deliver(repo, record)
    with pytest.raises(ValueError, match="already exists"):
        deliver(repo, record)


def test_evidence_rejects_symlinked_build_root(author, tmp_path) -> None:
    repo, record, _ = author
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (repo / "build").symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        deliver(repo, record)
    assert not list(elsewhere.iterdir())


def test_atomic_evidence_publication_has_exactly_one_concurrent_winner(tmp_path) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from homalg.io import atomic_create

    barrier = Barrier(2)
    path = tmp_path / "evidence.json"

    def publish(value):
        barrier.wait(timeout=5)
        try:
            atomic_create(path, value)
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(publish, ["first\n" * 100, "second\n" * 100]))
    assert sorted(outcomes) == [False, True]
    assert path.read_text() in {"first\n" * 100, "second\n" * 100}
    assert path.stat().st_mode & 0o777 == 0o600
    assert list(tmp_path.iterdir()) == [path]


def test_next_is_read_only_and_retains_blocked_status(repo: Path) -> None:
    record = register(repo, stage="INV", status="blocked")
    before = {path: path.read_bytes() for path in repo.rglob("*") if path.is_file()}
    data = workflow.next_tasks(repo, "Fixture2000", proofs="deferred")
    assert not data["ready"]
    assert data["held"] == [
        {"task": record["id"], "reason": "Preserve existing task status", "status": "blocked"}
    ]
    assert before == {path: path.read_bytes() for path in repo.rglob("*") if path.is_file()}


def test_deferred_mode_does_not_hide_an_already_running_proof(repo: Path) -> None:
    record = register(repo, stage="PROOF", status="running")
    data = workflow.next_tasks(repo, "Fixture2000", proofs="deferred")
    assert data["running"] == [{"task": record["id"], "status": "running"}]
    assert record["id"] not in {item["task"] for item in data["held"]}


def test_next_gates_and_priority_never_requeue_or_include_deferred_proof(repo, monkeypatch):
    definitions = register(repo, number=2)
    definitions["metadata"]["homalg"]["kind_group"] = "definitions"
    path = repo / ".archon-horizon/tasks/items/Fixture2000.STMT.2.yaml"
    path.write_text(dump_metadata(definitions))
    theorem = register(repo)
    proof = register(repo, stage="PROOF")
    blocked = register(repo, number=3, status="blocked")
    ineligible = register(repo, number=4)

    def eligible(*args, **kwargs):
        assert kwargs["persist_transcription"] is False
        return [theorem, proof, definitions, blocked], False

    monkeypatch.setattr(planning, "unlocked_tasks", eligible)
    data = workflow.next_tasks(repo, "Fixture2000", proofs="deferred")
    assert [item["task"] for item in data["ready"]] == [definitions["id"], theorem["id"]]
    assert {item["task"] for item in data["held"]} == {proof["id"], blocked["id"], ineligible["id"]}


def test_deferred_proof_planning_persists_across_advance_without_fake_completion(repo, monkeypatch):
    shutil.copytree(ROOT / "horizon", repo / "horizon")
    monkeypatch.setattr(planning, "horizon", fake_engine)
    candidate = planning.proposed_task(repo, "Fixture2000", "PROOF", 1, chapter="1")
    monkeypatch.setattr(planning, "unlocked_tasks", lambda *args, **kwargs: ([candidate], False))
    first = planning.plan(repo, "Fixture2000", no_claim=True, proofs="deferred")
    assert first["proofs"] == "deferred" and not first["created_tasks"]
    advanced = planning.plan(repo, "Fixture2000", advance=True)
    assert advanced["proofs"] == "deferred" and not advanced["created_tasks"]
    included = planning.plan(repo, "Fixture2000", advance=True, proofs="included")
    assert included["created_tasks"] == ["Fixture2000.PROOF.1"]
    path = repo / ".archon-horizon/tasks/items/Fixture2000.PROOF.1.yaml"
    before = path.read_bytes()
    planning.plan(repo, "Fixture2000", advance=True, proofs="deferred")
    assert path.read_bytes() == before


def test_cli_workflow_and_worker_commands_are_registered(author) -> None:
    repo, record, _ = author
    result = CliRunner().invoke(
        cli,
        [
            "workflow",
            "prepare",
            record["id"],
            "--repo",
            str(repo),
            "--json",
            "--author-session",
            "fictional-author",
            "--out",
            "build/cli-handoff.json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"]["ready_for_review"]
    for command in ("workflow", "workspaces"):
        result = CliRunner().invoke(cli, [command, "--help"])
        assert result.exit_code == 0
