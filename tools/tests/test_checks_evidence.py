"""Relations, disputes, source provenance and rendering evidence remain independently auditable."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from homalg.checks import RULES
from homalg.checks.context import Context
from homalg.checks.evidence_rules import join_reviewed_pages, normalized_excerpt
from homalg.relations import relation_id
from homalg.validate import load_context


def test_cross_page_paragraph_keeps_footnotes_separately() -> None:
    """Printed page furniture must not interrupt a genuine cross-page source paragraph."""
    source = normalized_excerpt(
        join_reviewed_pages(
            [
                "% source: original\nThis paragraph ends within a\n\n"
                "\\paragraph{[Footnote 2]} A separate definition is $x_i = 1$.",
                "% pdf_page: 2\n% transcribed_by: independent\ncoboundary and continues.\n",
            ]
        )
    )
    assert "This paragraph ends within a coboundary and continues." in source
    assert "A separate definition is $x_i = 1$." in source
    assert "source:" not in source
    assert "$x_i = 0$" not in source


@pytest.fixture
def ctx(repo: Path) -> Context:
    return load_context(repo)


def relation(
    ctx: Context,
    *,
    source: str = "Fixture2000.Def_1",
    target: str = "Fixture2001.Def_1",
    kind: str = "precursor_of",
) -> tuple[str, dict]:
    path = "taxonomy/relations/Fixture2000.yaml"
    record = {
        "id": relation_id(source, kind, target),
        "source": source,
        "type": kind,
        "target": target,
        "provenance": {"on": "2001-01-01"},
        "review": {"status": "unreviewed"},
    }
    ctx.relation_records = [(path, record, False)]
    return path, record


def test_relations_canonicalization_duplicates_and_endpoints(ctx: Context) -> None:
    path, record = relation(ctx)
    assert not RULES["relations-valid"](ctx)
    assert not RULES["relation-review"](ctx)
    record["id"] = "rel-00000000"
    assert record["source"] in ctx.existing_nodes
    assert "must be rel-" in RULES["relations-valid"](ctx)[0].message
    record["id"] = relation_id(record["source"], record["type"], record["target"])
    ctx.relation_records.append(
        (
            "HomAlg/Fixture2000/Def_1.lean",
            record
            | {"id": relation_id(record["source"], record["type"], record["target"], header=True)},
            True,
        )
    )
    assert any(
        "Duplicate canonical" in finding.message for finding in RULES["relations-valid"](ctx)
    )
    ctx.relation_records.pop()
    record["target"] = record["source"]
    assert any("itself" in finding.message for finding in RULES["relations-valid"](ctx))
    record["target"] = "Fixture2001.Def_1"
    record["bridge"] = "Fixture2000.Lem_2"
    assert any("bridge" in finding.message for finding in RULES["relations-valid"](ctx))
    record.pop("bridge")
    record["provenance"] = {}
    assert any("source date" in finding.message for finding in RULES["relations-valid"](ctx))


def test_historical_dangling_relations_warn_but_changed_records_block(ctx: Context) -> None:
    path, record = relation(ctx, target="Fixture2001.Missing")
    findings = RULES["relations-valid"](ctx)
    assert findings[0].rule == "relation-dangling" and findings[0].severity == "warning"
    ctx.pr = {"base": "main"}
    ctx.changed_paths.add(path)
    ctx.base_sources[path] = json.dumps({"relations": [record]})
    assert RULES["relations-valid"](ctx)[0].severity == "warning"
    record["note"] = "This record was edited"
    assert RULES["relations-valid"](ctx)[0].severity == "error"
    ctx.retired["Fixture2001.Missing"] = {"moved_to": "Fixture2001.Def_1"}
    assert not RULES["relations-valid"](ctx)
    ctx.retired["Fixture2001.Def_1"] = {"moved_to": "Fixture2001.Missing"}
    assert "cycle" in RULES["relations-valid"](ctx)[0].message


def test_relation_decisions_and_year_direction(ctx: Context) -> None:
    _, record = relation(ctx)
    record["review"] = {"status": "accepted", "by": "fictional-reviewer"}
    assert RULES["relation-review"](ctx)
    ctx.relation_reviews = {"reviews": {"rel-00000000": {"status": "accepted"}}}
    assert RULES["relation-reviews-valid"](ctx)[0].severity == "warning"
    record["type"] = "cites"
    assert RULES["relations-year-order"](ctx)
    record["source"], record["target"] = record["target"], record["source"]
    assert not RULES["relations-year-order"](ctx)


def evolution(ctx: Context) -> tuple[str, dict]:
    path = "taxonomy/evolution/chain-complex.yaml"
    version = {
        "version": 1,
        "provenance": {"bundle_sha256": "a" * 64},
        "stages": [
            {
                "period": "2000",
                "doc": "Fixture2000",
                "nodes": ["Fixture2000.Def_1"],
                "change": "Definition",
            }
        ],
        "proposed_relations": [],
    }
    ctx.evolution_files[path] = {"concept": "chain-complex", "summaries": [version]}
    return path, version


def test_evolution_hash_nodes_and_preserved_history(ctx: Context) -> None:
    path, version = evolution(ctx)
    assert not RULES["evolution-valid"](ctx)
    version["provenance"] = {}
    assert RULES["evolution-valid"](ctx)
    version["provenance"]["bundle_sha256"] = "a" * 64
    version["stages"][0]["nodes"] = ["Fixture2000.Retired"]
    assert RULES["evolution-valid"](ctx)[0].rule == "evolution-dangling"
    ctx.pr = {"base": "main"}
    ctx.changed_paths.add(path)
    ctx.base_sources[path] = json.dumps(ctx.evolution_files[path])
    assert RULES["evolution-valid"](ctx)[0].severity == "warning"
    version["narrative_md"] = "Changed summary"
    assert RULES["evolution-valid"](ctx)[0].severity == "error"
    ctx.retired["Fixture2000.Retired"] = {"merged_into": "Fixture2000.Def_1"}
    assert not RULES["evolution-valid"](ctx)


def test_dispute_markers_and_resolution_routes(ctx: Context) -> None:
    path = "HomAlg/Fixture2000/Prop_1.lean"
    metadata = ctx.valid_headers[path].metadata
    assert not RULES["dispute-sync"](ctx)
    metadata["dispute"]["kind"] = "proof"
    assert RULES["dispute-sync"](ctx)
    metadata["dispute"].update(
        status="resolved", confirmed_by="fictional-reviewer", resolution={"via": "withdrawn"}
    )
    assert RULES["dispute-valid"](ctx)
    metadata["dispute"]["resolution"]["via"] = "erratum"
    assert RULES["dispute-valid"](ctx)
    metadata["fidelity"]["deviations"] = [{"kind": "erratum"}]
    assert not RULES["dispute-valid"](ctx)
    metadata["dispute"]["kind"] = "statement"
    assert RULES["dispute-valid"](ctx)
    ctx.valid_headers[path].sections["Statement (corrected)"] = "Corrected statement."
    assert not RULES["dispute-valid"](ctx)
    metadata["dispute"]["resolution"]["via"] = "proof-route"
    assert RULES["dispute-valid"](ctx)
    metadata["dispute"]["kind"] = "proof"
    metadata["fidelity"]["deviations"] = [{"kind": "proof-route"}]
    assert not RULES["dispute-valid"](ctx)


def test_dispute_append_only_and_archived_inbox(ctx: Context) -> None:
    path = "HomAlg/Fixture2000/Prop_1.lean"
    ctx.pr = {"base": "main"}
    ctx.base_sources[path] = ctx.sources[path]
    metadata = ctx.valid_headers[path].metadata
    original = metadata.pop("dispute")
    assert RULES["dispute-valid"](ctx)
    metadata["dispute_history"] = [copy.deepcopy(original)]
    assert not RULES["dispute-valid"](ctx)
    archived = ctx.repo / "literature/Fixture2000/run-log/inbox/dispute.yaml"
    archived.parent.mkdir(parents=True)
    archived.write_text(
        json.dumps({"kind": "dispute", "scope": {"blueprint_nodes": ["label:Fixture2000.Thm_1"]}})
    )
    assert any("Archived dispute" in finding.message for finding in RULES["dispute-valid"](ctx))


def private_page(ctx: Context) -> tuple[Path, Path]:
    header = copy.deepcopy(ctx.valid_headers["HomAlg/Fixture2000/Rem_1.lean"])
    header.metadata.update(id="Author2000.Rem_1", doc="Author2000")
    header.metadata["source"]["pages"] = [1]
    header.sections["Statement"] = "For $x_i$ in $[0,1]$, one has $x_i = x_i$."
    ctx.valid_headers = {"HomAlg/Author2000/Rem_1.lean": header}
    ctx.all_docs["Author2000"] = {"language": "en", "pdf": {"sha256": "a" * 64, "page_offset": 1}}
    ctx.docs = {"Author2000": ctx.all_docs["Author2000"]}
    private = ctx.repo / "literature/.private/Author2000"
    page = private / "tex/page-0002.tex"
    page.parent.mkdir(parents=True)
    page.write_text(r"\begin{remark}" + header.sections["Statement"] + r"\end{remark}")
    digest = hashlib.sha256(page.read_bytes()).hexdigest()
    manifest = private / "transcription.yaml"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "doc_key": "Author2000",
                "pdf_sha256": "a" * 64,
                "pages": {
                    "0002": {
                        "status": "reviewed",
                        "file_sha256": digest,
                        "transcribed_by": {"session": "test", "at": "2000-01-01T00:00:00Z"},
                        "reviews": [
                            {
                                "status": "satisfactory",
                                "by": "fictional-reviewer",
                                "at": "2000-01-01T00:00:00Z",
                                "file_sha256": digest,
                            }
                        ],
                    }
                },
            }
        )
    )
    return page, manifest


def test_private_provenance_preserves_math_and_reviewed_page_bytes(ctx: Context) -> None:
    page, _ = private_page(ctx)
    assert not RULES["statement-provenance"](ctx)
    header = next(iter(ctx.valid_headers.values()))
    header.sections["Statement"] += " An invented sentence."
    assert "paragraph" in RULES["statement-provenance"](ctx)[0].message
    header.sections["Statement"] = "For $x_j$ in $[0,1]$, one has $x_j = x_j$."
    assert RULES["statement-provenance"](ctx)
    page.write_text(page.read_text() + "\nnew page edit")
    assert any("current bytes" in finding.message for finding in RULES["statement-provenance"](ctx))
    assert (
        normalized_excerpt("*A result* [editorial] $x_i \\in [0,1]$") == "A result $x_i \\in [0,1]$"
    )


def test_markdown_findings_restrict_document_scope(ctx: Context) -> None:
    ctx.health = {
        "markdown_findings": [
            {"node": "Fixture2000.Thm_1", "message": "Unbalanced KaTeX brace"},
            {"node": "Unknown2000.Thm_1", "message": "Broken link"},
        ]
    }
    assert len(RULES["markdown-renders"](ctx)) == 1
    ctx.docs = {"Fixture2001": ctx.docs["Fixture2001"]}
    assert not RULES["markdown-renders"](ctx)


def test_provenance_distinguishes_authored_bridges_from_source_statements(ctx: Context) -> None:
    """Contributor bridges are new mathematics; verbatim citations still require source evidence."""
    private_page(ctx)
    header = next(iter(ctx.valid_headers.values()))
    header.sections["Statement"] = "The source encoding is equivalent to a library encoding."
    assert RULES["statement-provenance"](ctx)
    header.metadata["aux"] = {
        "parent": "Author2000.Def_1",
        "kind": "bridge",
        "reason": "Compare the historical and library definitions.",
    }
    assert not RULES["statement-provenance"](ctx)
    del header.metadata["aux"]
    header.metadata["cited"] = {"formulation": "verbatim"}
    assert RULES["statement-provenance"](ctx)
    header.metadata["cited"]["formulation"] = "editorial"
    assert not RULES["statement-provenance"](ctx)
