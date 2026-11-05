"""Independent cohort provenance and rollback checks use only fictional fixtures."""

import json
from pathlib import Path

import pytest
import test_review_cohorts as baseline

from homalg import review, review_cohorts, workflow
from homalg.documents import dump_metadata
from homalg.io import json_text
from homalg.nodeio import node_path

author = baseline.author
cohorts = baseline.cohorts
NOW = baseline.NOW


def journals(repo: Path) -> list[dict]:
    return [
        json.loads(path.read_text())
        for path in (repo / ".archon-horizon/cache/fidelity-transactions").glob("*.json")
    ]


def test_ready_subset_of_whole_author_deliveries_does_not_wait_for_other_author(cohorts):
    repo, _, commands, _, manifest, data = cohorts
    omitted = data["cohorts"].pop()
    omitted_node = node_path(repo, omitted["node_ids"][0])
    before = omitted_node.read_bytes()
    (repo / manifest).write_text(json_text(data))
    baseline.capture(cohorts)
    locks = review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert list(locks) == data["cohorts"][0]["node_ids"]
    assert omitted_node.read_bytes() == before
    assert [command[1] for command in commands] == ["build", "exe"]


@pytest.mark.parametrize("omit_one_reviewer", [False, True])
def test_split_actual_author_requires_complete_combined_delivery(cohorts, omit_one_reviewer):
    repo, record, commands, _, manifest, data = cohorts
    node_ids = [node for entry in data["cohorts"] for node in entry["node_ids"]]
    actual_author = "fictional-joint-delivery-author"
    handoff = Path("build/joint-author.json")
    workflow.prepare_batch(
        repo,
        record["id"],
        authors=[{"author_session": actual_author, "node_ids": node_ids}],
        out=handoff,
    )
    for entry in data["cohorts"]:
        entry["author_session"] = actual_author
    baseline.write_reports(repo, data["cohorts"])
    if omit_one_reviewer:
        data["cohorts"].pop()
    (repo / manifest).write_text(json_text(data))
    commands.clear()
    before = {node_path(repo, node): node_path(repo, node).read_bytes() for node in node_ids}
    if omit_one_reviewer:
        with pytest.raises(ValueError, match="complete delivery"):
            review_cohorts.snapshot(
                repo, handoff, manifest=manifest, out=Path("build/reviews.json")
            )
        assert not commands and not (repo / "build/reviews.json").exists()
        assert all(path.read_bytes() == content for path, content in before.items())
        return
    bundle = review_cohorts.snapshot(
        repo, handoff, manifest=manifest, out=Path("build/reviews.json")
    )
    assert "expected_author_session" not in bundle["inputs"]
    locks = review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert {lock["author_session"] for lock in locks.values()} == {actual_author}
    assert len({lock["session"] for lock in locks.values()}) == 2
    assert [command[1] for command in commands] == ["build", "exe"]


@pytest.mark.parametrize("changed", ["task", "handoff", "snapshot", "private", "report"])
def test_late_evidence_edits_after_first_lock_roll_back_entire_union(cohorts, monkeypatch, changed):
    repo, record, commands, handoff, _, _ = cohorts
    baseline.capture(cohorts)
    before = baseline.sources(cohorts)
    paths = {
        "task": repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml",
        "handoff": repo / handoff,
        "snapshot": repo / "build/reviews.json",
        "private": repo / "literature/.private/Fixture2000/tex/page-0003.tex",
        "report": repo / "literature/Fixture2000/reviews/Thm_1.md",
    }
    target = paths[changed]
    write = review.atomic_write_with_receipt
    calls = 0
    external = None

    def mutate_evidence(path, text):
        nonlocal calls, external
        receipt = write(path, text)
        calls += 1
        if calls == 1:
            if changed == "task":
                record["write_set"]["files"].remove("HomAlg/Fixture2000/Lem_1.lean")
                target.write_text(dump_metadata(record))
            else:
                target.write_text(target.read_text() + "\n")
            external = target.read_bytes()
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", mutate_evidence)
    with pytest.raises(ValueError, match="rolled-back"):
        review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert all(path.read_bytes() == content for path, content in before.items())
    assert target.read_bytes() == external
    assert [item["status"] for item in journals(repo)] == ["rolled-back"]
    assert [command[1] for command in commands] == ["build", "exe"]


def test_foreign_edit_to_written_cohort_is_preserved_and_blocks_retry(cohorts, monkeypatch):
    repo, _, commands, _, _, data = cohorts
    baseline.capture(cohorts)
    before = baseline.sources(cohorts)
    first, second = [node_path(repo, entry["node_ids"][0]) for entry in data["cohorts"]]
    write = review.atomic_write_with_receipt
    foreign = None

    def concurrent_edit(path, text):
        nonlocal foreign
        receipt = write(path, text)
        if path == second:
            foreign = first.read_bytes() + b"\n-- Fictional independent concurrent edit\n"
            first.write_bytes(foreign)
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", concurrent_edit)
    with pytest.raises(ValueError, match="recovery-required"):
        review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert first.read_bytes() == foreign
    assert second.read_bytes() == before[second]
    journal = journals(repo)
    assert len(journal) == 1 and journal[0]["status"] == "recovery-required"
    assert str(first) in journal[0]["recovery_conflicts"]
    commands.clear()
    with pytest.raises(ValueError, match="Unfinished fidelity transaction"):
        review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert not commands and first.read_bytes() == foreign


def test_snapshot_rechecks_task_after_last_union_verification(cohorts, monkeypatch):
    repo, record, commands, _, _, _ = cohorts
    before = baseline.sources(cohorts)
    verify = review._assert_snapshot

    def narrow_after_union(*args, **kwargs):
        verify(*args, **kwargs)
        record["write_set"]["files"].remove("HomAlg/Fixture2000/Lem_1.lean")
        path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
        path.write_text(dump_metadata(record))

    monkeypatch.setattr(review, "_assert_snapshot", narrow_after_union)
    with pytest.raises(ValueError, match="task scope changed"):
        baseline.capture(cohorts)
    assert not commands and not (repo / "build/reviews.json").exists()
    assert all(path.read_bytes() == content for path, content in before.items())


def test_separate_registration_makes_old_union_stale_before_new_export(cohorts):
    repo, _, commands, _, _, data = cohorts
    baseline.capture(cohorts)
    entry = data["cohorts"][0]
    review.review_fidelity_batch(
        repo,
        entry["node_ids"],
        by=entry["by"],
        session=entry["session"],
        author_session=entry["author_session"],
        now=NOW,
    )
    before = baseline.sources(cohorts)
    commands.clear()
    with pytest.raises(ValueError, match="snapshot is stale"):
        review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert not commands
    assert all(path.read_bytes() == content for path, content in before.items())


def test_missing_last_compiled_declaration_publishes_no_cohort_lock(cohorts, monkeypatch):
    repo, _, commands, _, _, _ = cohorts
    baseline.capture(cohorts)
    before = baseline.sources(cohorts)
    export = review_cohorts.export_lean

    def missing(*args, **kwargs):
        raw = export(*args, **kwargs)
        module = next(
            item for item in raw["modules"] if item["module"] == "HomAlg.Fixture2000.Lem_1"
        )
        module["decls"] = []
        return raw

    monkeypatch.setattr(review_cohorts, "export_lean", missing)
    with pytest.raises(ValueError, match="main declaration"):
        review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert not journals(repo)
    assert all(path.read_bytes() == content for path, content in before.items())
    assert [command[1] for command in commands] == ["build", "exe"]
