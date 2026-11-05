"""Native statement units use actual local prerequisites, never chapter completion fiction."""

import copy
import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner
from test_engine_integration import fake_engine

from homalg import planning, stages, workflow
from homalg.cli import cli
from homalg.documents import dump_metadata, read_document
from homalg.headers import parse_header
from homalg.nodeio import header_mapping, replace_header
from homalg.repository import node_paths
from homalg.schemas import SchemaStore, load_yaml
from homalg.statement_frontier import StatementFrontier, unit_blockers

ROOT = Path(__file__).resolve().parents[2]
KEY = "Fixture2000"


@pytest.fixture
def frontier_repo(repo, monkeypatch):
    shutil.copytree(ROOT / "horizon", repo / "horizon")
    monkeypatch.setattr(planning, "horizon", fake_engine)
    pages = {}
    for path in node_paths(repo, [KEY]):
        node = parse_header(path.read_text()).metadata
        if "aux" in node:
            continue
        for number in node["source"]["pages"]:
            entry = pages.setdefault(f"{number:04}", {"complete": True, "items": []})
            entry["items"].append(
                {
                    "node": node["id"],
                    "label": node["source"]["label"],
                    "disposition": "informal" if "informal" in node else "node",
                }
            )
    (repo / "literature" / KEY / "inventory.yaml").write_text(
        dump_metadata(
            {
                "schema_version": 1,
                "doc_key": KEY,
                "pages": pages,
            }
        )
    )
    return repo


def edit_node(repo, local, update):
    path = repo / "HomAlg" / KEY / f"{local}.lean"
    source = path.read_text()
    metadata = header_mapping(source)
    update(metadata)
    path.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))


def units(repo):
    return planning.statement_units(repo, KEY, read_document(repo, KEY)["structure"])


def unit(repo, local="Def_1"):
    return next(item for item in units(repo) if item["id"] == f"{KEY}.STMT.Unit_{local}")


def save_task(repo, record):
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = copy.deepcopy(record)
    record.pop("blockers", None)
    record["status"] = "queued"
    path.write_text(dump_metadata(record))
    return path


def test_opt_in_units_start_before_whole_chapter_dag_and_keep_aggregate_gates(frontier_repo):
    repo = frontier_repo
    initial = planning.plan(repo, KEY, no_claim=True)
    assert all(".Unit_" not in identifier for identifier in initial["created_tasks"])
    result = planning.plan(
        repo, KEY, advance=True, statement_frontier=True, proofs="deferred", statement_batch_size=1
    )
    assert f"{KEY}.STMT.Unit_Def_1" in result["created_tasks"]
    dag = load_yaml((repo / f".archon-horizon/tasks/items/{KEY}.DAG.1.yaml").read_text())
    assert dag["status"] == "queued"
    assert f"{KEY}.STMT.1" not in result["created_tasks"]
    record = load_yaml(
        (repo / f".archon-horizon/tasks/items/{KEY}.STMT.Unit_Def_1.yaml").read_text()
    )
    assert record["metadata"]["homalg"]["node_ids"] == [
        f"{KEY}.Def_1",
        f"{KEY}.Bridge_Def_1_mathlib",
    ]
    assert record["write_set"]["files"] == [
        f"HomAlg/{KEY}/Bridge_Def_1_mathlib.lean",
        f"HomAlg/{KEY}/Def_1.lean",
        f"literature/{KEY}/reviews/Bridge_Def_1_mathlib.md",
        f"literature/{KEY}/reviews/Def_1.md",
    ]
    assert "outer-session acceptance" in record["objective"]
    again = planning.plan(repo, KEY, advance=True)
    assert again["statement_frontier"] and again["proofs"] == "deferred"
    assert all(".Unit_" not in identifier for identifier in again["created_tasks"])
    coarse = load_yaml((repo / f".archon-horizon/tasks/items/{KEY}.STMT.1.yaml").read_text())
    assert "aggregate acceptance" in coarse["metadata"]["dispatch_hold"]
    assert coarse["status"] == "queued"


def test_unrelated_unreviewed_page_does_not_block_ready_definition(frontier_repo):
    frontier = StatementFrontier(frontier_repo, KEY)
    frontier.document["type"] = "book"
    frontier.pages = {"0001": {"status": "reviewed"}, "0002": {"status": "unreadable"}}
    assert frontier.blockers([f"{KEY}.Def_1"]) == []
    assert any("0002 is not reviewed" in error for error in frontier.blockers([f"{KEY}.Lem_1"]))


@pytest.mark.parametrize("missing", ["inventory", "occurrence", "statement", "foundation"])
def test_missing_local_evidence_prevents_dispatch(frontier_repo, missing):
    frontier = StatementFrontier(frontier_repo, KEY)
    if missing == "inventory":
        frontier.inventory["pages"]["0001"]["complete"] = False
    elif missing == "occurrence":
        frontier.inventory["pages"]["0001"]["items"] = []
    elif missing == "statement":
        frontier.headers[f"{KEY}.Def_1"].sections["Statement"] = "TODO: fill from source"
    else:
        frontier.document["foundations"][0]["status"] = "proposed"
    assert frontier.blockers([f"{KEY}.Def_1"])


def test_statement_dependencies_need_current_reviewed_compiled_interfaces(
    frontier_repo, monkeypatch
):
    frontier = StatementFrontier(frontier_repo, KEY)
    identifier = f"{KEY}.Def_1"
    frontier.headers[identifier].metadata["deps"]["statement"] = [f"{KEY}.Def_2"]
    review = frontier_repo / "literature" / KEY / "reviews/Def_2.md"
    review.parent.mkdir(exist_ok=True)
    review.write_text("## source-fidelity — fictional fixture\nStatus: satisfactory\n")
    accepted = {
        "authored": {"decls": ["Real.Data"], "fidelity": {"reviewed": {"by": "fictional"}}},
        "approx": False,
        "derived": {"local_status": "proved"},
        "global": {"reopened": False, "headline": "proof-complete"},
    }
    monkeypatch.setattr(frontier, "state", lambda _identifier: accepted)
    assert frontier.blockers([identifier]) == []
    review.write_text("## source-fidelity — fictional fixture\nStatus: major-issues\n")
    assert frontier.blockers([identifier])
    review.write_text("## source-fidelity — fictional fixture\nStatus: satisfactory\n")
    for field in ("approx", "reopened", "decls", "reviewed"):
        changed = copy.deepcopy(accepted)
        if field == "approx":
            changed["approx"] = True
        elif field == "reopened":
            changed["global"][field] = True
        else:
            (changed["authored"] if field == "decls" else changed["authored"]["fidelity"])[
                field
            ] = []
        monkeypatch.setattr(frontier, "state", lambda _identifier, value=changed: value)
        assert any("statement interface" in error for error in frontier.blockers([identifier]))


def test_proof_only_dependencies_do_not_block_statements_but_early_review_does(frontier_repo):
    frontier = StatementFrontier(frontier_repo, KEY)
    identifier = f"{KEY}.Lem_1"
    node = frontier.headers[identifier].metadata
    node["deps"] = {"statement": [], "proof": [f"{KEY}.Def_1", "Missing2000.Thm_1"]}
    assert any("early review" in error for error in frontier.blockers([identifier]))
    frontier.document["early_review"] = {"by": "fictional-reviewer", "on": "2026-01-01"}
    assert frontier.blockers([identifier]) == []
    frontier.headers[identifier].sections["Proof"] = "TODO"
    assert any("Proof text" in error for error in frontier.blockers([identifier]))


def test_actual_undeclared_local_import_and_cycles_are_not_assumed_independent(frontier_repo):
    frontier = StatementFrontier(frontier_repo, KEY)
    identifier = f"{KEY}.Def_1"
    frontier.sources[identifier] = (
        "import HomAlg.Fixture2000.Def_2\n" + frontier.sources[identifier]
    )
    assert any("statement interface" in error for error in frontier.blockers([identifier]))
    frontier.sources[identifier] = ""
    frontier.headers[identifier].metadata["deps"]["statement"] = [identifier]
    assert any("cyclic" in error for error in frontier.blockers([identifier]))
    frontier.headers[identifier].metadata["deps"]["statement"] = ["malformed-dependency"]
    assert any("statement interface" in error for error in frontier.blockers([identifier]))


def test_scoped_selection_rejects_missing_foreign_and_auxiliary_nodes(frontier_repo):
    chapters = read_document(frontier_repo, KEY)["structure"]
    for identifier in ("Fixture2001.Def_1", f"{KEY}.Missing", f"{KEY}.Aux_Thm_1_step"):
        with pytest.raises(ValueError):
            planning.statement_units(frontier_repo, KEY, chapters, (identifier,))
    assert len(planning.statement_units(frontier_repo, KEY, chapters, (f"{KEY}.Def_1",))) == 1


def test_existing_unit_is_held_after_input_change_and_recovers_without_status_edit(frontier_repo):
    repo = frontier_repo
    planning.plan(repo, KEY, no_claim=True, statement_frontier=True, statement_batch_size=1)
    path = repo / f".archon-horizon/tasks/items/{KEY}.STMT.Unit_Def_1.yaml"
    source = repo / f"HomAlg/{KEY}/Def_1.lean"
    before = source.read_text()
    source.write_text(before.replace("## Statement\n", "## Statement\n\nTODO\n"))
    planning.plan(repo, KEY, advance=True)
    held = load_yaml(path.read_text())
    assert "Statement text" in held["metadata"]["dispatch_hold"]
    assert held["status"] == "queued"
    source.write_text(before)
    planning.plan(repo, KEY, advance=True)
    ready = load_yaml(path.read_text())
    assert "dispatch_hold" not in ready["metadata"] and ready["status"] == "queued"


def test_coarse_tasks_are_aggregation_only_without_accepting_them(frontier_repo, monkeypatch):
    repo = frontier_repo
    record = planning.proposed_task(repo, KEY, "STMT", 1, chapter="1", kind_group="definitions")
    path = save_task(repo, record)
    monkeypatch.setattr(planning, "evaluate", lambda *args, **kwargs: {"complete": False})
    planning.reconcile_frontier_holds(repo, KEY, read_document(repo, KEY)["structure"], True)
    held = load_yaml(path.read_text())
    assert "aggregate acceptance" in held["metadata"]["dispatch_hold"]
    assert held["status"] == "queued" and held["write_set"] == record["write_set"]
    monkeypatch.setattr(planning, "evaluate", lambda *args, **kwargs: {"complete": True})
    planning.reconcile_frontier_holds(repo, KEY, read_document(repo, KEY)["structure"], True)
    ready = load_yaml(path.read_text())
    assert "dispatch_hold" not in ready["metadata"] and ready["status"] == "queued"


def test_unit_stage_check_preserves_full_review_and_compiled_requirements(frontier_repo):
    record = unit(frontier_repo)
    assert not unit_blockers(frontier_repo, record)
    evaluation = stages.evaluate(frontier_repo, record, refresh_exports=False)
    assert not evaluation["complete"]
    assert any(
        "fresh main declarations" in failure or "current satisfactory statement lock" in failure
        for failure in evaluation["failures"]
    )
    record["write_set"]["files"].append(f"HomAlg/{KEY}/Def_2.lean")
    assert unit_blockers(frontier_repo, record) == [
        "Statement unit node_ids and immutable Lean scope disagree"
    ]


def test_next_reports_unready_units_and_is_read_only(frontier_repo):
    repo = frontier_repo
    planning.plan(repo, KEY, no_claim=True, statement_frontier=True, statement_batch_size=1)
    before = {path: path.read_bytes() for path in (repo / ".archon-horizon").rglob("*.yaml")}
    data = workflow.next_tasks(repo, KEY)
    assert any(item["task"] == f"{KEY}.STMT.Unit_Def_1" for item in data["ready"])
    assert any(
        item["task"] == f"{KEY}.STMT.Unit_Lem_1" and item.get("blockers") for item in data["held"]
    )
    assert all(path.read_bytes() == content for path, content in before.items())


def test_cli_persists_explicit_statement_frontier(frontier_repo):
    result = CliRunner().invoke(
        cli,
        [
            "plan",
            KEY,
            "--repo",
            str(frontier_repo),
            "--no-claim",
            "--statement-frontier",
            "--statement-node",
            f"{KEY}.Def_1",
            "--proofs",
            "deferred",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    overlay = json.loads((frontier_repo / f".archon-horizon/overlay/plan-{KEY}.json").read_text())
    assert overlay["statement_frontier"] and overlay["statement_nodes"] == [f"{KEY}.Def_1"]


def test_disabling_frontier_holds_units_and_releases_aggregate_dispatch(frontier_repo):
    repo = frontier_repo
    planning.plan(repo, KEY, no_claim=True, statement_nodes=(f"{KEY}.Def_1",))
    result = planning.plan(repo, KEY, advance=True, statement_frontier=False)
    assert not result["statement_frontier"] and not result["statement_nodes"]
    record = load_yaml(
        (repo / f".archon-horizon/tasks/items/{KEY}.STMT.Unit_Def_1.yaml").read_text()
    )
    assert "outside the enabled frontier" in record["metadata"]["dispatch_hold"]


def test_default_native_batch_is_disjoint_and_preserves_registered_scope(frontier_repo):
    repo = frontier_repo
    result = planning.plan(repo, KEY, no_claim=True, statement_frontier=True)
    assert result["statement_batch_size"] == 4
    identifier = next(value for value in result["created_tasks"] if ".STMT.UnitBatch_" in value)
    path = repo / ".archon-horizon/tasks/items" / f"{identifier}.yaml"
    record = load_yaml(path.read_text())
    info = record["metadata"]["homalg"]
    assert {group["primary"] for group in info["author_groups"]} >= {
        f"{KEY}.Def_1",
        f"{KEY}.Def_2",
    }
    assert len(info["author_groups"]) <= 4
    all_nodes = [node for group in info["author_groups"] for node in group["node_ids"]]
    assert len(all_nodes) == len(set(all_nodes))
    assert "Dispatch these independent groups concurrently" in record["objective"]
    assert record["metadata"]["roadmap_status_sync"] is False
    record["status"] = "blocked"
    path.write_text(dump_metadata(record))
    again = planning.plan(repo, KEY, advance=True, statement_batch_size=1)
    assert all(".STMT.Unit_" not in value for value in again["created_tasks"])
    preserved = load_yaml(path.read_text())
    assert preserved["status"] == "blocked"
    assert preserved["write_set"] == record["write_set"]
    assert preserved["metadata"]["homalg"]["node_ids"] == info["node_ids"]


def test_batching_never_parallelizes_connected_statement_interfaces(frontier_repo, monkeypatch):
    frontier = StatementFrontier(frontier_repo, KEY)
    # Even if both are otherwise ready against an accepted baseline, rewriting
    # a dependency and its consumer is not an independent author batch.
    monkeypatch.setattr(frontier, "blockers", lambda identifiers: [])
    result = planning.statement_units(
        frontier_repo,
        KEY,
        read_document(frontier_repo, KEY)["structure"],
        (f"{KEY}.Def_1", f"{KEY}.Def_3"),
        frontier=frontier,
        batch_size=4,
    )
    assert len(result) == 2
    assert all("UnitBatch" not in candidate["id"] for candidate in result)


def test_pending_finalization_is_not_recommended_as_ready(frontier_repo):
    repo = frontier_repo
    planning.plan(repo, KEY, no_claim=True, statement_nodes=(f"{KEY}.Def_2",))
    path = repo / f".archon-horizon/tasks/items/{KEY}.STMT.Unit_Def_2.yaml"
    record = load_yaml(path.read_text())
    record["metadata"]["finalization_hold"] = "incomplete outer acceptance"
    path.write_text(dump_metadata(record))
    result = workflow.next_tasks(repo, KEY)
    assert all(item["task"] != record["id"] for item in result["ready"])
    assert any(item["task"] == record["id"] for item in result["held"])


def test_accepted_prior_content_creates_no_redundant_units_and_preserves_existing(
    frontier_repo, monkeypatch
):
    repo = frontier_repo
    registered = unit(repo, "Def_2")
    path = save_task(repo, registered)
    accepted = {
        "authored": {"decls": ["Fictional.current"], "fidelity": {"reviewed": {"by": "fictional"}}},
        "approx": False,
        "derived": {"local_status": "proved"},
        "global": {"reopened": False, "headline": "proof-complete"},
    }
    monkeypatch.setattr(StatementFrontier, "state", lambda self, identifier: accepted)
    directory = repo / "literature" / KEY / "reviews"
    directory.mkdir(exist_ok=True)
    for source in node_paths(repo, [KEY]):
        metadata = parse_header(source.read_text()).metadata
        if not metadata["decls"] and "informal" not in metadata:
            # This test replaces the compiled-state boundary with the fictional
            # accepted record above; authored declarations must agree with it.
            edit_node(repo, source.stem, lambda node: node.update(decls=["Fictional.current"]))
        (directory / f"{source.stem}.md").write_text(
            "## source-fidelity — fictional accepted baseline\nStatus: satisfactory\n"
        )
    original = load_yaml(path.read_text())
    result = planning.plan(repo, KEY, no_claim=True, statement_frontier=True)
    assert all(".STMT.Unit" not in identifier for identifier in result["created_tasks"])
    next_work = workflow.next_tasks(repo, KEY)
    assert all(".STMT.Unit" not in item["task"] for item in next_work["requires_plan"])
    preserved = load_yaml(path.read_text())
    assert preserved["status"] == original["status"]
    assert preserved["write_set"] == original["write_set"]
    # One unreviewed helper keeps its parent group eligible for actual work.
    (directory / "Bridge_Def_1_mathlib.md").unlink()
    fresh = planning.statement_units(repo, KEY, read_document(repo, KEY)["structure"], batch_size=4)
    assert any(f"{KEY}.Def_1" in candidate["node_ids"] for candidate in fresh)


def test_settled_source_error_is_skipped_but_never_used_as_an_interface(frontier_repo, monkeypatch):
    frontier = StatementFrontier(frontier_repo, KEY)
    error = {
        "authored": {
            "decls": ["Fictional.false_claim"],
            "dispute": {
                "status": "open",
                "confirmed_by": "fictional-human",
            },
        },
        "approx": False,
        "derived": {"local_status": "stated"},
        "global": {"reopened": False, "headline": "error"},
    }
    monkeypatch.setattr(frontier, "state", lambda identifier: error)
    assert frontier.settled_statement(f"{KEY}.Thm_4")
    assert not frontier.accepted_interface(f"{KEY}.Thm_4")
    error["approx"] = True
    assert not frontier.settled_statement(f"{KEY}.Thm_4")
