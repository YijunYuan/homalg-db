"""Fictional identities exercise real multi-cohort capture and registration gates."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import test_workflow as baseline
from click.testing import CliRunner
from test_prepare_batch_inputs import private_inputs

from homalg import review, review_cohorts, workflow
from homalg.cli import cli
from homalg.io import json_text
from homalg.nodeio import header_mapping, node_path, replace_header
from homalg.schemas import SchemaStore

author = baseline.author
NOW = datetime(2026, 11, 5, tzinfo=UTC)


def write_reports(repo: Path, cohorts: list[dict]) -> None:
    for cohort in cohorts:
        for identifier in cohort["node_ids"]:
            key, local = identifier.split(".")
            path = repo / "literature" / key / "reviews" / f"{local}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "## source-fidelity — fictional independent review\n"
                f"Session: {cohort['session']}\nAuthor-session: {cohort['author_session']}\n"
                "Status: satisfactory\nVerdict: Fixture source and statement agree.\n"
                "| Source | Lean |\n| --- | --- |\n| Fixture | Same statement |\n"
            )


@pytest.fixture
def cohorts(author):
    repo, record, commands = author
    groups = baseline.two_authors(repo, record)
    policy = repo / "horizon/review-policy.yaml"
    policy.parent.mkdir(exist_ok=True)
    policy.write_text("schema_version: 1\nallow_independent_agent_reviews: true\n")
    private_inputs(repo)
    handoff = Path("build/authors.json")
    workflow.prepare_batch(repo, record["id"], authors=groups, out=handoff)
    entries = [
        {
            "by": f"reviewer-{i}",
            "session": f"fictional-review-{i}",
            "author_session": group["author_session"],
            "node_ids": group["node_ids"],
        }
        for i, group in enumerate(groups)
    ]
    manifest = Path("build/cohorts.json")
    data = {"schema_version": 1, "kind": review_cohorts.MANIFEST_KIND, "cohorts": entries}
    (repo / manifest).write_text(json_text(data))
    write_reports(repo, entries)
    commands.clear()
    return repo, record, commands, handoff, manifest, data


def capture(fixture) -> dict:
    repo, _, _, handoff, manifest, _ = fixture
    return review_cohorts.snapshot(repo, handoff, manifest=manifest, out=Path("build/reviews.json"))


def sources(fixture) -> dict[Path, bytes]:
    repo, _, _, _, _, manifest = fixture
    return {
        node_path(repo, node): node_path(repo, node).read_bytes()
        for cohort in manifest["cohorts"]
        for node in cohort["node_ids"]
    }


def test_union_matches_serial_locks_and_builds_once_with_real_identities(cohorts):
    repo, _, commands, _, _, manifest = cohorts
    before = sources(cohorts)
    bundle = capture(cohorts)
    assert commands == []
    assert not bundle["approval"] and not bundle["task_complete"]
    assert "expected_author_session" not in bundle["inputs"]
    locks = review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert [command[1] for command in commands] == ["build", "exe"]
    for cohort in manifest["cohorts"]:
        for node in cohort["node_ids"]:
            assert {key: locks[node][key] for key in ("by", "session", "author_session")} == {
                key: cohort[key] for key in ("by", "session", "author_session")
            }
            assert (
                header_mapping(node_path(repo, node).read_text())["fidelity"]["reviewed"]
                == locks[node]
            )
    journal = json.loads(
        next((repo / ".archon-horizon/cache/fidelity-transactions").glob("*.json")).read_text()
    )
    assert journal["status"] == "committed"
    assert journal["evidence"]["cohorts"] == bundle["cohorts"]
    for path, data in before.items():
        path.write_bytes(data)
    serial = {}
    for cohort in manifest["cohorts"]:
        serial.update(
            review.review_fidelity_batch(
                repo,
                cohort["node_ids"],
                by=cohort["by"],
                session=cohort["session"],
                author_session=cohort["author_session"],
                now=NOW,
            )
        )
    assert serial == locks


def test_one_reviewer_may_review_distinct_actual_authors(cohorts):
    repo, _, _, _, manifest, data = cohorts
    for cohort in data["cohorts"]:
        cohort.update(by="one-reviewer", session="fictional-independent-reviewer")
    (repo / manifest).write_text(json_text(data))
    write_reports(repo, data["cohorts"])
    capture(cohorts)
    locks = review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert len({item["author_session"] for item in locks.values()}) == 2
    assert len({item["session"] for item in locks.values()}) == 1


@pytest.mark.parametrize(
    "invalid",
    [
        "duplicate",
        "unknown-field",
        "same-author",
        "bad-login",
        "wrong-author",
        "empty",
        "wrong-version",
        "non-string-id",
    ],
)
def test_manifest_identity_rejections_publish_nothing_before_build(cohorts, invalid):
    repo, _, commands, _, manifest, data = cohorts
    if invalid == "duplicate":
        data["cohorts"][1]["node_ids"] = data["cohorts"][0]["node_ids"]
    elif invalid == "unknown-field":
        data["cohorts"][0]["human"] = True
    elif invalid == "same-author":
        data["cohorts"][0]["session"] = data["cohorts"][0]["author_session"]
    elif invalid == "bad-login":
        data["cohorts"][0]["by"] = "reviewer_bad"
    elif invalid == "wrong-author":
        data["cohorts"][0]["author_session"] = "fabricated-author"
    elif invalid == "empty":
        data["cohorts"] = []
    elif invalid == "wrong-version":
        data["schema_version"] = True
    else:
        data["cohorts"][0]["node_ids"] = [123]
    (repo / manifest).write_text(json_text(data))
    with pytest.raises(ValueError):
        capture(cohorts)
    assert not commands and not (repo / "build/reviews.json").exists()


@pytest.mark.parametrize(
    "kind", ["human", "legacy-human", "dispute", "honesty", "report-author", "disabled-policy"]
)
def test_existing_protected_review_gates_remain_mandatory(cohorts, kind):
    repo, _, commands, _, _, data = cohorts
    identifier = data["cohorts"][1]["node_ids"][0]
    path = node_path(repo, identifier)
    source = path.read_text()
    metadata = header_mapping(source)
    if kind in {"human", "legacy-human"}:
        metadata["fidelity"]["reviewed"] = {
            "kind": "human",
            "by": "fictional-human",
            "on": "2026-11-01",
            "status": "satisfactory",
            "decl_hashes": {},
        }
        if kind == "legacy-human":
            metadata["fidelity"]["reviewed"].pop("kind")
        # Legacy envelope intentionally bypasses current schema for this guard regression.
        from homalg.documents import dump_metadata

        header = review.parse_header(source)
        start = source.index("```yaml node", header.start) + len("```yaml node")
        end = source.index("```", start)
        path.write_text(source[:start] + "\n" + dump_metadata(metadata) + source[end:])
    elif kind == "dispute":
        metadata["dispute"] = {
            "status": "open",
            "kind": "proof",
            "reason": "Fictional unresolved proof dispute",
            "on": "2026-11-01",
            "opened_by": "fixture",
        }
        path.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))
    elif kind == "disabled-policy":
        (repo / "horizon/review-policy.yaml").write_text(
            "schema_version: 1\nallow_independent_agent_reviews: false\n"
        )
    else:
        report = repo / "literature/Fixture2000/reviews/Lem_1.md"
        if kind == "honesty":
            report.write_text(
                report.read_text()
                + "\n## honesty — another actual reviewer\nSession: other-reviewer\n"
                "Author-session: fictional-author-b\nStatus: satisfactory\n"
                "Verdict: Different provenance.\n| A | B |\n"
            )
        else:
            report.write_text(report.read_text().replace("fictional-author-b", "fabricated-author"))
    before = {path: path.read_bytes() for path in sources(cohorts)}
    with pytest.raises(ValueError):
        capture(cohorts)
    assert not commands
    assert all(path.read_bytes() == value for path, value in before.items())


@pytest.mark.parametrize(
    "changed", ["source", "private", "report", "manifest", "handoff", "snapshot", "task"]
)
def test_frozen_bundle_rejects_staleness_before_export(cohorts, changed):
    repo, record, commands, handoff, manifest, _ = cohorts
    capture(cohorts)
    paths = {
        "source": repo / "HomAlg/Fixture2000/Thm_1.lean",
        "private": repo / "literature/.private/Fixture2000/tex/page-0003.tex",
        "report": repo / "literature/Fixture2000/reviews/Thm_1.md",
        "manifest": repo / manifest,
        "handoff": repo / handoff,
        "snapshot": repo / "build/reviews.json",
        "task": repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml",
    }
    path = paths[changed]
    if changed == "snapshot":
        data = json.loads(path.read_text())
        data["cohorts"][0]["author_session"] = "fabricated-author"
        path.write_text(json_text(data))
    elif changed == "task":
        from homalg.documents import dump_metadata

        record["objective"] = "Changed task contract"
        path.write_text(dump_metadata(record))
    else:
        path.write_text(path.read_text() + "\n")
    before = sources(cohorts)
    with pytest.raises(ValueError):
        review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert not commands
    assert all(path.read_bytes() == value for path, value in before.items())


def test_failure_during_second_write_rolls_back_union(cohorts, monkeypatch):
    repo, _, _, _, _, _ = cohorts
    capture(cohorts)
    before = sources(cohorts)
    write = review.atomic_write_with_receipt
    calls = 0

    def fail(path, text):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("Fictional write failure")
        return write(path, text)

    monkeypatch.setattr(review, "atomic_write_with_receipt", fail)
    with pytest.raises(ValueError, match="rolled-back"):
        review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert all(path.read_bytes() == value for path, value in before.items())


def test_manifest_change_during_writes_is_guarded_and_rolled_back(cohorts, monkeypatch):
    repo, _, _, _, manifest, _ = cohorts
    capture(cohorts)
    before = sources(cohorts)
    write = review.atomic_write_with_receipt
    calls = 0

    def change(path, text):
        nonlocal calls
        result = write(path, text)
        calls += 1
        if calls == 1:
            (repo / manifest).write_text((repo / manifest).read_text() + "\n")
        return result

    monkeypatch.setattr(review, "atomic_write_with_receipt", change)
    with pytest.raises(ValueError, match="rolled-back"):
        review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert all(path.read_bytes() == value for path, value in before.items())


def test_agent_only_cohort_cli_has_no_identity_override(cohorts):
    repo, _, commands, handoff, manifest, _ = cohorts
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "workflow",
            "review-snapshot-cohorts",
            str(repo / handoff),
            "--repo",
            str(repo),
            "--cohorts",
            str(repo / manifest),
            "--out",
            "build/reviews.json",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(
        cli,
        [
            "review-fidelity-cohorts",
            "--repo",
            str(repo),
            "--snapshot",
            str(repo / "build/reviews.json"),
            "--human",
            "--json",
        ],
    )
    assert result.exit_code == 2 and not commands
    result = runner.invoke(
        cli,
        [
            "review-fidelity-cohorts",
            "--repo",
            str(repo),
            "--snapshot",
            str(repo / "build/reviews.json"),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert len(json.loads(result.output)["data"]["locks"]) == 2


def test_generated_export_change_during_post_export_checks_is_rejected(cohorts, monkeypatch):
    repo, _, _, _, _, _ = cohorts
    capture(cohorts)
    before = sources(cohorts)
    check = review._assert_snapshot
    changed = False

    def alter_export(*args, **kwargs):
        nonlocal changed
        result = check(*args, **kwargs)
        if not changed:
            changed = True
            path = repo / "literature/Fixture2000/nodes.json"
            path.write_text(path.read_text() + "\n")
        return result

    monkeypatch.setattr(review, "_assert_snapshot", alter_export)
    with pytest.raises(ValueError, match="Compiled export changed"):
        review_cohorts.register(repo, Path("build/reviews.json"), now=NOW)
    assert all(path.read_bytes() == value for path, value in before.items())
