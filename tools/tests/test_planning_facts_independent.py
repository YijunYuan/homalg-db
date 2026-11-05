"""Independent mutation probes; all repositories and actor identities are fictional."""

import subprocess

import pytest
import test_planning_facts as baseline
from test_planning_inputs import git, initialize

from homalg import planning
from homalg.documents import dump_metadata
from homalg.planning_facts import PlanningFacts, StalePlanningInputs
from homalg.schemas import load_yaml
from homalg.validate import validate_repo

inputs = baseline.inputs


def test_index_only_change_invalidates_even_when_tracked_names_do_not_change(inputs):
    initialize(inputs)
    relative = "HomAlg/Fixture2000/Def_1.lean"
    git(inputs, "add", "--", relative)
    before_names = git(inputs, "ls-files", "-z")
    before_source = (inputs / relative).read_bytes()
    facts = PlanningFacts(inputs)
    facts.validation(baseline.KEY, validate_repo, fast=True)
    git(inputs, "update-index", "--assume-unchanged", "--", relative)
    assert git(inputs, "ls-files", "-z") == before_names
    assert (inputs / relative).read_bytes() == before_source
    with pytest.raises(StalePlanningInputs):
        facts.validation(baseline.KEY, validate_repo, fast=True)


def test_source_ledger_head_change_invalidates_without_source_change(inputs):
    ledger = inputs / ".archon-horizon/vcs/workspace.git"
    ledger.parent.mkdir(parents=True)
    subprocess.run(["git", "init", "--bare", "-q", str(ledger)], check=True)

    def ledger_git(*args):
        return subprocess.run(
            ["git", "--git-dir", str(ledger), *args],
            input="Fictional authority generation\n" if args[0] == "commit-tree" else None,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()

    ledger_git("config", "user.name", "Fictional operator")
    ledger_git("config", "user.email", "fixture@example.invalid")
    tree = ledger_git("mktree")
    first = ledger_git("commit-tree", tree)
    ledger_git("update-ref", "HEAD", first)
    facts = PlanningFacts(inputs)
    second = ledger_git("commit-tree", tree, "-p", first)
    ledger_git("update-ref", "HEAD", second)
    with pytest.raises(StalePlanningInputs):
        facts.assert_current()


@pytest.mark.parametrize(
    "relative,payload",
    [
        ("literature/Fixture2000/claim.yaml", "broken: [\n"),
        ("taxonomy/policy.yaml", "[]\n"),
    ],
)
def test_malformed_input_keeps_real_findings_skips_and_counts(inputs, relative, payload):
    (inputs / relative).write_text(payload)
    facts = PlanningFacts(inputs)
    direct = validate_repo(inputs, (baseline.KEY,), fast=True, now=facts.started.isoformat())
    cached = facts.validation(baseline.KEY, validate_repo, fast=True)
    assert cached == direct
    assert any(item.severity == "error" for item in cached[0])


def test_reconcile_rejects_changed_task_before_publishing_any_holds(inputs, monkeypatch):
    _, path, document = baseline.save_task(inputs, stage="STMT")
    task = load_yaml(path.read_text())
    task["status"] = "queued"
    path.write_text(dump_metadata(task))
    intended_by_other_actor = []

    def concurrent_change(*args, **kwargs):
        current = load_yaml(path.read_text())
        current["write_set"]["files"] = []
        path.write_text(dump_metadata(current))
        intended_by_other_actor.append(path.read_bytes())
        return {"complete": False}

    monkeypatch.setattr(planning, "evaluate", concurrent_change)
    with pytest.raises(StalePlanningInputs):
        planning.reconcile_frontier_holds(inputs, baseline.KEY, document["structure"], enabled=True)
    assert intended_by_other_actor and path.read_bytes() == intended_by_other_actor[-1]
    assert "dispatch_hold" not in load_yaml(path.read_text())["metadata"]
