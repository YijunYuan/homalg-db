"""Authoring and review run as separate units; review identities here are fictional."""

from pathlib import Path

import pytest
from test_engine_integration import fake_engine
from test_statement_frontier import KEY, edit_node, frontier_repo, save_task, unit  # noqa: F401
from test_workflow import GOLDEN

from homalg import leanexport, phases, planning, settlement, stages, workflow
from homalg.documents import dump_metadata, parse_metadata, read_document
from homalg.statement_frontier import StatementFrontier

DEF_1 = f"{KEY}.Def_1"
GROUP = [DEF_1, f"{KEY}.Bridge_Def_1_mathlib"]


@pytest.fixture
def lean(frontier_repo, monkeypatch):  # noqa: F811
    calls = []

    def run(_repo, command):
        calls.append(command)
        return "" if command[1] == "build" else GOLDEN.read_text()

    monkeypatch.setattr(leanexport, "run_tool", run)
    monkeypatch.setattr(planning, "horizon", engine)
    monkeypatch.setattr(settlement, "horizon", engine)
    return frontier_repo, calls


def engine(root, *args):
    if args[:2] == ("task", "set"):
        path = root / ".archon-horizon/tasks/items" / f"{args[2]}.yaml"
        current = parse_metadata(path.read_text())
        if "--status" in args:
            current["status"] = args[args.index("--status") + 1]
        if "--priority" in args:
            current["priority"] = args[args.index("--priority") + 1]
        path.write_text(dump_metadata(current))
        return "{}"
    result = fake_engine(root, *args)
    if args[:2] == ("task", "add") and "--priority" in args:
        path = root / ".archon-horizon/tasks/items" / f"{result}.yaml"
        current = parse_metadata(path.read_text())
        current["priority"] = args[args.index("--priority") + 1]
        path.write_text(dump_metadata(current))
    return result


def author_unit(repo: Path, status: str = "queued") -> dict:
    record = unit(repo, "Def_1")
    assert record["metadata"]["homalg"]["phase"] == "author"
    save_task(repo, record)
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    current = parse_metadata(path.read_text())
    current["status"] = status
    path.write_text(dump_metadata(current))
    return current


def deliver(repo: Path, record: dict, out: str = "build/handoff.json", author="writer-a"):
    return workflow.prepare(
        repo, record["id"], author_session=author, out=Path(out), node_ids=tuple(GROUP)
    )


def finish(repo: Path, record: dict) -> None:
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    current = parse_metadata(path.read_text())
    current["status"] = "done"
    path.write_text(dump_metadata(current))


def states(repo: Path) -> dict:
    return phases.node_states(repo, KEY, StatementFrontier(repo, KEY))


def test_delivery_is_recorded_scoped_and_completes_the_author_unit(lean):
    repo, calls = lean
    record = author_unit(repo)
    assert phases.author_failures(repo, record) == [
        f"{node}: a current author handoff is required" for node in sorted(GROUP)
    ]
    data = deliver(repo, record)
    assert data["ready_for_review"]
    # Only this unit's modules are built and exported.
    modules = (repo / "build/modules-Fixture2000-scoped.txt").read_text().split()
    assert modules == sorted(f"HomAlg.{node}" for node in GROUP)
    assert [command[1] for command in calls] == ["build", "exe"]
    recorded = workflow.task_handoffs(repo, record["id"])
    assert len(recorded) == 1 and recorded[0][1] == data
    assert phases.author_failures(repo, record) == []
    evaluation = stages.evaluate(repo, record, refresh_exports=False)
    assert evaluation["complete"], evaluation["failures"]
    assert len(calls) == 2  # completion is judged from the delivery, without an export


def test_a_changed_dependency_returns_the_node_to_authoring(lean):
    repo, _ = lean
    record = author_unit(repo)
    deliver(repo, record)
    path = repo / f"HomAlg/{KEY}/Def_1.lean"
    path.write_text(path.read_text() + "\n-- clarified after delivery\n")
    assert f"{DEF_1}: a current author handoff is required" in phases.author_failures(repo, record)


def test_delivered_nodes_await_review_and_get_a_review_unit(lean):
    repo, _ = lean
    record = author_unit(repo)
    deliver(repo, record)
    finish(repo, record)
    assert states(repo)[DEF_1]["state"] == "awaiting_review"
    structure = read_document(repo, KEY)["structure"]
    # No second author unit for a node that is waiting for review.
    proposed = planning.statement_units(repo, KEY, structure, batch_size=4)
    assert all(DEF_1 not in item["node_ids"] for item in proposed if "status" not in item)
    reviews = phases.review_units(repo, KEY, structure, frontier=StatementFrontier(repo, KEY))
    assert len(reviews) == 1
    review = reviews[0]
    info = review["metadata"]["homalg"]
    assert info["phase"] == "review" and info["primary_nodes"] == [DEF_1]
    assert info["node_ids"] == GROUP
    assert info["handoffs"][0]["author_session"] == "writer-a"
    assert f"HomAlg/{KEY}/Def_1.lean" in review["write_set"]["files"]
    planning.create_task(repo, review, login="fixture-user", document=read_document(repo, KEY))
    saved = parse_metadata(
        (repo / ".archon-horizon/tasks/items" / f"{review['id']}.yaml").read_text()
    )
    assert saved["priority"] == "urgent"
    assert "Independently review and register" in saved["objective"]
    assert info["handoffs"][0]["path"] in saved["objective"]
    assert settlement.auto_eligible(repo, saved)
    assert states(repo)[DEF_1]["state"] == "active"


def test_handoffs_command_reports_freshness_and_copies_below_build(lean):
    repo, _ = lean
    record = author_unit(repo)
    deliver(repo, record)
    listed = workflow.list_handoffs(repo, record["id"], copy=Path("build/copied"))
    entry = listed["handoffs"][0]
    assert entry["fresh"] and set(entry["node_ids"]) == set(GROUP)
    assert (repo / entry["copy"]).read_text() == (repo / entry["path"]).read_text()
    with pytest.raises(ValueError, match="build/"):
        workflow.list_handoffs(repo, record["id"], copy=Path("elsewhere"))


def test_open_dispute_parks_a_delivered_node_instead_of_reviewing_it(lean, monkeypatch):
    repo, _ = lean
    from homalg import disputes

    monkeypatch.setattr(disputes, "horizon", lambda *args: '{"id": "I-0001"}')
    disputes.open_dispute(repo, DEF_1, kind="proof", reason="printed typo", by="fixture-user")
    record = author_unit(repo)
    deliver(repo, record)
    finish(repo, record)
    state = states(repo)[DEF_1]
    assert state["state"] == "parked" and state["reason"] == "open dispute"


def test_failed_review_goes_back_to_authoring_and_twice_parks(lean):
    repo, _ = lean
    record = author_unit(repo)
    deliver(repo, record)
    finish(repo, record)
    structure = read_document(repo, KEY)["structure"]
    review = phases.review_units(repo, KEY, structure, frontier=StatementFrontier(repo, KEY))[0]
    review_record = {**review, "status": "done"}
    plan = {
        "task": review["id"],
        "narrowed": review_record,
        "retained": [],
        "released": {DEF_1: GROUP},
        "released_files": [],
        "failures": {DEF_1: [f"{DEF_1}: latest reviews must be satisfactory"]},
        "review_failed": {DEF_1: Path(review["metadata"]["homalg"]["handoffs"][0]["path"]).stem},
    }
    save_task(repo, review_record)
    path = repo / ".archon-horizon/tasks/items" / f"{review['id']}.yaml"
    current = parse_metadata(path.read_text())
    current["status"] = "done"
    path.write_text(dump_metadata(current))
    settlement.apply_settlement(repo, plan)
    assert states(repo)[DEF_1]["state"] == "needs_author"
    proposed = planning.statement_units(repo, KEY, structure, batch_size=4)
    assert any(DEF_1 in item["node_ids"] for item in proposed if "status" not in item)
    # A new delivery is reviewed again; a second failure parks the node.
    deliver(repo, record, out="build/handoff-2.json", author="writer-b")
    assert states(repo)[DEF_1]["state"] == "awaiting_review"
    current = parse_metadata(path.read_text())
    current["metadata"]["homalg"]["settlements"].append({"review_failed": {DEF_1: "other"}})
    path.write_text(dump_metadata(current))
    state = states(repo)[DEF_1]
    assert state["state"] == "parked" and state["reason"] == "repeated review failure"


def test_review_settlement_records_the_failed_delivery(lean, monkeypatch):
    repo, _ = lean
    record = author_unit(repo)
    deliver(repo, record)
    finish(repo, record)
    structure = read_document(repo, KEY)["structure"]
    edit_node(repo, "Def_2", lambda metadata: None)
    review = phases.review_units(repo, KEY, structure, frontier=StatementFrontier(repo, KEY))[0]
    info = review["metadata"]["homalg"]
    info["primary_nodes"] = [DEF_1, f"{KEY}.Def_2"]
    info["node_ids"] = [*GROUP, f"{KEY}.Def_2"]
    evaluation = {"complete": False, "failures": [f"{DEF_1}: latest reviews must be satisfactory"]}
    plan = settlement.plan_settlement(
        repo, review, evaluation, lambda narrowed: {"complete": True, "failures": []}
    )
    assert plan["applicable"]
    assert plan["review_failed"] == {DEF_1: Path(info["handoffs"][0]["path"]).stem}


def test_replan_cancels_pre_split_units_and_planning_recreates_author_units(lean, monkeypatch):
    repo, _ = lean
    legacy = unit(repo, "Def_1")
    legacy["metadata"]["homalg"].pop("phase")
    legacy["objective"] = planning.render_objective(
        repo, legacy, login="fixture-user", document=read_document(repo, KEY)
    )
    save_task(repo, legacy)
    import homalg.human

    monkeypatch.setattr(homalg.human, "require_idle", lambda repo: None)
    monkeypatch.setattr(
        stages,
        "evaluate",
        lambda repo, record, **kw: {
            "complete": False,
            "failures": ["lean-build: other document error"],
        },
    )
    planned = []
    monkeypatch.setattr(planning, "plan", lambda *args, **kw: planned.append(1) or {})
    data = settlement.settle_document(repo, KEY, replan=True, apply=True)
    actions = {item["task"]: item["action"] for item in data["actions"]}
    assert actions[legacy["id"]] == "replan"
    saved = parse_metadata(
        (repo / ".archon-horizon/tasks/items" / f"{legacy['id']}.yaml").read_text()
    )
    assert saved["status"] == "cancelled"
    assert saved["metadata"]["homalg"]["settlements"][-1]["released"] == {DEF_1: GROUP}
    assert planned == [1]
    structure = read_document(repo, KEY)["structure"]
    proposed = planning.statement_units(repo, KEY, structure, batch_size=4)
    assert any(
        DEF_1 in item["node_ids"] and item["metadata"]["homalg"]["phase"] == "author"
        for item in proposed
        if "status" not in item
    )


def test_planning_creates_review_units_without_holding_them(lean):
    repo, _ = lean
    planning.plan(repo, KEY, no_claim=True, statement_frontier=True, statement_batch_size=1)
    record = parse_metadata(
        (repo / f".archon-horizon/tasks/items/{KEY}.STMT.Unit_Def_1.yaml").read_text()
    )
    deliver(repo, record)
    finish(repo, record)
    result = planning.plan(repo, KEY, advance=True)
    created = [item for item in result["created_tasks"] if ".STMT.Review_" in item]
    assert len(created) == 1
    review = parse_metadata(
        (repo / ".archon-horizon/tasks/items" / f"{created[0]}.yaml").read_text()
    )
    assert review["metadata"]["homalg"]["phase"] == "review"
    assert not review["metadata"].get("dispatch_hold")
    again = planning.plan(repo, KEY, advance=True)
    assert not [item for item in again["created_tasks"] if ".STMT.Review_" in item]


def test_replanned_or_re_reviewed_nodes_get_a_new_unit_id(lean):
    repo, _ = lean
    planning.plan(repo, KEY, no_claim=True, statement_frontier=True, statement_batch_size=1)
    path = repo / f".archon-horizon/tasks/items/{KEY}.STMT.Unit_Def_1.yaml"
    record = parse_metadata(path.read_text())
    record["status"] = "cancelled"
    record["metadata"]["homalg"]["settlements"] = [
        {"replanned": True, "released": {DEF_1: GROUP}, "released_files": []}
    ]
    path.write_text(dump_metadata(record))
    result = planning.plan(repo, KEY, advance=True)
    assert f"{KEY}.STMT.Unit_Def_1_r2" in result["created_tasks"]
