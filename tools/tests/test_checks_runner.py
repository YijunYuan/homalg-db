"""Validation dispatch uses prerequisites and PR context without weakening reports."""

import json
import subprocess
from pathlib import Path

import pytest

from homalg.checks import RULES
from homalg.checks.context import Finding
from homalg.validate import load_context, validate_repo


def git_repo(repo: Path) -> None:
    for command in (
        ["init", "-q"],
        ["config", "user.name", "Test"],
        ["config", "user.email", "test@example.invalid"],
        ["add", "."],
        ["commit", "-qm", "Initial test inputs"],
    ):
        subprocess.run(["git", *command], cwd=repo, check=True)


def test_pr_dispatch_runs_once_and_owner_only_is_separate(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git_repo(repo)
    calls = []

    def run(_repo: Path, **kwargs):
        calls.append(kwargs)
        name = "owner-approval" if kwargs.get("owner_only") else "claim-author"
        return [Finding(name, "error", "", "Test adjudication")]

    monkeypatch.setattr("homalg.pr_checks.pr_findings", run)
    findings, skipped, _ = validate_repo(repo, pr_base="HEAD", pr_author="contributor")
    assert len(calls) == 1
    assert "owner-approval" in skipped
    assert any(item.rule == "claim-author" for item in findings)
    calls.clear()
    findings, skipped, _ = validate_repo(
        repo,
        pr_base="HEAD",
        pr_author="contributor",
        only=("owner-approval",),
        pr_number=42,
        pr_head="HEAD",
    )
    assert len(calls) == 1 and calls[0]["owner_only"]
    assert calls[0]["number"] == 42
    assert not skipped and findings[0].rule == "owner-approval"


def test_changed_scope_and_base_capture(repo: Path) -> None:
    git_repo(repo)
    subprocess.run(["git", "update-ref", "refs/remotes/origin/main", "HEAD"], cwd=repo, check=True)
    path = repo / "HomAlg/Fixture2001/Thm_1.lean"
    before = path.read_text()
    path.write_text(before + "\n-- Working tree edit.\n")
    ctx = load_context(repo, changed=True)
    assert set(ctx.docs) == {"Fixture2001"}
    assert ctx.base_sources[path.relative_to(repo).as_posix()] == before
    assert len(ctx.sources) == 2
    findings, _, _ = validate_repo(repo, changed=True)
    assert any(item.rule == "nodes-json-stale" for item in findings)


def test_schema_errors_are_selected_and_never_crash_dependent_checks(repo: Path) -> None:
    target = repo / "literature/Fixture2000/document.yaml"
    record = json.loads(target.read_text())
    record["year"] = "bad-year"
    target.write_text(json.dumps(record))
    findings, _, _ = validate_repo(repo)
    assert any(item.rule == "schema-document" for item in findings)
    findings, _, _ = validate_repo(repo, only=("schema-claim",))
    assert not findings
    target = repo / "literature/Fixture2000/inventory.yaml"
    target.write_text("schema_version: 1\nitems: []\n")
    findings, _, _ = validate_repo(repo, only=("inventory-valid",))
    assert findings and all(item.rule == "inventory-valid" for item in findings)


def test_header_schema_sections_and_document_identity(repo: Path) -> None:
    source = repo / "HomAlg/Fixture2000/Thm_1.lean"
    source.write_text(source.read_text().replace('"kind": "theorem"', '"kind": []'))
    findings, _, _ = validate_repo(repo, only=("schema-header",))
    assert findings and all(item.rule == "schema-header" for item in findings)
    ctx = load_context(repo)
    header = ctx.headers["HomAlg/Fixture2000/Thm_1.lean"]
    header.sections["Statement"] = ""
    assert RULES["header-sections"](ctx)
    ctx.docs["Fixture2000"]["doc_key"] = "Fixture2001"
    assert RULES["schema-document"](ctx)


def test_out_of_scope_new_source_item(repo: Path) -> None:
    ctx = load_context(repo)
    path = "HomAlg/Fixture2000/Thm_1.lean"
    header = ctx.valid_headers[path]
    header.metadata["doc"] = "Author2000"
    ctx.claims["Author2000"] = {
        "claims": [
            {
                "holder": "contributor",
                "claimed_at": "2026-01-01T00:00:00Z",
                "expires_at": "2026-04-01T00:00:00Z",
                "scope": {"chapters": ["99"], "sections": []},
            }
        ]
    }
    ctx.now = "2026-02-01T00:00:00Z"
    assert RULES["out-of-scope"](ctx)
    ctx.claims["Author2000"]["claims"][0]["scope"]["chapters"] = [
        header.metadata["source"]["chapter"]
    ]
    assert not RULES["out-of-scope"](ctx)
