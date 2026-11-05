"""Independent adversarial checks for shared preflights; fixture identities only."""

import json
from pathlib import Path

import pytest
import test_workflow as baseline

from homalg import workflow
from homalg.documents import dump_metadata
from homalg.nodeio import header_mapping, replace_header
from homalg.schemas import SchemaStore

author = baseline.author
two_authors = baseline.two_authors


def test_batch_contract_change_after_validation_publishes_nothing(author, monkeypatch):
    repo, record, _ = author
    groups = two_authors(repo, record)
    validate = workflow.validate_repo

    def change_contract(*args, **kwargs):
        result = validate(*args, **kwargs)
        record["objective"] = "Changed task while its preflight was running"
        path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
        path.write_text(dump_metadata(record))
        return result

    monkeypatch.setattr(workflow, "validate_repo", change_contract)
    with pytest.raises(ValueError, match="task scope changed"):
        workflow.prepare_batch(
            repo, record["id"], authors=groups, out=Path("build/contract-race.json")
        )
    assert not (repo / "build/contract-race.json").exists()


def test_batch_final_union_rechecks_first_authors_private_source(author, monkeypatch):
    repo, record, _ = author
    groups = two_authors(repo, record)
    # Only the first author's proof dependency reads this page. The second
    # author's later verification must not substitute for rechecking the union.
    path = repo / "HomAlg/Fixture2000/Lem_2.lean"
    source = path.read_text()
    header = header_mapping(source)
    header["source"]["pages"] = [3]
    path.write_text(replace_header(source, header, SchemaStore(repo / "schema")))
    private_page = repo / "literature/.private/Fixture2000/tex/page-0003.tex"
    private_page.parent.mkdir(parents=True, exist_ok=True)
    private_page.write_text("Original fictional page\n")
    select = workflow._nodes
    calls = 0

    def change_earlier_context(*args, **kwargs):
        nonlocal calls
        calls += 1
        result = select(*args, **kwargs)
        if calls == 3:
            private_page.write_text("Concurrent change after first author was rechecked\n")
        return result

    monkeypatch.setattr(workflow, "_nodes", change_earlier_context)
    with pytest.raises(ValueError, match="Batch author inputs changed"):
        workflow.prepare_batch(
            repo, record["id"], authors=groups, out=Path("build/context-race.json")
        )
    assert calls == 4
    assert not (repo / "build/context-race.json").exists()


def test_batch_new_invocation_rebuilds_and_old_bundle_stays_stale(author):
    repo, record, calls = author
    groups = two_authors(repo, record)
    workflow.prepare_batch(repo, record["id"], authors=groups, out=Path("build/first.json"))
    path = repo / "HomAlg/Fixture2000/Lem_1.lean"
    path.write_text(path.read_text() + "\n-- Changed author's explanatory comment.\n")
    # Each delivery binds only its own closure: the unchanged author stays valid.
    workflow.verify(repo, Path("build/first.json"), author_session=groups[0]["author_session"])
    with pytest.raises(ValueError, match="stale"):
        workflow.verify(repo, Path("build/first.json"), author_session=groups[1]["author_session"])
    current = workflow.prepare_batch(
        repo, record["id"], authors=groups, out=Path("build/second.json")
    )
    assert current["ready_for_review"]
    assert [command[1] for command in calls] == ["build", "exe", "build", "exe"]
    assert (
        workflow.verify(
            repo, Path("build/second.json"), author_session=groups[1]["author_session"]
        )["node_ids"]
        == groups[1]["node_ids"]
    )


def test_batch_snapshot_requires_author_and_binds_exact_selected_delivery(author):
    repo, record, calls = author
    groups = two_authors(repo, record)
    workflow.prepare_batch(repo, record["id"], authors=groups, out=Path("build/authors.json"))
    with pytest.raises(ValueError, match="Select the actual author"):
        workflow.review_snapshot(repo, Path("build/authors.json"), out=Path("build/no-author.json"))
    assert not (repo / "build/no-author.json").exists()
    report = repo / "literature/Fixture2000/reviews/Lem_1.md"
    report.parent.mkdir(exist_ok=True)
    report.write_text("Fictional independent report to bind; no registration claimed.\n")
    snapshot = workflow.review_snapshot(
        repo,
        Path("build/authors.json"),
        author_session=groups[1]["author_session"],
        out=Path("build/selected-author.json"),
    )
    assert snapshot["node_ids"] == groups[1]["node_ids"]
    assert snapshot["expected_author_session"] == groups[1]["author_session"]
    assert json.loads((repo / "build/selected-author.json").read_text()) == snapshot
    assert len(calls) == 2
