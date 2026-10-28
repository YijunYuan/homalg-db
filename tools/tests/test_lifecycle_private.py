"""Private scope recovery uses actual Git objects, preserving preexisting dirty/index bytes."""

import json
from pathlib import Path

import pytest

from homalg import lifecycle
from homalg.lifecycle import git, private_after_session, private_snapshot


def initialize(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.name", "Test"),
        ("config", "user.email", "test@example.invalid"),
    ):
        git(path, *args)


@pytest.fixture
def private(repo: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict]:
    root = repo / "literature/.private"
    initialize(root)
    directory = root / "Fixture2000/tex"
    directory.mkdir(parents=True)
    for number in (1, 2):
        (directory / f"page-{number:04}.tex").write_text(f"Original page {number}.\n")
    manifest = {
        "schema_version": 1,
        "doc_key": "Fixture2000",
        "pdf_sha256": "a" * 64,
        "pages": {"0001": {"status": "todo"}, "0002": {"status": "todo"}},
    }
    (directory.parent / "transcription.yaml").write_text(json.dumps(manifest))
    git(root, "add", ".")
    git(root, "commit", "-qm", "Initial private pages")
    monkeypatch.setattr("homalg.publishing.notify", lambda *args, **kwargs: "I-0001")
    task = {
        "id": "T-Fixture2000-1",
        "metadata": {"homalg": {"doc": "Fixture2000", "stage": "T", "pages": [1]}},
    }
    return root, task


def test_private_rollback_preserves_preexisting_dirty_and_staged_bytes(
    repo: Path, private: tuple
) -> None:
    root, task = private
    second = root / "Fixture2000/tex/page-0002.tex"
    second.write_text("User's staged revision.\n")
    git(root, "add", str(second))
    staged = git(root, "show", ":Fixture2000/tex/page-0002.tex").stdout
    second.write_text("User's later unstaged revision.\n")
    note = root / "personal-note.txt"
    note.write_text("Preexisting untracked note.\n")
    private_snapshot(repo)
    second.write_text("Unauthorized session replacement.\n")
    git(root, "add", str(second))
    note.unlink()
    (root / "unexpected.txt").write_text("Session output outside task.\n")
    first = root / "Fixture2000/tex/page-0001.tex"
    first.write_text("Authorized transcription.\n")
    result = private_after_session(repo, task, repo / "session")
    assert set(result["violations"]) == {
        "Fixture2000/tex/page-0002.tex",
        "personal-note.txt",
        "unexpected.txt",
    }
    assert second.read_text() == "User's later unstaged revision.\n"
    assert git(root, "show", ":Fixture2000/tex/page-0002.tex").stdout == staged
    assert note.read_text() == "Preexisting untracked note.\n"
    assert not (root / "unexpected.txt").exists()
    assert (
        git(root, "show", "HEAD:Fixture2000/tex/page-0001.tex").stdout
        == b"Authorized transcription.\n"
    )
    assert git(root, "show", "HEAD:Fixture2000/tex/page-0002.tex").stdout == b"Original page 2.\n"
    assert private_after_session(repo, task, repo / "session")["changed"] == []


def test_manifest_changes_are_limited_to_task_pages(repo: Path, private: tuple) -> None:
    root, task = private
    manifest = root / "Fixture2000/transcription.yaml"
    before = manifest.read_bytes()
    private_snapshot(repo)
    changed = json.loads(before)
    changed["pages"]["0002"]["status"] = "transcribed"
    manifest.write_text(json.dumps(changed))
    result = private_after_session(repo, task, repo / "session")
    assert result["violations"] == ["Fixture2000/transcription.yaml"]
    assert manifest.read_bytes() == before


def test_private_head_change_is_not_silently_published(repo: Path, private: tuple) -> None:
    root, task = private
    private_snapshot(repo)
    git(root, "commit", "--allow-empty", "-qm", "Unexpected concurrent private commit")
    with pytest.raises(ValueError, match="HEAD changed"):
        private_after_session(repo, task, repo / "session")


def test_missing_private_snapshot_stops_transcription(repo: Path, private: tuple) -> None:
    _, task = private
    with pytest.raises(ValueError, match="baseline"):
        private_after_session(repo, task, repo / "session")
    assert (
        lifecycle.private_after_session(
            repo, {"metadata": {"homalg": {"stage": "DAG"}}}, repo / "session"
        )["changed"]
        == []
    )


def test_index_only_out_of_scope_change_is_restored(repo: Path, private: tuple) -> None:
    root, task = private
    second = root / "Fixture2000/tex/page-0002.tex"
    second.write_text("User's pending unstaged work.\n")
    before_index = git(root, "show", ":Fixture2000/tex/page-0002.tex").stdout
    private_snapshot(repo)
    git(root, "add", str(second))
    result = private_after_session(repo, task, repo / "session")
    assert result["violations"] == ["Fixture2000/tex/page-0002.tex"]
    assert second.read_text() == "User's pending unstaged work.\n"
    assert git(root, "show", ":Fixture2000/tex/page-0002.tex").stdout == before_index


def test_transcription_session_cannot_forge_human_review(repo: Path, private: tuple) -> None:
    root, task = private
    path = root / "Fixture2000/transcription.yaml"
    before = path.read_bytes()
    private_snapshot(repo)
    data = json.loads(before)
    data["pages"]["0001"]["reviews"] = [
        {"kind": "human", "by": "invented", "status": "satisfactory"}
    ]
    path.write_text(json.dumps(data))
    result = private_after_session(repo, task, repo / "session")
    assert result["violations"] == ["Fixture2000/transcription.yaml"]
    assert path.read_bytes() == before
