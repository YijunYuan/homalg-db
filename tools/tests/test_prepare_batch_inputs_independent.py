"""Independent adversarial checks; all source and author evidence is fictional."""

from pathlib import Path

import pytest
import test_workflow as baseline

from homalg import review, workflow
from homalg.documents import dump_metadata
from homalg.nodeio import header_mapping, replace_header
from homalg.schemas import SchemaStore

author = baseline.author
GROUPS = [("Fixture2000.Thm_1",), ("Fixture2000.Lem_1",)]


def selected_private_source(repo: Path) -> tuple[Path, Path]:
    """Give only the first author a private source dependency on page three."""
    dependency = repo / "HomAlg/Fixture2000/Lem_2.lean"
    text = dependency.read_text()
    header = header_mapping(text)
    header["source"]["pages"] = [3]
    dependency.write_text(replace_header(text, header, SchemaStore(repo / "schema")))
    page = repo / "literature/.private/Fixture2000/tex/page-0003.tex"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("Fictional private source\n")
    manifest = page.parent.parent / "transcription.yaml"
    manifest.write_text("pages:\n  '0003': {status: draft}\n")
    return page, manifest


@pytest.mark.parametrize("last_checked_author", [1, 2])
@pytest.mark.parametrize("change", ["create-page", "delete-page", "manifest", "symlink"])
def test_last_union_rejects_private_changes_after_each_author_scope_check(
    author, monkeypatch, last_checked_author, change
):
    repo, record, _ = author
    groups = baseline.two_authors(repo, record)
    page, manifest = selected_private_source(repo)
    if change == "create-page":
        page.unlink()
    outside = repo / "outside-private-document.tex"
    outside.write_text("Fictional source outside its authorized private document\n")
    select = workflow._nodes
    calls = 0

    def mutate_after_scope_check(*args, **kwargs):
        nonlocal calls
        selected = select(*args, **kwargs)
        calls += 1
        if calls == 2 + last_checked_author:
            if change == "create-page":
                page.write_text("Previously missing fictional source now exists\n")
            elif change == "delete-page":
                page.unlink()
            elif change == "manifest":
                manifest.write_text("pages:\n  '0003': {status: needs-adjudication}\n")
            else:
                page.unlink()
                page.symlink_to(outside)
        return selected

    monkeypatch.setattr(workflow, "_nodes", mutate_after_scope_check)
    with pytest.raises(ValueError, match="changed|escapes"):
        workflow.prepare_batch(
            repo, record["id"], authors=groups, out=Path("build/private-race.json")
        )
    assert calls == 4
    assert not (repo / "build/private-race.json").exists()


def test_grouped_capture_rejects_same_byte_private_replacement_but_keeps_no_cache(
    repo, monkeypatch
):
    page, _ = selected_private_source(repo)
    before = review.freeze_authoring_batch_inputs(repo, GROUPS)
    context = review.authoring_context_inputs
    calls = 0

    def replace_after_first_author(*args, **kwargs):
        nonlocal calls
        captured = context(*args, **kwargs)
        calls += 1
        if calls == 2:
            replacement = page.with_name("replacement.tex")
            replacement.write_bytes(page.read_bytes())
            replacement.replace(page)
        return captured

    monkeypatch.setattr(review, "authoring_context_inputs", replace_after_first_author)
    with pytest.raises(ValueError, match="changed"):
        review.freeze_authoring_batch_inputs(repo, GROUPS)
    monkeypatch.setattr(review, "authoring_context_inputs", context)
    # Identity must be stable during capture, while settled snapshots still bind bytes.
    assert review.freeze_authoring_batch_inputs(repo, GROUPS) == before


def test_package_revisions_bind_snapshots_but_stray_package_files_do_not(repo):
    """Packages are pinned by the manifest; a delivery binds those revisions."""
    before = review.freeze_authoring_batch_inputs(repo, GROUPS)
    stray = repo / ".lake/packages/fictional/Added.lean"
    stray.parent.mkdir(parents=True)
    stray.write_text("-- Stray local package file\n")
    assert review.freeze_authoring_batch_inputs(repo, GROUPS) == before
    manifest = repo / "lake-manifest.json"  # the baseline fixture copy has none yet
    manifest.write_text('{"packages": [{"name": "mathlib", "rev": "fictional"}]}\n')
    snapshots, combined = review.freeze_authoring_batch_inputs(repo, GROUPS)
    assert combined != before[1]
    assert snapshots == [review.freeze_authoring_inputs(repo, group) for group in GROUPS]


def test_next_author_rechecks_task_scope_after_previous_author_check(author, monkeypatch):
    repo, record, _ = author
    groups = baseline.two_authors(repo, record)
    select = workflow._nodes
    calls = 0

    def narrow_scope(*args, **kwargs):
        nonlocal calls
        selected = select(*args, **kwargs)
        calls += 1
        if calls == 3:
            record["write_set"]["files"].remove("HomAlg/Fixture2000/Lem_1.lean")
            path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
            path.write_text(dump_metadata(record))
        return selected

    monkeypatch.setattr(workflow, "_nodes", narrow_scope)
    with pytest.raises(ValueError, match="task scope changed"):
        workflow.prepare_batch(
            repo, record["id"], authors=groups, out=Path("build/scope-race.json")
        )
    assert not (repo / "build/scope-race.json").exists()
