"""Partial statement units settle per primary without relaxing any stage gate."""

import copy
import json
from pathlib import Path

import pytest
from test_engine_integration import fake_engine
from test_statement_frontier import KEY, edit_node, frontier_repo  # noqa: F401

from homalg import lifecycle, planning, publishing, settlement, stages
from homalg.documents import dump_metadata, parse_metadata, read_document

LOCK = "a current satisfactory statement lock is required"


def lean(local: str) -> str:
    return f"HomAlg/{KEY}/{local}.lean"


def review(local: str) -> str:
    return f"literature/{KEY}/reviews/{local}.md"


def batch(*locals_: str, status: str = "blocked") -> dict:
    node_ids = []
    for local in locals_:
        node_ids.append(f"{KEY}.{local}")
        if local == "Thm_1":
            node_ids.append(f"{KEY}.Aux_Thm_1_step")
    files = sorted(
        [lean(identifier.split(".")[1]) for identifier in node_ids]
        + [review(identifier.split(".")[1]) for identifier in node_ids]
    )
    return {
        "id": f"{KEY}.STMT.UnitBatch_test",
        "status": status,
        "priority": "high",
        "inbox_refs": ["I-0007"],
        "roadmap_refs": [f"{KEY}.STMT"],
        "write_set": {"files": list(files)},
        "scope": {"projects": ["HomAlg"], "files": list(files)},
        "metadata": {
            "homalg": {
                "doc": KEY,
                "stage": "STMT",
                "chapter": "1",
                "attempts": 0,
                "pages": [1, 2],
                "granularity": "node",
                "kind_group": "items",
                "node_ids": node_ids,
                "primary_nodes": [f"{KEY}.{local}" for local in locals_],
                "author_groups": [
                    {
                        "primary": f"{KEY}.{local}",
                        "node_ids": [f"{KEY}.{local}"]
                        + ([f"{KEY}.Aux_Thm_1_step"] if local == "Thm_1" else []),
                    }
                    for local in locals_
                ],
            }
        },
    }


def save(repo: Path, record: dict) -> Path:
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_metadata(record))
    return path


def write_export(repo, key, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("{}")


def complete(record):
    return {"complete": True, "failures": [], "task": record["id"]}


def test_failure_on_an_aux_node_releases_its_primary_group_only(repo: Path) -> None:
    record = batch("Thm_1", "Thm_2", "Prop_1")
    evaluation = {"complete": False, "failures": [f"{KEY}.Aux_Thm_1_step: {LOCK}"]}
    seen = []
    plan = settlement.plan_settlement(
        repo, record, evaluation, lambda narrowed: seen.append(narrowed) or complete(narrowed)
    )
    assert plan["applicable"]
    assert plan["retained"] == [f"{KEY}.Prop_1", f"{KEY}.Thm_2"]
    assert plan["released"] == {f"{KEY}.Thm_1": [f"{KEY}.Aux_Thm_1_step", f"{KEY}.Thm_1"]}
    assert sorted(plan["released_files"]) == sorted(
        [lean("Aux_Thm_1_step"), lean("Thm_1"), review("Aux_Thm_1_step"), review("Thm_1")]
    )
    narrowed = seen[0]
    info = narrowed["metadata"]["homalg"]
    assert info["node_ids"] == [f"{KEY}.Thm_2", f"{KEY}.Prop_1"]
    assert info["primary_nodes"] == [f"{KEY}.Thm_2", f"{KEY}.Prop_1"]
    assert [group["primary"] for group in info["author_groups"]] == [
        f"{KEY}.Thm_2",
        f"{KEY}.Prop_1",
    ]
    assert narrowed["write_set"]["files"] == narrowed["scope"]["files"]
    assert set(narrowed["write_set"]["files"]) == {
        lean("Thm_2"),
        lean("Prop_1"),
        review("Thm_2"),
        review("Prop_1"),
    }
    # The immutable input record is untouched until the caller applies the plan.
    assert record["metadata"]["homalg"]["node_ids"][0] == f"{KEY}.Thm_1"


@pytest.mark.parametrize(
    "failures, reason",
    [
        (["lean-build: Thm_2 does not compile", f"{KEY}.Thm_1: {LOCK}"], "unattributable"),
        (["No current compiled document export is available"], "unattributable"),
        ([f"{KEY}.Def_2: {LOCK}"], "unattributable"),
        ([f"{KEY}.Thm_1: {LOCK}", f"{KEY}.Thm_2: {LOCK}", f"{KEY}.Prop_1: {LOCK}"], "no primary"),
        ([], "without recorded failures"),
    ],
)
def test_unattributable_or_total_failures_never_settle(repo, failures, reason) -> None:
    record = batch("Thm_1", "Thm_2", "Prop_1")
    plan = settlement.plan_settlement(
        repo,
        record,
        {"complete": False, "failures": failures},
        lambda narrowed: pytest.fail("narrowed evaluation must not run"),
    )
    assert not plan["applicable"]
    assert reason in plan["reason"]


def test_narrowed_unit_must_pass_the_identical_evaluation_on_its_own(repo: Path) -> None:
    record = batch("Thm_1", "Thm_2")
    plan = settlement.plan_settlement(
        repo,
        record,
        {"complete": False, "failures": [f"{KEY}.Thm_1: {LOCK}"]},
        lambda narrowed: {
            "complete": False,
            "failures": [f"{KEY}.Thm_2: statement interface is not current: {KEY}.Thm_1"],
        },
    )
    assert not plan["applicable"]
    assert plan["narrowed_failures"]


def test_non_unit_and_complete_tasks_are_left_alone(repo: Path) -> None:
    record = batch("Thm_1", "Thm_2")
    chapter = copy.deepcopy(record)
    chapter["metadata"]["homalg"].pop("granularity")
    assert not settlement.plan_settlement(
        repo, chapter, {"complete": False, "failures": [f"{KEY}.Thm_1: x"]}, complete
    )["applicable"]
    assert not settlement.plan_settlement(repo, record, {"complete": True}, complete)["applicable"]


def test_apply_writes_narrowed_scope_and_session_bound_audit_allowance(repo: Path) -> None:
    record = batch("Thm_1", "Thm_2")
    path = save(repo, record)
    plan = settlement.plan_settlement(
        repo, record, {"complete": False, "failures": [f"{KEY}.Thm_1: {LOCK}"]}, complete
    )
    entry = settlement.apply_settlement(repo, plan, interval=("a" * 40, "b" * 40))
    saved = parse_metadata(path.read_text())
    info = saved["metadata"]["homalg"]
    assert info["node_ids"] == [f"{KEY}.Thm_2"]
    assert saved["write_set"]["files"] == [lean("Thm_2"), review("Thm_2")]
    assert saved["scope"]["files"] == [lean("Thm_2"), review("Thm_2")]
    assert saved["status"] == "blocked"  # the caller owns the status transition
    assert info["settlements"][-1]["released_files"] == entry["released_files"]
    allowed = settlement.released_scope(saved, "a" * 40, "b" * 40)
    assert lean("Thm_1") in allowed and lean("Aux_Thm_1_step") in allowed
    assert settlement.released_scope(saved, "c" * 40, "b" * 40) == set()


def test_open_dispute_is_never_batched_with_ready_siblings(frontier_repo) -> None:  # noqa: F811
    repo = frontier_repo
    structure = read_document(repo, KEY)["structure"]
    before = {
        item["id"]: item["node_ids"]
        for item in planning.statement_units(repo, KEY, structure, batch_size=4)
    }
    batched = next(nodes for name, nodes in before.items() if ".UnitBatch_" in name)
    assert f"{KEY}.Def_2" in batched

    def dispute(metadata):
        metadata["dispute"] = {
            "status": "open",
            "kind": "proof",
            "reason": "printed proof uses the wrong module",
            "on": "2026-11-05",
        }

    edit_node(repo, "Def_2", dispute)
    after = planning.statement_units(repo, KEY, structure, batch_size=4)
    nodes = {item["id"]: item["node_ids"] for item in after}
    assert nodes[f"{KEY}.STMT.Unit_Def_2"] == [f"{KEY}.Def_2"]
    assert all(
        f"{KEY}.Def_2" not in members
        for name, members in nodes.items()
        if name != f"{KEY}.STMT.Unit_Def_2"
    )


@pytest.fixture
def engine_calls(frontier_repo: Path, monkeypatch: pytest.MonkeyPatch) -> list:  # noqa: F811
    calls = []

    def horizon(root, *args):
        calls.append(args)
        if args[0] == "roadmap" or args[0] == "inbox":
            return fake_engine(root, *args)
        if args[:2] == ("task", "add"):
            identifier = args[args.index("--id") + 1]
            save(
                root,
                {
                    "id": identifier,
                    "status": "queued",
                    "priority": "normal",
                    "objective": args[args.index("--objective") + 1],
                    "write_set": {
                        "files": [args[i + 1] for i, value in enumerate(args) if value == "--file"]
                    },
                    "metadata": {},
                },
            )
        elif args[:2] == ("task", "set"):
            path = root / ".archon-horizon/tasks/items" / f"{args[2]}.yaml"
            current = parse_metadata(path.read_text())
            if "--status" in args:
                current["status"] = args[args.index("--status") + 1]
            if "--priority" in args:
                current["priority"] = args[args.index("--priority") + 1]
            refs = [args[i + 1] for i, value in enumerate(args) if value == "--inbox-ref"]
            if refs:
                current["inbox_refs"] = refs
            path.write_text(dump_metadata(current))
        return "{}"

    monkeypatch.setattr(settlement, "horizon", horizon)
    monkeypatch.setattr(planning, "horizon", horizon)
    monkeypatch.setattr(lifecycle.engine, "horizon", horizon)
    return calls


def test_only_ready_released_primaries_get_a_unit(frontier_repo: Path, engine_calls) -> None:  # noqa: F811
    repo = frontier_repo
    # The source has already been narrowed and accepted; it covers neither primary.
    source = batch("Def_2", "Thm_1", status="done")
    save(repo, source)
    released = {
        f"{KEY}.Def_2": [f"{KEY}.Def_2"],
        f"{KEY}.Thm_1": [f"{KEY}.Aux_Thm_1_step", f"{KEY}.Thm_1"],
    }
    created = settlement.ensure_units(repo, KEY, released, source=source, login="fixture-user")
    # Thm_1 still lacks reviewed interfaces; planning creates it once they are accepted.
    assert created == [f"{KEY}.STMT.Unit_Def_2"]
    unit = parse_metadata(
        (repo / f".archon-horizon/tasks/items/{KEY}.STMT.Unit_Def_2.yaml").read_text()
    )
    assert unit["metadata"]["homalg"]["released_from"] == source["id"]
    assert unit["metadata"]["homalg"]["node_ids"] == [f"{KEY}.Def_2"]
    assert unit["inbox_refs"] == ["I-0007"]
    assert unit["write_set"]["files"] == [lean("Def_2"), review("Def_2")]
    # A primary already covered by an active task is not duplicated.
    assert settlement.ensure_units(repo, KEY, released, source=source, login="u") == []


def test_cancelled_unit_releases_only_settled_primaries_to_the_frontier(
    frontier_repo: Path,  # noqa: F811
) -> None:
    repo = frontier_repo
    structure = read_document(repo, KEY)["structure"]

    def planned_nodes():
        # Newly proposed units only; existing registered units are echoed back unchanged.
        return {
            node
            for item in planning.statement_units(repo, KEY, structure, batch_size=4)
            if "status" not in item
            for node in item["node_ids"]
        }

    hold = batch("Def_2", status="cancelled")
    hold["id"] = f"{KEY}.STMT.Unit_Def_2_hold"
    save(repo, hold)
    assert f"{KEY}.Def_2" not in planned_nodes()  # an operator cancellation still holds
    source = batch("Def_2", "Rem_1", status="done")
    source["metadata"]["homalg"]["settlements"] = [
        {"released": {f"{KEY}.Def_2": [f"{KEY}.Def_2"]}, "released_files": []}
    ]
    source["metadata"]["homalg"]["node_ids"] = [f"{KEY}.Rem_1"]
    source["metadata"]["homalg"]["primary_nodes"] = [f"{KEY}.Rem_1"]
    save(repo, source)
    assert f"{KEY}.Def_2" in planned_nodes()


def patch_hook(monkeypatch: pytest.MonkeyPatch, *, validation=()) -> list:
    planned = []
    monkeypatch.setattr(lifecycle.scope, "check_scope", lambda *args: [])
    monkeypatch.setattr(lifecycle, "private_after_session", lambda *args: {"violations": []})
    monkeypatch.setattr(lifecycle, "export_lean", write_export)
    monkeypatch.setattr(lifecycle, "validate_repo", lambda *args, **kw: (list(validation), [], {}))
    monkeypatch.setattr(lifecycle, "progress_made", lambda *args: True)
    monkeypatch.setattr(publishing, "publish_status", lambda *args, **kw: {})
    monkeypatch.setattr(publishing, "notify", lambda *args, **kw: "I-0001")
    monkeypatch.setattr(lifecycle, "backup", lambda *args, **kw: {})
    monkeypatch.setattr(lifecycle.planning, "plan", lambda *args, **kw: planned.append(1) or {})
    return planned


def failing_on(local: str):
    def evaluate(repo, current, **kwargs):
        if f"{KEY}.{local}" in current["metadata"]["homalg"]["node_ids"]:
            return {"complete": False, "failures": [f"{KEY}.{local}: {LOCK}"]}
        return {"complete": True, "failures": []}

    return evaluate


def test_after_session_settles_then_marks_the_narrowed_unit_done(
    frontier_repo: Path,  # noqa: F811
    engine_calls,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = frontier_repo
    record = plain(repo, batch("Def_2", "Rem_1"))
    path = save(repo, record)
    planned = patch_hook(monkeypatch)
    monkeypatch.setattr(stages, "evaluate", failing_on("Def_2"))
    result = lifecycle.after_session(repo, record["id"], repo / "session", "a" * 40, "b" * 40)
    assert result["settlement"]["applicable"]
    assert result["evaluation"]["complete"]
    assert result["status"] == "done"
    assert planned == [1]
    assert result["released_units"] == [f"{KEY}.STMT.Unit_Def_2"]
    saved = parse_metadata(path.read_text())
    assert saved["status"] == "done"
    assert saved["metadata"]["homalg"]["node_ids"] == [f"{KEY}.Rem_1"]
    assert saved["metadata"]["homalg"]["settlements"][0]["interval"] == ["a" * 40, "b" * 40]


def test_after_session_never_settles_when_document_validation_fails(
    frontier_repo: Path,  # noqa: F811
    engine_calls,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from homalg.validate import Finding

    repo = frontier_repo
    record = batch("Def_2", "Rem_1")
    path = save(repo, record)
    patch_hook(monkeypatch, validation=[Finding("schema", "error", "x.yaml", "broken")])
    monkeypatch.setattr(stages, "evaluate", failing_on("Def_2"))
    result = lifecycle.after_session(repo, record["id"], repo / "session", "a" * 40, "b" * 40)
    assert "settlement" not in result
    assert parse_metadata(path.read_text())["metadata"]["homalg"]["node_ids"][0] == f"{KEY}.Def_2"


def test_settle_document_dry_run_reports_and_apply_closes_and_settles(
    frontier_repo: Path,  # noqa: F811
    engine_calls,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = frontier_repo
    done_already = batch("Thm_2", status="queued")
    done_already["id"] = f"{KEY}.STMT.Unit_Thm_2"
    partial = batch("Def_2", "Rem_1")
    held = batch("Thm_3", "Thm_4", status="queued")
    held["id"] = f"{KEY}.STMT.UnitBatch_held"
    for record in (done_already, partial, held):
        save(repo, plain(repo, record))
    settle_on_def_2 = failing_on("Def_2")

    def evaluate(repo, current, **kwargs):
        if current["id"] == held["id"]:
            return {"complete": False, "failures": ["lean-build: document does not compile"]}
        return settle_on_def_2(repo, current, **kwargs)

    monkeypatch.setattr(stages, "evaluate", evaluate)
    dry = settlement.settle_document(repo, KEY)
    actions = {item["task"]: item["action"] for item in dry["actions"]}
    assert actions == {done_already["id"]: "close", partial["id"]: "settle", held["id"]: "none"}
    saved = parse_metadata((repo / f".archon-horizon/tasks/items/{partial['id']}.yaml").read_text())
    assert saved["metadata"]["homalg"]["node_ids"][0] == f"{KEY}.Def_2"
    assert engine_calls == []

    import homalg.human

    monkeypatch.setattr(homalg.human, "require_idle", lambda repo: None)
    monkeypatch.setattr(planning, "plan", lambda *args, **kw: {"created_tasks": []})
    applied = settlement.settle_document(repo, KEY, apply=True)
    assert applied["created_tasks"] == [f"{KEY}.STMT.Unit_Def_2"]
    status = {
        record["id"]: parse_metadata(
            (repo / f".archon-horizon/tasks/items/{record['id']}.yaml").read_text()
        )["status"]
        for record in (done_already, partial, held)
    }
    assert status == {done_already["id"]: "done", partial["id"]: "done", held["id"]: "queued"}
    closure = parse_metadata(
        (repo / f".archon-horizon/tasks/items/{done_already['id']}.yaml").read_text()
    )["metadata"]["homalg"]["evidence_closure"]
    assert closure["complete"] and json.dumps(closure)


def plain(repo: Path, record: dict) -> dict:
    """Give a test record the objective the planner would generate for it."""
    record["node_ids"] = record["metadata"]["homalg"]["node_ids"]
    record["objective"] = generated(repo, record)
    return record


def generated(repo: Path, record: dict) -> str:
    return planning.render_objective(
        repo, record, login="fixture-user", document=read_document(repo, KEY)
    )


def test_generated_objectives_are_plain_and_extended_ones_are_not(
    frontier_repo: Path,  # noqa: F811
) -> None:
    repo = frontier_repo
    record = batch("Def_2", "Rem_1")
    record["metadata"]["homalg"]["node_ids"] = [f"{KEY}.Def_2", f"{KEY}.Rem_1"]
    record["node_ids"] = record["metadata"]["homalg"]["node_ids"]
    legacy = generated(repo, record)
    record["objective"] = legacy
    assert "Native parallel author groups" in legacy
    assert settlement.auto_eligible(repo, record)
    extra = "Prove the transfinite certificates before releasing consumers."
    record["objective"] = legacy + "\n\n" + extra
    assert settlement.objective_extension(repo, record).startswith(extra)
    assert "horizon task show" in settlement.objective_extension(repo, record)
    assert not settlement.auto_eligible(repo, record)
    rewritten = dict(record, objective="Verify the existing aggregate under its scope.")
    assert not settlement.auto_eligible(repo, rewritten)
    assert settlement.objective_extension(repo, rewritten).startswith("The source objective")
    # A recorded digest is authoritative for tasks created after this change.
    import hashlib

    record["metadata"]["homalg"]["objective_sha256"] = hashlib.sha256(legacy.encode()).hexdigest()
    assert not settlement.auto_eligible(repo, record)
    record["objective"] = legacy
    assert settlement.auto_eligible(repo, record)


def test_extended_task_needs_explicit_selection_and_passes_its_guidance_on(
    frontier_repo: Path,  # noqa: F811
    engine_calls,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = frontier_repo
    partial = batch("Def_2", "Rem_1")
    partial["node_ids"] = partial["metadata"]["homalg"]["node_ids"]
    extra = "Register the Baer certificate continuation for a later session."
    partial["objective"] = generated(repo, partial) + "\n\n" + extra
    save(repo, partial)
    monkeypatch.setattr(stages, "evaluate", failing_on("Def_2"))
    automatic = settlement.settle_document(repo, KEY)
    assert [item["action"] for item in automatic["actions"]] == ["none"]
    assert "--task" in automatic["actions"][0]["reason"]

    import homalg.human

    monkeypatch.setattr(homalg.human, "require_idle", lambda repo: None)
    monkeypatch.setattr(planning, "plan", lambda *args, **kw: {"created_tasks": []})
    applied = settlement.settle_document(repo, KEY, task_ids=(partial["id"],), apply=True)
    assert applied["created_tasks"] == [f"{KEY}.STMT.Unit_Def_2"]
    saved = parse_metadata((repo / f".archon-horizon/tasks/items/{partial['id']}.yaml").read_text())
    carried = saved["metadata"]["homalg"]["settlements"][-1]["inherit"]
    assert carried["source"] == partial["id"] and carried["inbox_refs"] == ["I-0007"]
    assert carried["guidance"].startswith(extra)
    unit = parse_metadata(
        (repo / f".archon-horizon/tasks/items/{KEY}.STMT.Unit_Def_2.yaml").read_text()
    )
    assert extra in unit["objective"] and partial["id"] in unit["objective"]
    assert unit["inbox_refs"] == ["I-0007"]
    assert "objective_sha256" not in unit["metadata"]["homalg"]


def test_planning_creates_released_units_with_inherited_guidance(
    frontier_repo: Path,  # noqa: F811
    engine_calls,
) -> None:
    repo = frontier_repo
    planning.plan(repo, KEY, no_claim=True)
    source = batch("Def_2", "Rem_1", status="done")
    source["metadata"]["homalg"]["node_ids"] = [f"{KEY}.Rem_1"]
    source["metadata"]["homalg"]["primary_nodes"] = [f"{KEY}.Rem_1"]
    source["metadata"]["homalg"]["settlements"] = [
        {
            "released": {f"{KEY}.Def_2": [f"{KEY}.Def_2"]},
            "released_files": [],
            "inherit": {
                "source": source["id"],
                "guidance": "Keep I.6.1 pending.",
                "inbox_refs": ["I-0044"],
            },
        }
    ]
    save(repo, source)
    result = planning.plan(
        repo, KEY, advance=True, statement_frontier=True, proofs="deferred", statement_batch_size=1
    )
    assert f"{KEY}.STMT.Unit_Def_2" in result["created_tasks"]
    unit = parse_metadata(
        (repo / f".archon-horizon/tasks/items/{KEY}.STMT.Unit_Def_2.yaml").read_text()
    )
    assert "Keep I.6.1 pending." in unit["objective"]
    assert unit["inbox_refs"] == ["I-0044"]
    plain = parse_metadata(
        (repo / f".archon-horizon/tasks/items/{KEY}.STMT.Unit_Def_1.yaml").read_text()
    )
    assert settlement.auto_eligible(repo, plain)
    assert plain["metadata"]["homalg"]["objective_sha256"]
