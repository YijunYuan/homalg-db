"""Call-local facts preserve exact gates and abort on changed mathematical or temporal inputs."""

import json
import os
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from test_claims import claim, status
from test_planning_inputs import initialize, publish

from homalg import planning, stages
from homalg.checks.context import Finding
from homalg.documents import dump_metadata, read_document
from homalg.planning_facts import PlanningFacts, StalePlanningInputs
from homalg.schemas import load_yaml

ROOT = Path(__file__).resolve().parents[2]
KEY = "Fixture2000"


@pytest.fixture
def inputs(repo):
    shutil.copytree(ROOT / "horizon", repo / "horizon")
    (repo / "build").mkdir()
    shutil.copyfile(
        ROOT / "tools/tests/golden/fixture-export.json", repo / f"build/lean-export-{KEY}.json"
    )
    return repo


def save_task(repo, stage="INV", number=1):
    document = read_document(repo, KEY)
    record = planning.proposed_task(repo, KEY, stage, number, chapter="1", pages=[1])
    record["status"] = "done"  # This must never confer completion on its own.
    path = repo / f".archon-horizon/tasks/items/{record['id']}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_metadata(record))
    return record, path, document


def test_exact_modes_reuse_complete_validation_tuple_and_defensive_copies(inputs):
    facts = PlanningFacts(inputs)
    calls = []

    def validate(repo, selected, **kwargs):
        calls.append((repo, selected, kwargs))
        return (
            [Finding("fictional-rule", "warning", "fixture", "Retain warning")],
            ["lean-build"],
            {"nodes": 7},
        )

    export = inputs / f"build/lean-export-{KEY}.json"
    first = facts.validation(KEY, validate, fast=True)
    first[0].clear()
    first[1].clear()
    first[2]["nodes"] = 99
    second = facts.validation(KEY, validate, fast=True)
    assert len(second[0]) == 1 and second[1] == ["lean-build"] and second[2] == {"nodes": 7}
    facts.validation(KEY, validate, fast=False, export=export)
    facts.validation(KEY, validate, fast=False, export=export)
    assert len(calls) == 2
    assert calls[0][2]["fast"] is True and "no_build" not in calls[0][2]
    assert calls[1][2]["fast"] is False and calls[1][2]["no_build"] is True
    assert calls[0][2]["now"] == calls[1][2]["now"] == facts.started.isoformat()
    with pytest.raises(ValueError, match="guarded document path"):
        facts.validation(KEY, validate, fast=False, export=inputs / "build/other.json")


def test_state_reuse_is_by_document_and_loader_and_not_shared_between_calls(inputs):
    calls = []

    def state(repo, key):
        calls.append(key)
        return {"doc_key": key, "nodes": []}

    facts = PlanningFacts(inputs)
    facts.state(KEY, state)["nodes"].append("not authoritative")
    assert facts.state(KEY, state)["nodes"] == []
    facts.state("Fixture2001", state)
    assert calls == [KEY, "Fixture2001"]
    PlanningFacts(inputs).state(KEY, state)
    assert calls == [KEY, "Fixture2001", KEY]


@pytest.mark.parametrize(
    "relative",
    [
        "HomAlg/Fixture2000/Def_1.lean",
        "HomAlg/Fixture2001/Thm_1.lean",
        "literature/Fixture2000/document.yaml",
        "literature/Fixture2001/claim.yaml",
        "literature/Fixture2000/reviews/Def_1.md",
        "horizon/review-policy.yaml",
        "horizon/owner-decision-replays.json",
        "taxonomy/tags.yaml",
        "schema/common.schema.json",
        "literature/Fixture2000/owner-decisions/fixture.json",
        "literature/.private/Fixture2000/transcription.yaml",
        "literature/.private/Fixture2000/tex/page-0001.tex",
        "build/lean-export-Fixture2000.json",
        "build/lean-export-new.json",
        "site/public/data/health.json",
        ".archon-horizon/tasks/items/Fixture2000.STMT.1.yaml",
        "unrelated-public-directory/source.pdf",
    ],
)
def test_changed_new_or_foreign_input_aborts_cached_evidence(inputs, relative):
    facts = PlanningFacts(inputs)
    calls = []

    def state(repo, key):
        calls.append(key)
        return {"nodes": []}

    facts.state(KEY, state)
    path = inputs / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((path.read_text() if path.is_file() else "") + "\nchanged fixture input\n")
    with pytest.raises(StalePlanningInputs, match="changed"):
        facts.state(KEY, state)
    assert calls == [KEY]


def test_export_deletion_and_mtime_order_are_inputs(inputs):
    path = inputs / f"build/lean-export-{KEY}.json"
    facts = PlanningFacts(inputs)
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1))
    with pytest.raises(StalePlanningInputs):
        facts.assert_current()
    facts = PlanningFacts(inputs)
    path.unlink()
    with pytest.raises(StalePlanningInputs):
        facts.assert_current()


def test_mutation_during_computation_is_not_cached_or_downgraded(inputs):
    record, _, document = save_task(inputs)

    def changed(repo, selected, **kwargs):
        path = inputs / "HomAlg/Fixture2000/Def_1.lean"
        path.write_text(path.read_text() + "\n-- changed while checking\n")
        return [], [], {}

    facts = PlanningFacts(inputs)
    with pytest.raises(StalePlanningInputs):
        facts.validation(KEY, changed, fast=True)
    assert facts._cache == {}


def test_mutation_escapes_planner_per_task_failure_fallback(inputs, monkeypatch):
    _, task_path, document = save_task(inputs)

    def changed(repo, selected, **kwargs):
        task = load_yaml(task_path.read_text())
        task["write_set"]["files"] = []
        task_path.write_text(dump_metadata(task))
        return [], [], {}

    monkeypatch.setattr(stages, "validate_repo", changed)
    with pytest.raises(StalePlanningInputs):
        planning.unlocked_tasks(inputs, KEY, document["structure"], persist_transcription=False)


def test_failed_validation_is_never_a_cache_entry(inputs):
    facts = PlanningFacts(inputs)
    calls = []

    def failed(*args, **kwargs):
        calls.append(1)
        raise ValueError("fictional invalid input")

    for _ in range(2):
        with pytest.raises(ValueError, match="fictional invalid"):
            facts.validation(KEY, failed, fast=True)
    assert calls == [1, 1] and facts._cache == {}


def test_task_specific_failures_and_standalone_behavior_are_unchanged(inputs, monkeypatch):
    calls = []
    original = stages.validate_repo

    def counted(*args, **kwargs):
        calls.append(kwargs.get("fast"))
        return original(*args, **kwargs)

    monkeypatch.setattr(stages, "validate_repo", counted)
    records = [
        planning.proposed_task(inputs, KEY, "INV", number, chapter="1", pages=[number])
        for number in [1, 999]
    ]
    records += [
        planning.proposed_task(inputs, KEY, stage, 1, chapter="1") for stage in ["DAG", "STMT"]
    ]
    standalone = [
        stages.evaluate(inputs, record, refresh_exports=False, persist_transcription=False)
        for record in records
    ]
    facts = PlanningFacts(inputs)
    cached = [
        stages.evaluate(
            inputs, record, refresh_exports=False, persist_transcription=False, facts=facts
        )
        for record in records
    ]
    assert cached == standalone
    assert any("0999" in error for error in cached[1]["failures"])
    assert calls.count(True) == 3  # standalone twice, one shared invocation
    assert calls.count(False) == 2
    with pytest.raises(ValueError, match="read-only"):
        stages.evaluate(inputs, records[0], facts=facts)
    other = inputs / "another-repository"
    other.mkdir()
    with pytest.raises(ValueError, match="another repository"):
        facts.require_repo(other)


def test_actual_claim_expiry_invalidates_without_file_mutation(inputs):
    now = datetime(2026, 1, 5, tzinfo=UTC)
    data = claim()
    data["doc_key"] = KEY
    data["claims"][0]["expires_at"] = (now + timedelta(seconds=2)).isoformat()
    (inputs / f"literature/{KEY}/claim.yaml").write_text(dump_metadata(data))
    clock = [now]
    facts = PlanningFacts(inputs, clock=lambda: clock[0])
    facts.assert_current()
    clock[0] += timedelta(seconds=2)
    with pytest.raises(StalePlanningInputs, match="claim/time"):
        facts.assert_current()
    # A new invocation must perform ordinary checks against the now-expired claim.
    PlanningFacts(inputs, clock=lambda: clock[0]).assert_current()


def test_future_status_admission_and_new_status_ref_invalidate(inputs):
    initialize(inputs)
    now = datetime(2026, 1, 5, tzinfo=UTC)
    data = claim()
    data["doc_key"] = KEY
    (inputs / f"literature/{KEY}/claim.yaml").write_text(dump_metadata(data))
    publication = status((now + timedelta(minutes=20)).isoformat()) | {"doc_key": KEY}
    publish(inputs, KEY, json.dumps(publication))
    clock = [now]
    facts = PlanningFacts(inputs, clock=lambda: clock[0])
    clock[0] += timedelta(minutes=10)
    with pytest.raises(StalePlanningInputs, match="claim/time"):
        facts.assert_current()
    facts = PlanningFacts(inputs, clock=lambda: clock[0])
    publish(inputs, KEY, json.dumps(status(clock[0].isoformat()) | {"doc_key": KEY}))
    with pytest.raises(StalePlanningInputs, match="inputs changed"):
        facts.assert_current()


def test_malformed_claim_and_policy_are_left_to_ordinary_validation(inputs):
    (inputs / f"literature/{KEY}/claim.yaml").write_text("broken: [\n")
    PlanningFacts(inputs).assert_current()
    (inputs / "taxonomy/policy.yaml").write_text("[]\n")
    PlanningFacts(inputs).assert_current()


def test_native_authority_metadata_is_guarded(inputs, monkeypatch):
    monkeypatch.setenv("ARCHON_HORIZON_RUN", "fictional-run")
    monkeypatch.setenv("ARCHON_HORIZON_SESSION", "fictional-session")
    facts = PlanningFacts(inputs)
    path = inputs / ".archon-horizon/runs/fictional-run/sessions/fictional-session/meta.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"start_sha":"forged"}\n')
    with pytest.raises(StalePlanningInputs):
        facts.assert_current()
