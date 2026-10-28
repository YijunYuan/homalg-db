"""Ordinary independent evolution review is explicit, source-backed and content-bound."""

import json
from pathlib import Path

import pytest

from homalg.documents import dump_metadata
from homalg.evolution.bundle import build_bundle
from homalg.evolution.importer import import_output, review
from homalg.evolution.reviews import subject_hash, validate_review
from homalg.schemas import SchemaStore, load_yaml

ROOT = Path(__file__).resolve().parents[2]


def prepare(repo):
    index = json.loads((ROOT / "tools/tests/fixtures/good/index.json").read_text())
    bundle = build_bundle(index, "chain-complex", repo=repo)
    node = bundle["nodes"][0]
    output = {
        "concept": "chain-complex",
        "narrative_md": "A synthetic source summary.",
        "stages": [
            {
                "period": str(node["year"]),
                "doc": node["doc"],
                "nodes": [node["id"]],
                "change": "Defined a complex.",
            }
        ],
        "proposed_relations": [],
    }
    import_output(repo, output, bundle, model="synthetic-test")
    path = repo / "taxonomy/evolution/chain-complex.yaml"
    subject = load_yaml(path.read_text())["summaries"][0]
    report = repo / "docs/evolution-review.md"
    report.parent.mkdir()
    report.write_text(
        "Session: independent-review\nAuthor-session: original-author\n"
        "Subject: chain-complex:1\n"
        f"Subject-sha256: {subject_hash(subject)}\n"
        f"Bundle-sha256: {bundle['bundle_sha256']}\n"
        "Verdict: satisfactory\nAssertions-checked: yes\n"
        "Source-evidence: Fixture2000 synthetic source, Definition 1.\n"
    )
    options = {
        "concept": "chain-complex",
        "version": 1,
        "status": "accepted",
        "by": "review-agent",
        "session": "independent-review",
        "author_session": "original-author",
        "report": report,
    }
    return path, subject, report, options


def enable(repo):
    path = repo / "horizon/review-policy.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(dump_metadata({"schema_version": 1, "allow_independent_agent_reviews": True}))


def test_agent_review_requires_policy_independence_and_source_report(repo):
    path, _subject, report, options = prepare(repo)
    original = path.read_bytes()
    with pytest.raises(ValueError, match="disabled"):
        review(repo, **options)
    enable(repo)
    with pytest.raises(ValueError, match="distinct"):
        review(repo, **(options | {"author_session": "independent-review"}))
    report.write_text(
        report.read_text().replace("Assertions-checked: yes", "Assertions-checked: no")
    )
    with pytest.raises(ValueError, match="Assertions-checked"):
        review(repo, **options)
    assert path.read_bytes() == original


def test_review_is_bound_to_subject_and_public_report(repo):
    path, _subject, report, options = prepare(repo)
    enable(repo)
    result = review(repo, **options)
    record = result["review"]
    assert record["kind"] == "agent" and record["status"] == "accepted"
    assert record["session"] != record["author_session"]
    value = load_yaml(path.read_text())
    assert not SchemaStore(repo / "schema").validate(value, "evolution.schema.json")
    subject = value["summaries"][0]
    validate_review(subject, repo)
    subject["narrative_md"] += " Changed mathematical assertion."
    with pytest.raises(ValueError, match="stale"):
        validate_review(subject, repo)
    subject = value["summaries"][0] | {"narrative_md": "A synthetic source summary."}
    report.write_text(report.read_text() + "Changed evidence.\n")
    with pytest.raises(ValueError, match="report changed"):
        validate_review(subject, repo)
    # A new actual review can replace a stale verdict, with a fresh report digest.
    review(repo, **options)
    validate_review(load_yaml(path.read_text())["summaries"][0], repo)


def test_partial_agent_flags_and_private_report_are_rejected(repo):
    _path, _subject, report, options = prepare(repo)
    enable(repo)
    with pytest.raises(ValueError, match="requires"):
        review(repo, **(options | {"author_session": None}))
    private = repo / "build/review.md"
    private.parent.mkdir(exist_ok=True)
    private.write_bytes(report.read_bytes())
    with pytest.raises(ValueError, match="public authored"):
        review(repo, **(options | {"report": private}))


def test_relation_review_survives_alias_projection_and_can_be_repeated_after_edits(repo):
    from homalg.relations import load_relations, relation_id

    enable(repo)
    source, target = "Fixture2000.Aux_Old", "Fixture2001.Def_1"
    identifier = relation_id(source, "precursor_of", target)
    subject = {
        "id": identifier,
        "source": source,
        "type": "precursor_of",
        "target": target,
        "provenance": {"by": "formalizer", "on": "2001-01-01"},
        "review": {"status": "unreviewed"},
    }
    path = repo / "taxonomy/relations/Fixture2000.yaml"
    path.write_text(dump_metadata({"schema_version": 1, "relations": [subject]}))
    report = repo / "docs/relation-review.md"
    report.parent.mkdir()

    def write_report():
        report.write_text(
            "Session: independent-review\nAuthor-session: original-author\n"
            f"Subject: {identifier}\nSubject-sha256: {subject_hash(subject)}\n"
            "Verdict: satisfactory\nAssertions-checked: yes\n"
            "Source-evidence: Both synthetic fixture statements and their exact hypotheses.\n"
        )

    write_report()
    options = {
        "relation": identifier,
        "status": "accepted",
        "by": "review-agent",
        "session": "independent-review",
        "author_session": "original-author",
        "report": report,
    }
    review(repo, **options)
    (repo / "literature/Fixture2000/retired.yaml").write_text(
        dump_metadata(
            {
                "schema_version": 1,
                "retired": [
                    {
                        "id": source,
                        "kind": "moved",
                        "on": "2001-01-03",
                        "by": "fixture-reviewer",
                        "reason": "Synthetic relocation.",
                        "moved_to": "Fixture2000.Def_1",
                    }
                ],
            }
        )
    )
    projected = load_relations(repo, [], SchemaStore(repo / "schema"))[0]
    assert projected["source"] == "Fixture2000.Def_1"
    assert projected["id"] == identifier and projected["review"]["kind"] == "agent"
    subject["note"] = "New source evidence requires a fresh review."
    path.write_text(dump_metadata({"schema_version": 1, "relations": [subject]}))
    with pytest.raises(ValueError, match="stale"):
        load_relations(repo, [], SchemaStore(repo / "schema"))
    write_report()
    review(repo, **options)
    assert (
        load_relations(repo, [], SchemaStore(repo / "schema"))[0]["review"]["status"] == "accepted"
    )
