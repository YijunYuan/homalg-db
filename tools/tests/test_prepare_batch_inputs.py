"""Exact, call-local author snapshots; all review identities are fictional."""

import copy
from pathlib import Path

import pytest
import test_workflow as baseline

from homalg import leanexport, review, workflow
from homalg.nodeio import header_mapping, replace_header
from homalg.schemas import SchemaStore

author = baseline.author
GROUPS = [("Fixture2000.Thm_1",), ("Fixture2000.Lem_1",)]


def private_inputs(repo: Path) -> tuple[Path, Path]:
    """Only the first author's proof dependency selects the third fixture page."""
    path = repo / "HomAlg/Fixture2000/Lem_2.lean"
    source = path.read_text()
    metadata = header_mapping(source)
    metadata["source"]["pages"] = [3]
    path.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))
    page = repo / "literature/.private/Fixture2000/tex/page-0003.tex"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("Fictional original source page\n")
    manifest = page.parent.parent / "transcription.yaml"
    manifest.write_text("pages:\n  '0003': {status: draft}\n  '0099': {status: draft}\n")
    return page, manifest


def test_grouped_snapshots_equal_standalone_including_scoped_private_context(repo, monkeypatch):
    page, _ = private_inputs(repo)
    expected = [review.freeze_authoring_inputs(repo, group) for group in GROUPS]
    union = review.freeze_authoring_inputs(repo, [node for group in GROUPS for node in group])
    original = leanexport.compilation_inputs
    captures = []

    def count_capture(path):
        result = original(path)
        captures.append(result)
        return result

    monkeypatch.setattr(leanexport, "compilation_inputs", count_capture)
    actual, combined = review.freeze_authoring_batch_inputs(repo, GROUPS)
    assert len(captures) == 2
    assert actual == expected
    assert combined == union
    assert str(page) in actual[0]["context"]["files"]
    assert str(page) not in actual[1]["context"]["files"]
    other, union_before = copy.deepcopy(actual[1]), copy.deepcopy(combined)
    actual[0]["compilation"]["files"].clear()
    actual[0]["compilation"]["environment"]["PATH"] = "fictional mutation"
    actual[0]["context"]["node_ids"].clear()
    assert actual[1] == other and combined == union_before


def test_grouped_capture_parses_each_document_once_per_guarded_read(repo, monkeypatch):
    document = (repo / "literature/Fixture2000/document.yaml").read_text()
    load = review.load_yaml
    count = 0

    def counted(text):
        nonlocal count
        count += text == document
        return load(text)

    monkeypatch.setattr(review, "load_yaml", counted)
    review.freeze_authoring_batch_inputs(repo, GROUPS)
    assert count == 2  # Shared capture, then a fresh independent union recheck.


@pytest.mark.parametrize(
    "changed",
    [
        "node",
        "dependency",
        "document",
        "policy",
        "toolchain",
        "inventory",
        "taxonomy",
        "private",
        "manifest",
        "new-node",
        "restore",
    ],
)
def test_grouped_capture_rejects_changed_inputs_and_next_call_is_fresh(repo, monkeypatch, changed):
    page, manifest = private_inputs(repo)
    paths = {
        "node": repo / "HomAlg/Fixture2000/Thm_1.lean",
        "dependency": repo / "HomAlg/Fixture2000/Def_1.lean",
        "document": repo / "literature/Fixture2000/document.yaml",
        "policy": repo / "horizon/review-policy.yaml",
        "toolchain": repo / "lean-toolchain",
        "inventory": repo / "literature/Fixture2000/inventory.yaml",
        "taxonomy": repo / "taxonomy/batch-test.yaml",
        "private": page,
        "manifest": manifest,
        "new-node": repo / "HomAlg/Fixture2000/New_batch_input.lean",
        "restore": repo / "HomAlg/Fixture2000/Thm_1.lean",
    }
    context = review.authoring_context_inputs
    calls = 0

    def change_after_first_author(*args, **kwargs):
        nonlocal calls
        result = context(*args, **kwargs)
        calls += 1
        if calls == 2:
            path = paths[changed]
            path.parent.mkdir(parents=True, exist_ok=True)
            old = path.read_text() if path.exists() else ""
            path.write_text(old + "\n# Concurrent fictional input edit\n")
            if changed == "restore":
                path.write_text(old)
        return result

    monkeypatch.setattr(review, "authoring_context_inputs", change_after_first_author)
    with pytest.raises(ValueError, match="changed"):
        review.freeze_authoring_batch_inputs(repo, GROUPS)
    monkeypatch.setattr(review, "authoring_context_inputs", context)
    # Failed capture state is not retained, even when bytes were restored.
    if changed == "new-node":
        paths[changed].unlink()
    current, union = review.freeze_authoring_batch_inputs(repo, GROUPS)
    assert current == [review.freeze_authoring_inputs(repo, group) for group in GROUPS]
    assert union == review.freeze_authoring_inputs(
        repo, [node for group in GROUPS for node in group]
    )


def test_grouped_prepare_preserves_final_union_after_each_author_scope_check(author, monkeypatch):
    repo, record, _ = author
    groups = baseline.two_authors(repo, record)
    page, _ = private_inputs(repo)
    select = workflow._nodes
    calls = 0

    def mutate_earlier_author(*args, **kwargs):
        nonlocal calls
        result = select(*args, **kwargs)
        calls += 1
        if calls == 3:
            page.write_text("Changed private source after first author's own scope check\n")
        return result

    monkeypatch.setattr(workflow, "_nodes", mutate_earlier_author)
    with pytest.raises(ValueError, match="Batch author inputs changed"):
        workflow.prepare_batch(repo, record["id"], authors=groups, out=Path("build/race.json"))
    assert calls == 4
    assert not (repo / "build/race.json").exists()


def test_grouped_freeze_preserves_unrelated_manifest_page_projection(repo):
    _, manifest = private_inputs(repo)
    before = review.freeze_authoring_batch_inputs(repo, GROUPS)
    manifest.write_text(
        manifest.read_text().replace("'0099': {status: draft}", "'0099': {status: reviewed}")
    )
    assert review.freeze_authoring_batch_inputs(repo, GROUPS) == before


def test_grouped_prepare_still_exports_and_validates_once_per_invocation(author, monkeypatch):
    repo, record, commands = author
    groups = baseline.two_authors(repo, record)
    validate = workflow.validate_repo
    validations = []

    def counted(*args, **kwargs):
        result = validate(*args, **kwargs)
        validations.append(result)
        return result

    monkeypatch.setattr(workflow, "validate_repo", counted)
    for name in ("first", "second"):
        data = workflow.prepare_batch(
            repo, record["id"], authors=groups, out=Path(f"build/{name}.json")
        )
        assert data["ready_for_review"] and not data["approval"] and not data["task_complete"]
    assert len(validations) == 2
    assert [command[1] for command in commands] == ["build", "exe", "build", "exe"]
    assert validations[0] == validations[1]
