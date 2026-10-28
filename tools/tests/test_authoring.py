"""Authoring commands preserve source prose and guarded review evidence."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from homalg.cli import cli
from homalg.disputes import open_dispute, resolve_dispute
from homalg.documents import dump_metadata, read_document
from homalg.foundations import confirm, draft
from homalg.headers import parse_header
from homalg.human import HumanApprovalRequired
from homalg.maintenance import prune_check
from homalg.review import review_fidelity
from homalg.scaffold import new_node
from homalg.schemas import SchemaStore, load_yaml
from homalg.taxonomy import find, merge


def make_node(repo: Path, node_id: str = "Fixture2000.Thm_20", **extra: object) -> Path:
    """Create a source-coordinate-complete synthetic scaffold."""
    return new_node(
        repo,
        node_id,
        kind="theorem",
        label="Theorem 20",
        pages=[3],
        tags=["basic"],
        chapter="1",
        section="1.1",
        **extra,
    )


def test_chapter_only_document_omits_section(repo: Path) -> None:
    """Articles whose sections are represented as chapters need no invented subsection."""
    document_path = repo / "literature/Fixture2000/document.yaml"
    document = load_yaml(document_path.read_text())
    del document["structure"][0]["sections"]
    document_path.write_text(dump_metadata(document))
    options = dict(kind="definition", label="Definition 20", pages=[3], tags=["basic"], chapter="1")
    path = new_node(repo, "Fixture2000.Def_20", **options)
    assert "section" not in parse_header(path.read_text()).metadata["source"]
    with pytest.raises(ValueError, match="has no sections"):
        new_node(repo, "Fixture2000.Def_21", section="invented", **options)


def test_scaffold_identity_and_auxiliary_constraints(repo: Path) -> None:
    """No overwrite, silent case collision, missing auxiliary parent or unknown vocabulary."""
    path = make_node(repo)
    header = parse_header(path.read_text())
    assert header.metadata["decls"] == []
    assert "TODO:" in header.sections["Statement"]
    assert "TODO:" in header.sections["Proof"]
    assert "namespace" not in path.read_text()
    with pytest.raises(FileExistsError):
        make_node(repo)
    with pytest.raises((FileExistsError, ValueError)):
        make_node(repo, "Fixture2000.thm_20")
    with pytest.raises(ValueError, match="require exactly"):
        make_node(repo, "Fixture2000.Aux_Thm_1_new")
    with pytest.raises(ValueError, match="same document"):
        make_node(
            repo,
            "Fixture2000.Aux_Thm_1_new",
            parent="Fixture2001.Def_1",
            aux_kind="lemma",
            reason="A helper",
        )


def test_cited_defaults_are_unique_and_schema_valid(repo: Path) -> None:
    """Repeated unnumbered citations receive stable distinct labels and source pages."""
    paths = [
        new_node(
            repo,
            f"Fixture2000.Cited_New{number}",
            kind="theorem",
            tags=["basic"],
            chapter="1",
            section="1.1",
            cited_kind="folklore",
            used_at=[3],
        )
        for number in (1, 2)
    ]
    headers = [parse_header(path.read_text()).metadata for path in paths]
    assert headers[0]["source"]["label"] != headers[1]["source"]["label"]
    assert all(header["source"]["pages"] == [3] for header in headers)
    assert all(
        not SchemaStore(repo / "schema").validate(header, "node-header.strict.schema.json")
        for header in headers
    )


def test_foundation_draft_preserves_evidence_and_confirm_is_guarded(repo: Path) -> None:
    """Existing synthetic approvals are not replaced by a new template draft."""
    path = repo / "literature/Fixture2000/document.yaml"
    before = path.read_bytes()
    assert draft(repo, "Fixture2000") == read_document(repo, "Fixture2000")["foundations"]
    assert path.read_bytes() == before
    data = read_document(repo, "Fixture2000")
    data["foundations"] = []
    path.write_text(dump_metadata(data))
    assert len(draft(repo, "Fixture2000")) == 6
    with pytest.raises(ValueError, match="proposed"):
        confirm(repo, "Fixture2000", 1, by="reviewer")
    data = read_document(repo, "Fixture2000")
    data["foundations"][0].update(status="proposed", evidence="Synthetic source p. 1")
    path.write_text(dump_metadata(data))
    before = path.read_bytes()
    with pytest.raises(HumanApprovalRequired):
        confirm(repo, "Fixture2000", 1, by="reviewer")
    assert path.read_bytes() == before


def test_dispute_lifecycle_preserves_docstring_and_history(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Opening a report marks only the primary declaration; withdrawal retains a resolved record."""
    monkeypatch.setattr("homalg.disputes._inbox", lambda *args: "I-0042")
    path = repo / "HomAlg/Fixture2000/Thm_1.lean"
    before = parse_header(path.read_text()).sections
    opened = open_dispute(repo, "Fixture2000.Thm_1", kind="proof", reason="Synthetic gap")
    assert opened["inbox"] == "I-0042"
    assert path.read_text().count("PROOF-DISPUTED:") == 1
    assert parse_header(path.read_text()).sections == before
    with pytest.raises(ValueError, match="already has"):
        open_dispute(repo, "Fixture2000.Thm_1", kind="proof", reason="Duplicate")
    monkeypatch.setattr("homalg.disputes.require_human", lambda *args, **kwargs: None)
    resolve_dispute(
        repo,
        "Fixture2000.Thm_1",
        via="withdrawn",
        by="fixture-reviewer",
        note="Fictional regression",
    )
    assert "PROOF-DISPUTED:" not in path.read_text()
    resolved = parse_header(path.read_text()).metadata["dispute"]
    open_dispute(repo, "Fixture2000.Thm_1", kind="statement", reason="Another synthetic concern")
    assert parse_header(path.read_text()).metadata["dispute_history"] == [resolved]
    assert path.read_text().count("STATEMENT-DISPUTED:") == 1


def test_latest_honesty_review_blocks_lock_even_without_structure(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An existing failed honesty review is binding even for an ordinary theorem."""
    reviews = repo / "literature/Fixture2000/reviews/Thm_1.md"
    reviews.parent.mkdir()
    reviews.write_text(
        "## source-fidelity — 2026-10-28 — writer\nStatus: satisfactory\nVerdict: matches\n"
        "| source | Lean |\n|---|---|\n| S | S |\n"
        "## honesty — 2026-10-28 — reviewer\nStatus: mismatch\nVerdict: circular\n"
    )
    with pytest.raises(ValueError, match="honesty"):
        review_fidelity(repo, "Fixture2000.Thm_1", by="fixture-user", session="writer")


def test_dispute_inbox_has_supported_scope_authorship_and_body(repo: Path, monkeypatch) -> None:
    """The real fork requires a title and description, and an explicit project root."""
    from homalg.disputes import _inbox

    def invoke(root: Path, *args: str) -> str:
        assert root == repo
        assert args[:2] == ("inbox", "add")
        assert args[args.index("--author") + 1] == "homalg"
        assert args[args.index("--to") + 1] == "human"
        assert args[args.index("--node") + 1] == "Fixture2000.Thm_1"
        title, description = args[args.index("--body") + 1].split("\n\n", 1)
        assert "statement dispute" in title and description == "Concrete source mismatch"
        return "Created I-0042\n"

    monkeypatch.setattr("homalg.disputes.horizon", invoke)
    assert _inbox(repo, "Fixture2000.Thm_1", "statement", "Concrete source mismatch") == "I-0042"


def test_review_lock_requires_fresh_export_and_locks_all_main_declarations(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid synthetic review locks each current declaration without touching the prose."""
    reviews = repo / "literature/Fixture2000/reviews/Thm_1.md"
    reviews.parent.mkdir()
    reviews.write_text(
        "## source-fidelity — 2026-10-28 — reviewer\nStatus: satisfactory\n"
        "Verdict: synthetic source matches\n| source | Lean |\n|---|---|\n| S | S |\n"
    )
    calls = []
    monkeypatch.setattr(
        "homalg.leanexport.export_lean", lambda *args, **kwargs: calls.append(kwargs)
    )
    path = repo / "HomAlg/Fixture2000/Thm_1.lean"
    before = parse_header(path.read_text())
    lock = review_fidelity(
        repo,
        "Fixture2000.Thm_1",
        by="fixture-user",
        session="writer",
        now=datetime(2026, 10, 28, tzinfo=UTC),
    )
    after = parse_header(path.read_text())
    assert calls == [{"doc": "Fixture2000"}]
    assert set(lock["decl_hashes"]) == set(before.metadata["decls"])
    assert lock["kind"] == "agent"
    assert after.sections == before.sections


def test_taxonomy_rename_rewrites_headers_but_retains_old_id(repo: Path) -> None:
    """A rename preserves a resolvable tombstone and source prose."""
    path = repo / "HomAlg/Fixture2000/Def_1.lean"
    before = parse_header(path.read_text()).sections
    assert find(repo, "CHAIN COMPLEX")
    changed = merge(repo, "basic", "elementary", rename=True)
    assert "taxonomy/tags.yaml" in changed
    tags = {
        item["id"]: item for item in load_yaml((repo / "taxonomy/tags.yaml").read_text())["tags"]
    }
    assert tags["basic"]["merged_into"] == "elementary"
    assert "elementary" in parse_header(path.read_text()).metadata["tags"]
    assert parse_header(path.read_text()).sections == before


def test_pruning_referenced_leaf_is_refused(repo: Path) -> None:
    """Source dependencies keep auxiliary ids alive even before a Lean proof uses them."""
    from homalg.nodeio import header_mapping, replace_header

    path = repo / "HomAlg/Fixture2000/Thm_1.lean"
    source = path.read_text()
    metadata = header_mapping(source)
    metadata["deps"]["proof"].append("Fixture2000.Aux_Thm_1_step")
    path.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))
    result = prune_check(repo, "Fixture2000.Aux_Thm_1_step")
    assert result["can_prune"] is False


def test_nested_options_work_outside_checkout(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Parent or leaf --repo/--json options both work from unrelated working directories."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    result = CliRunner().invoke(
        cli, ["foundations", "--repo", str(repo), "--json", "list", "Fixture2000"]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"]
