"""Positive and adversarial authored-source checks with real repository fixtures."""

import json
import subprocess
from pathlib import Path

import pytest

from homalg.checks import RULES
from homalg.checks.context import Context
from homalg.headers import parse_header
from homalg.leantext import commands
from homalg.validate import FILE_RULES, compiled_context, load_context, validate_repo

GOLDEN = Path(__file__).parent / "golden/fixture-export.json"
PRIMARY = "HomAlg/Fixture2000/Thm_1.lean"


@pytest.fixture
def context(repo: Path) -> Context:
    """Load complete valid authored inputs and genuine compiled fixture observations."""
    ctx = load_context(repo)
    compiled_context(ctx, json.loads(GOLDEN.read_text()))
    return ctx


def replace_source(ctx: Context, path: str, source: str) -> None:
    """Reparse source edits exactly as the validation loader does."""
    header = parse_header(source)
    ctx.sources[path] = ctx.all_sources[path] = source
    ctx.headers[path] = ctx.valid_headers[path] = ctx.all_headers[path] = header
    ctx.commands[path] = commands(source)


def test_every_rule_is_registered_and_real_fixtures_pass(context: Context) -> None:
    """Each check has explicit prerequisites and passes a genuine compiled fixture."""
    assert len(RULES) >= 65
    for name, rule in RULES.items():
        assert rule.name == name
        assert callable(rule.check)
        if not (rule.needs_pr_context or rule.needs_private or rule.needs_prerender):
            assert not rule(context), name


@pytest.mark.parametrize(
    "rule,source",
    json.loads((Path(__file__).parent / "fixtures/bad/source-rules/cases.json").read_text()),
)
def test_unsafe_lean_source_is_rejected(context: Context, rule: str, source: str) -> None:
    """Real Lean snippets exercise tokenization, namespace ownership and unsafe commands."""
    replace_source(context, PRIMARY, context.sources[PRIMARY] + "\n" + source)
    assert RULES[rule](context)


@pytest.mark.parametrize("module", ["Mathlib", "HomAlg", "HomAlg.Fixture2001"])
def test_umbrella_imports_are_rejected(context: Context, module: str) -> None:
    replace_source(context, PRIMARY, f"import {module}\n" + context.sources[PRIMARY])
    assert RULES["lean-style"](context)


def test_safe_local_commands_and_literal_words_are_accepted(context: Context) -> None:
    source = (
        context.sources[PRIMARY]
        + """
namespace Fixture2000
local notation "safe" => True
attribute [local simp] Nat.add_comm
/-- A documented helper whose string contains sorry. -/
def literal : String := "sorry unsafe def escaped"
end Fixture2000
"""
    )
    replace_source(context, PRIMARY, source)
    assert not RULES["lean-style"](context)
    assert not RULES["sorry-named"](context)


@pytest.mark.parametrize(
    "rule,path,key,value",
    [
        ("id-path", PRIMARY, "doc", "Fixture2001"),
        ("id-grammar", PRIMARY, "id", "Fixture2000.Thm_1"),
        ("aux-parent", PRIMARY, "aux", {"kind": "helper", "parent": "Fixture2001.Thm_1"}),
        (
            "cited-source",
            PRIMARY,
            "cited",
            {
                "formulation": "editorial",
                "source": {"kind": "document", "doc": "Missing2000"},
                "used_at": [],
            },
        ),
        ("tags-known", PRIMARY, "tags", ["unknown-tag"]),
        ("concepts-known", PRIMARY, "concepts", {"introduces": ["unknown-concept"]}),
        ("deps-exist", PRIMARY, "deps", {"statement": ["Fixture2000.Missing"], "proof": []}),
        ("deps-imported", PRIMARY, "deps", {"statement": ["Fixture2000.Rem_1"], "proof": []}),
        ("foundation-declared", PRIMARY, "fidelity", {"status": "foundation"}),
        ("deviation-justified", PRIMARY, "fidelity", {"status": "deviates", "deviations": []}),
    ],
)
def test_authored_invariants_reject_concrete_bad_metadata(
    context: Context, rule: str, path: str, key: str, value: object
) -> None:
    """Context-level cases isolate invariants beyond schema validation."""
    context.valid_headers[path].metadata[key] = value
    if rule == "id-grammar":
        context.retired["Fixture2000.Thm_1"] = {"kind": "pruned"}
    assert RULES[rule](context)


def test_cycles_include_planned_nodes_and_cross_document_imports(context: Context) -> None:
    context.valid_headers[PRIMARY].metadata["deps"]["proof"].append("Fixture2000.Rem_1")
    context.valid_headers["HomAlg/Fixture2000/Rem_1.lean"].metadata["deps"]["proof"].append(
        "Fixture2000.Thm_1"
    )
    assert RULES["deps-acyclic"](context)
    replace_source(context, PRIMARY, "import HomAlg.Fixture2001.Thm_1\n" + context.sources[PRIMARY])
    assert RULES["doc-acyclic"](context)
    assert RULES["doc-import-direction"](context)
    context.all_docs["Fixture2000"]["may_import"] = ["Fixture2001"]
    assert not RULES["doc-import-direction"](context)


def test_labels_inventory_and_unused_citations(context: Context) -> None:
    header = context.valid_headers[PRIMARY]
    header.metadata["source"]["label"] = "Definition 1"
    assert RULES["label-unique"](context)
    context.inventories["Fixture2000"] = {
        "doc_key": "Fixture2000",
        "pages": {
            "0001": {
                "complete": True,
                "items": [{"label": "X", "disposition": "node", "node": "Fixture2001.Thm_1"}],
            }
        },
    }
    assert RULES["inventory-valid"](context)
    for item in context.all_headers.values():
        item.metadata["deps"]["proof"] = []
        item.metadata["deps"]["statement"] = []
    assert RULES["cited-used"](context)


def test_taxonomy_alias_diagnostics_and_cycles(context: Context) -> None:
    context.valid_headers[PRIMARY].metadata["tags"] = ["chain-complex"]
    context.taxonomy["tags"]["tags"][0]["merged_into"] = "homology"
    assert RULES["tags-known"](context)[0].severity == "warning"
    context.changed_paths.add(PRIMARY)
    assert any(
        item.file == PRIMARY and item.severity == "error" for item in RULES["tags-known"](context)
    )
    homology = next(item for item in context.taxonomy["tags"]["tags"] if item["id"] == "homology")
    homology["merged_into"] = "chain-complex"
    assert RULES["taxonomy-merge-cycle"](context)


def test_repository_files_and_english(context: Context) -> None:
    (context.repo / "paper.PDF").write_bytes(b"%PDF-1.7")
    private = context.repo / "literature/.private/Fixture2000/source.pdf"
    private.parent.mkdir(parents=True)
    private.write_bytes(b"%PDF-1.7")
    assert len(RULES["no-pdf"](context)) == 1
    (context.repo / "REGISTRY.md").write_text("Legacy registry\n")
    assert RULES["registry-none"](context)
    context.sources[PRIMARY] += "\n" * 2001
    assert RULES["file-size"](context)
    context.valid_headers[PRIMARY].sections["Description"] = "非英语说明"
    assert RULES["english-only"](context)
    context.valid_headers[PRIMARY].sections["Description"] = "A map α → β."
    assert not RULES["english-only"](context)


def test_freshness_detects_content_edits_without_writing(context: Context) -> None:
    target = context.repo / "literature/Fixture2000/nodes.json"
    original = target.read_bytes()
    context.sources[PRIMARY] += "\n-- Additional comment.\n"
    assert RULES["nodes-json-stale"](context)
    context.expected_nodes["Fixture2000"]["nodes"][0]["authored"]["description_md"] += " changed"
    assert RULES["nodes-json-fresh"](context)
    assert target.read_bytes() == original
    (context.repo / "HomAlg/Fixture2000.lean").write_text("-- stale\n")
    assert RULES["roots-fresh"](context)


def test_invalid_header_and_file_alias_report_without_crashing(repo: Path, tmp_path: Path) -> None:
    source = tmp_path / "editor-buffer.lean"
    source.write_text("import Mathlib\n/-! broken")
    findings, skipped, counts = validate_repo(
        repo, files=((source, "HomAlg/Fixture2000/Thm_1.lean"),)
    )
    assert any(item.rule == "header-syntax" for item in findings)
    assert counts["nodes"] == 1
    assert set(skipped) == set(RULES) - FILE_RULES


def test_only_and_missing_context_are_explicit(repo: Path) -> None:
    findings, skipped, _ = validate_repo(repo, only=("owner-approval",))
    assert not findings and skipped == ["owner-approval"]
    with pytest.raises(ValueError, match="Unknown validation"):
        validate_repo(repo, only=("invented",))
    with pytest.raises(ValueError, match="requires --export"):
        validate_repo(repo, no_build=True)
    findings, skipped, _ = validate_repo(repo, no_build=True, export=json.loads(GOLDEN.read_text()))
    assert not findings
    assert {"lean-build", "nodes-json-fresh"} <= set(skipped)
    assert "decls-exist" not in skipped


def test_no_build_validation_preserves_committed_files(repo: Path) -> None:
    path = repo / "literature/Fixture2000/nodes.json"
    before = path.read_bytes()
    source = repo / PRIMARY
    source.write_text(
        source.read_text().replace("## Description", "## Description\n\nEdited prose.")
    )
    findings, _, _ = validate_repo(repo, fast=False, export=json.loads(GOLDEN.read_text()))
    assert any(item.rule == "nodes-json-fresh" for item in findings)
    assert path.read_bytes() == before


def test_force_tracked_private_pdf_is_rejected(context: Context) -> None:
    subprocess.run(["git", "init", "-q"], cwd=context.repo, check=True)
    path = context.repo / "literature/.private/Fixture2000/source.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"%PDF-1.7")
    subprocess.run(["git", "add", "-f", str(path)], cwd=context.repo, check=True)
    assert RULES["no-pdf"](context)
