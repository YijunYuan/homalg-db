"""Behavioral tests for deterministic extraction and bootstrap validation."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from homalg.cli import cli
from homalg.extract import extract_document
from homalg.io import atomic_write, json_text
from homalg.roots import generate_roots, stale_roots
from homalg.schemas import SchemaStore
from homalg.validate import validate_repo


def test_real_fixture_headers_validate(repo: Path) -> None:
    """Compile-independent checks accept all authored synthetic examples."""
    findings, skipped, counts = validate_repo(repo)
    assert not findings
    assert counts == {"documents": 2, "nodes": 17}
    assert "fidelity-reopened" in skipped


def test_extract_retains_derived_and_is_reproducible(repo: Path) -> None:
    """Changing prose leaves the exact existing derived object untouched."""
    schemas = SchemaStore(repo / "schema")
    previous = extract_document(repo, "Fixture2000", schemas)
    fixture = Path(__file__).parent / "fixtures/good/nodes.json"
    derived = json.loads(fixture.read_text())["nodes"][0]["derived"]
    record = next(node for node in previous["nodes"] if node["id"] == "Fixture2000.Rem_1")
    record["derived"] = derived
    target = repo / "literature/Fixture2000/nodes.json"
    atomic_write(target, json_text(previous))
    source = repo / "HomAlg/Fixture2000/Rem_1.lean"
    source.write_text(source.read_text().replace("## Description", "## Description\n\nNew prose."))
    current = extract_document(repo, "Fixture2000", schemas)
    changed = next(node for node in current["nodes"] if node["id"] == "Fixture2000.Rem_1")
    assert changed["derived"] == derived
    assert "New prose." in changed["authored"]["description_md"]
    assert current["lean"] == previous["lean"]
    atomic_write(target, json_text(current))
    before = target.read_bytes()
    modified = target.stat().st_mtime_ns
    atomic_write(target, json_text(extract_document(repo, "Fixture2000", schemas)))
    assert target.read_bytes() == before
    assert target.stat().st_mtime_ns == modified
    assert "generated_at" not in current["generator"]


def test_extract_refuses_duplicate_prior_ids(repo: Path) -> None:
    """Do not silently choose between conflicting derived records."""
    schemas = SchemaStore(repo / "schema")
    previous = extract_document(repo, "Fixture2000", schemas)
    previous["nodes"].append(previous["nodes"][0])
    (repo / "literature/Fixture2000/nodes.json").write_text(json_text(previous))
    with pytest.raises(ValueError, match="duplicate node ids"):
        extract_document(repo, "Fixture2000", schemas)


def test_roots_exclude_auxiliary_and_cited_nodes(repo: Path) -> None:
    """Bridges are public roots; cited/auxiliary nodes are reachable through users."""
    roots = generate_roots(repo)
    document = roots["HomAlg/Fixture2000.lean"]
    assert "Aux_" not in document and "Cited_" not in document
    assert "Bridge_Def_1_mathlib" in document
    assert "import HomAlg.Fixture2001" in roots["HomAlg.lean"]
    assert set(generate_roots(repo, ("Fixture2000",))) == {"HomAlg.lean", "HomAlg/Fixture2000.lean"}


def test_empty_documents_and_stale_roots(repo: Path) -> None:
    """Removing the last node removes its generated root and library import."""
    for path in (repo / "HomAlg/Fixture2001").glob("*.lean"):
        path.unlink()
    assert stale_roots(repo) == ["HomAlg/Fixture2001.lean"]
    runner = CliRunner()
    result = runner.invoke(cli, ["gen-roots", "--repo", str(repo), "--json"])
    assert result.exit_code == 0, result.output
    assert not (repo / "HomAlg/Fixture2001.lean").exists()
    assert "Fixture2001" not in (repo / "HomAlg.lean").read_text()


def test_mirror_roots_does_not_change_checkout(repo: Path, tmp_path: Path) -> None:
    """The --out mode makes reviewable generated artifacts outside the checkout."""
    original = (repo / "HomAlg.lean").read_bytes()
    output = tmp_path / "mirror"
    result = CliRunner().invoke(cli, ["gen-roots", "--repo", str(repo), "--out", str(output)])
    assert result.exit_code == 0, result.output
    assert (repo / "HomAlg.lean").read_bytes() == original
    assert (output / "HomAlg.lean").read_bytes() == original


@pytest.mark.parametrize("key,value", [("kind", "[]"), ("doc", "[]")])
def test_malformed_field_types_report_findings(repo: Path, key: str, value: str) -> None:
    """Dependent rules must not crash on syntactically valid but ill-typed YAML."""
    import re

    path = repo / "HomAlg/Fixture2000/Rem_1.lean"
    changed, count = re.subn(rf'"{key}": "[^"]+"', f'"{key}": {value}', path.read_text())
    assert count == 1
    path.write_text(changed)
    result = CliRunner().invoke(cli, ["validate", "--repo", str(repo), "--fast", "--json"])
    assert result.exit_code == 1, result.output
    report = json.loads(result.stdout)
    assert not report["ok"]
    assert any(finding["rule"] == "schema-header" for finding in report["findings"])


def test_unknown_document_is_configuration_error(repo: Path) -> None:
    """An invalid selector must not accidentally extract or validate every document."""
    result = CliRunner().invoke(
        cli, ["extract", "--repo", str(repo), "--doc", "Missing2000", "--json"]
    )
    assert result.exit_code == 2
    assert json.loads(result.stdout)["summary"]["errors"] == 1


def test_strict_mode_fails_scaffold_warnings(repo: Path) -> None:
    """Warnings remain successful by default but fail under --strict."""
    source = repo / "HomAlg/Fixture2000/Rem_1.lean"
    source.write_text(
        source.read_text().replace("## Description", "## Description\n\nTODO: explain")
    )
    args = ["validate", "--repo", str(repo), "--fast", "--json"]
    normal = CliRunner().invoke(cli, args)
    strict = CliRunner().invoke(cli, [*args, "--strict"])
    assert normal.exit_code == 0
    assert {item["rule"] for item in json.loads(normal.stdout)["findings"]} == {
        "header-sections",
        "nodes-json-stale",
    }
    assert strict.exit_code == 1


def test_extraction_checks_all_inputs_before_writing(repo: Path) -> None:
    """An invalid second document cannot leave the first partially regenerated."""
    target = repo / "literature/Fixture2000/nodes.json"
    original = target.read_bytes()
    first = repo / "HomAlg/Fixture2000/Rem_1.lean"
    first.write_text(first.read_text().replace("## Description", "## Description\n\nChanged."))
    second = next((repo / "HomAlg/Fixture2001").glob("*.lean"))
    second.write_text("/-! malformed -/")
    result = CliRunner().invoke(cli, ["extract", "--repo", str(repo), "--json"])
    assert result.exit_code != 0
    assert target.read_bytes() == original


@pytest.mark.parametrize(
    "args",
    [
        ["validate", "--json", "--unknown"],
        ["validate", "--json", "--repo"],
        ["--unknown", "validate", "--json"],
        ["unimplemented", "--json"],
    ],
)
def test_usage_errors_are_machine_readable(args: list[str]) -> None:
    """Even errors before command execution honor the requested report format."""
    result = CliRunner().invoke(cli, args)
    assert result.exit_code == 2, result.output
    assert json.loads(result.stdout)["ok"] is False


def test_external_build_failure_uses_exit_three(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Lake logs cannot pollute the JSON report; failed builds have their own exit code."""
    from homalg.leanexport import ExternalToolError

    def failed_export(*args: object, **kwargs: object) -> None:
        raise ExternalToolError(["lake", "build"], "build output\nbuild error\n")

    monkeypatch.setattr(
        "homalg.validate.export_lean",
        failed_export,
    )
    result = CliRunner().invoke(cli, ["validate", "--repo", str(repo), "--json"])
    assert result.exit_code == 3, result.output
    assert json.loads(result.stdout)["findings"][0]["rule"] == "lean-build"
    assert "build error" in result.stderr
