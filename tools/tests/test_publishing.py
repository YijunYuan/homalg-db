"""Numeric status uses live ownership and fast-forward Git plumbing against local bare remotes."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from homalg import publishing
from homalg.collaboration import Client, ExternalToolError
from homalg.documents import dump_metadata
from homalg.lifecycle import git
from homalg.schemas import SchemaStore

NOW = datetime(2026, 1, 15, tzinfo=UTC)


def test_diagnostic_inbox_body_has_a_title_and_paragraph(repo: Path, monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(publishing, "inbox_items", lambda _: [])
    monkeypatch.setattr(
        publishing.engine,
        "horizon",
        lambda root, *args: calls.append((root, args)) or '{"id":"I-0001"}',
    )
    assert (
        publishing.notify(
            repo, "Fixture2000", "Publication failed.", rule="publish", node="Fixture2000.Thm_1"
        )
        == "I-0001"
    )
    root, args = calls[0]
    assert root == repo
    body = args[args.index("--body") + 1]
    assert body == "[homalg:publish:Fixture2000.Thm_1]\n\nPublication failed."


@pytest.fixture
def publication(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    remote = tmp_path / "public.git"
    remote.mkdir()
    git(remote, "init", "--bare", "-q", "-b", "main")
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.name", "Test"),
        ("config", "user.email", "test@example.invalid"),
    ):
        git(repo, *args)
    (repo / ".gitignore").write_text(
        ".archon-horizon/\nbuild/\npublic.git/\nliterature/.private/\n"
    )
    claim = {
        "schema_version": 1,
        "doc_key": "Fixture2000",
        "claims": [
            {
                "holder": "alice",
                "claimed_at": "2026-01-01T00:00:00Z",
                "expires_at": "2026-03-01T00:00:00Z",
                "scope": {"chapters": ["1"], "sections": [], "note": "PRIVATE CLAIM TEXT"},
            }
        ],
    }
    (repo / "literature/Fixture2000/claim.yaml").write_text(dump_metadata(claim))
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "Registered contribution")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-qu", "origin", "main")
    git(repo, "checkout", "-qb", "work")
    settings = repo / ".archon-horizon/overlay/homalg.yaml"
    settings.parent.mkdir(parents=True)
    settings.write_text("login: alice\n")
    monkeypatch.setattr(publishing, "inbox_items", lambda repo: [])
    monkeypatch.setattr(publishing, "notify", lambda *args, **kwargs: "I-0001")
    return repo, remote


def test_status_is_numeric_and_leaves_worktree_and_index_untouched(publication: tuple) -> None:
    repo, remote = publication
    (repo / "unrelated.txt").write_text("Unrelated staged user work.\n")
    git(repo, "add", "unrelated.txt")
    (repo / "unrelated.txt").write_text("Later unstaged user work.\n")
    before_head = git(repo, "rev-parse", "HEAD").stdout
    before_status = git(repo, "status", "--porcelain").stdout
    before_index = git(repo, "diff", "--cached", "--binary").stdout
    first = publishing.publish_status(repo, "Fixture2000", now=NOW)
    assert first["published"], first
    payload = json.loads(git(remote, "show", "status/Fixture2000:status.json").stdout)
    assert not SchemaStore(repo / "schema").validate(payload, "run-status.schema.json")
    assert "PRIVATE CLAIM TEXT" not in json.dumps(payload)
    assert payload["holder"] == "alice" and payload["last_check"] == {"result": "none", "at": None}
    assert git(remote, "ls-tree", "--name-only", "status/Fixture2000").stdout == b"status.json\n"
    assert git(repo, "rev-parse", "HEAD").stdout == before_head
    assert git(repo, "status", "--porcelain").stdout == before_status
    assert git(repo, "diff", "--cached", "--binary").stdout == before_index
    assert not publishing.publish_status(repo, "Fixture2000", now=NOW + timedelta(minutes=30))[
        "published"
    ]
    second = publishing.publish_status(repo, "Fixture2000", now=NOW + timedelta(minutes=61))
    assert second["published"]
    assert (
        git(remote, "rev-parse", "status/Fixture2000^").stdout.decode().strip() == first["commit"]
    )


def test_status_refuses_stale_working_branch_owner(publication: tuple, tmp_path: Path) -> None:
    repo, remote = publication
    other = tmp_path / "updater"
    git(repo, "clone", "-q", str(remote), str(other))
    git(other, "config", "user.name", "Other")
    git(other, "config", "user.email", "other@example.invalid")
    claim_path = other / "literature/Fixture2000/claim.yaml"
    claim_path.write_text(claim_path.read_text().replace("alice", "bob"))
    git(other, "add", str(claim_path))
    git(other, "commit", "-qm", "New claimant on main")
    git(other, "push", "-q", "origin", "main")
    result = publishing.publish_status(repo, "Fixture2000", now=NOW)
    assert result == {"published": False, "reason": "claim-inactive"}
    assert "alice" in (repo / "literature/Fixture2000/claim.yaml").read_text()
    assert git(
        remote, "show-ref", "--verify", "refs/heads/status/Fixture2000", check=False
    ).returncode


def test_expired_claim_cannot_be_revived_by_publication(publication: tuple) -> None:
    repo, _ = publication
    result = publishing.publish_status(repo, "Fixture2000", now=NOW + timedelta(days=400))
    assert result["reason"] == "claim-inactive"


def test_failed_fetch_is_logged_and_retried_without_throttle(publication: tuple) -> None:
    repo, _ = publication

    class Offline(Client):
        def fetch(self, key=None):
            raise ExternalToolError("network unavailable")

    result = publishing.publish_status(repo, "Fixture2000", now=NOW, client=Offline(repo))
    assert result["reason"] == "network-or-git-error"
    assert not (repo / ".archon-horizon/overlay/publish-status-Fixture2000.json").exists()
    assert "network unavailable" in (repo / ".archon-horizon/overlay/hooks.log").read_text()
    assert publishing.publish_status(repo, "Fixture2000", now=NOW)["published"]


def test_concurrent_publication_is_never_force_pushed(publication: tuple) -> None:
    repo, remote = publication
    first = publishing.publish_status(repo, "Fixture2000", now=NOW)
    other = None

    class Racing(Client):
        def git(self, *args, **kwargs):
            nonlocal other
            if (
                args[0] == "push"
                and args[1] == "origin"
                and args[2].endswith(":refs/heads/status/Fixture2000")
            ):
                tree = super().git("rev-parse", f"{first['commit']}^{{tree}}").strip()
                other = (
                    super()
                    .git(
                        "commit-tree",
                        tree,
                        "-p",
                        first["commit"],
                        "-m",
                        "Concurrent numeric status",
                    )
                    .strip()
                )
                super().git("push", "origin", f"{other}:refs/heads/status/Fixture2000")
            return super().git(*args, **kwargs)

    result = publishing.publish_status(
        repo, "Fixture2000", now=NOW + timedelta(minutes=61), client=Racing(repo)
    )
    assert not result["published"]
    assert git(remote, "rev-parse", "status/Fixture2000").stdout.decode().strip() == other


def test_backup_uses_private_remote_and_preserves_unrelated_staging(
    publication: tuple, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from homalg import lifecycle

    repo, public = publication
    private = tmp_path / "backup.git"
    private.mkdir()
    git(private, "init", "--bare", "-q", "-b", "main")
    monkeypatch.setenv("HOMALG_BACKUP_REMOTE", str(private))
    record = {
        "id": "I-001",
        "status": "open",
        "body": "Private detailed discussion",
        "scope": {"blueprint_nodes": ["Fixture2000.Thm_1"]},
    }
    monkeypatch.setattr(publishing, "inbox_items", lambda repo: [record])
    (repo / "unrelated.txt").write_text("Keep this staged separately.\n")
    git(repo, "add", "unrelated.txt")
    before = git(repo, "diff", "--cached", "--binary").stdout
    public_head = git(public, "rev-parse", "main").stdout
    result = lifecycle.backup(repo, now=NOW)
    assert result["backed_up"]
    assert result["source"] == "user-git"
    assert result["source_commit"] == git(repo, "rev-parse", "HEAD").stdout.decode().strip()
    assert git(repo, "diff", "--cached", "--binary").stdout == before
    assert git(public, "rev-parse", "main").stdout == public_head
    assert (
        b"Private detailed discussion"
        in git(
            private, "show", "backup/alice/work:literature/Fixture2000/run-log/inbox/I-001.yaml"
        ).stdout
    )
    assert git(private, "cat-file", "-e", "backup/alice/work:unrelated.txt", check=False).returncode
    assert lifecycle.backup(repo, now=NOW + timedelta(hours=5))["reason"] == "throttled"
    monkeypatch.setenv("HOMALG_BACKUP_REMOTE", "origin")
    with pytest.raises(ValueError, match="differ from the public origin"):
        lifecycle.backup(repo, now=NOW, force=True)


def ledger_git(repo: Path, *args: str, check: bool = True):
    return git(
        repo,
        "--git-dir",
        str(repo / ".archon-horizon/vcs/workspace.git"),
        "--work-tree",
        str(repo),
        *args,
        check=check,
    )


@pytest.fixture
def ledger_backup(publication: tuple, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo, public = publication
    ledger = repo / ".archon-horizon/vcs/workspace.git"
    ledger.parent.mkdir(parents=True)
    git(repo, "clone", "--bare", "-q", str(repo), str(ledger))
    ledger_git(repo, "remote", "remove", "origin")
    ledger_git(repo, "config", "user.name", "Ledger Test")
    ledger_git(repo, "config", "user.email", "ledger@example.invalid")
    (repo / "ledger-only.txt").write_text("Actual source work absent from user HEAD.\n")
    ledger_git(repo, "add", "ledger-only.txt")
    ledger_git(repo, "commit", "-qm", "Ledger source work")
    remote = tmp_path / "private-backup.git"
    remote.mkdir()
    git(remote, "init", "--bare", "-q", "-b", "sources")
    private = repo / "literature/.private"
    private.mkdir()
    git(private, "init", "-q", "-b", "sources")
    git(private, "config", "user.name", "Private Test")
    git(private, "config", "user.email", "private@example.invalid")
    (private / "source.txt").write_text("Explicitly fictional private source fixture.\n")
    git(private, "add", "source.txt")
    git(private, "commit", "-qm", "Private source fixture")
    git(private, "remote", "add", "origin", str(remote))
    git(repo, "remote", "add", "archive", str(remote))
    monkeypatch.setenv("HOMALG_BACKUP_REMOTE", "archive")
    monkeypatch.setattr(
        publishing,
        "inbox_items",
        lambda repo: [
            {
                "id": "I-001",
                "status": "open",
                "body": "Fictional private ledger discussion",
                "scope": {"blueprint_nodes": ["Fixture2000.Thm_1"]},
            }
        ],
    )
    return repo, public, remote, private


def test_backup_archives_and_pushes_ledger_without_user_git_changes(ledger_backup: tuple) -> None:
    from homalg import lifecycle

    repo, public, remote, private = ledger_backup
    (repo / "user-staged.txt").write_text("User staged version.\n")
    git(repo, "add", "user-staged.txt")
    (repo / "user-staged.txt").write_text("User unstaged version.\n")
    (repo / "ledger-staged.txt").write_text("Unrelated ledger staging.\n")
    ledger_git(repo, "add", "ledger-staged.txt")
    ledger_staged = ledger_git(repo, "diff", "--cached", "--binary").stdout
    before = {name: (repo / ".git" / name).read_bytes() for name in ("HEAD", "index", "config")}
    user_head = git(repo, "rev-parse", "HEAD").stdout
    source_head = ledger_git(repo, "rev-parse", "HEAD").stdout
    public_head = git(public, "rev-parse", "main").stdout
    private_head = git(private, "rev-parse", "HEAD").stdout
    assert not ledger_git(repo, "remote").stdout

    result = lifecycle.backup(repo, now=NOW)

    assert git(repo, "rev-parse", "HEAD").stdout == user_head
    assert {name: (repo / ".git" / name).read_bytes() for name in before} == before
    assert result["backed_up"] and result["source"] == "ledger"
    assert git(public, "rev-parse", "main").stdout == public_head
    assert git(private, "rev-parse", "HEAD").stdout == private_head
    assert git(remote, "rev-parse", "sources").stdout == private_head
    assert ledger_git(repo, "rev-parse", "HEAD^").stdout == source_head
    assert ledger_git(repo, "diff", "--cached", "--binary").stdout == ledger_staged
    assert (
        git(remote, "rev-parse", "backup/alice/work").stdout
        == ledger_git(repo, "rev-parse", "HEAD").stdout
    )
    assert result["source_commit"] == ledger_git(repo, "rev-parse", "HEAD").stdout.decode().strip()
    assert (
        git(remote, "show", "backup/alice/work:ledger-only.txt").stdout
        == (repo / "ledger-only.txt").read_bytes()
    )
    assert (
        b"Fictional private ledger discussion"
        in git(
            remote, "show", "backup/alice/work:literature/Fixture2000/run-log/inbox/I-001.yaml"
        ).stdout
    )
    for name in ("user-staged.txt", "ledger-staged.txt", "literature/.private/source.txt"):
        assert git(remote, "cat-file", "-e", f"backup/alice/work:{name}", check=False).returncode


def test_ledger_backup_resolves_push_url_and_refuses_public_destination(
    ledger_backup: tuple,
) -> None:
    from homalg import lifecycle

    repo, public, _, _ = ledger_backup
    git(repo, "remote", "set-url", "--push", "archive", str(public))
    before = ledger_git(repo, "rev-parse", "HEAD").stdout
    with pytest.raises(ValueError, match="differ from the public origin"):
        lifecycle.backup(repo, now=NOW)
    assert ledger_git(repo, "rev-parse", "HEAD").stdout == before
    assert not (repo / "literature/Fixture2000/run-log").exists()


@pytest.mark.parametrize("destination", ["origin", "alias", "url"])
def test_ledger_backup_refuses_public_origin_with_separate_push_url(
    ledger_backup: tuple, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, destination: str
) -> None:
    from homalg import lifecycle

    repo, _, _, _ = ledger_backup
    public_push = tmp_path / "public-push.git"
    public_push.mkdir()
    git(public_push, "init", "--bare", "-q", "-b", "main")
    git(repo, "remote", "set-url", "--push", "origin", str(public_push))
    if destination == "alias":
        git(repo, "remote", "set-url", "--push", "archive", str(public_push))
        remote = "archive"
    else:
        remote = "origin" if destination == "origin" else str(public_push)
    monkeypatch.setenv("HOMALG_BACKUP_REMOTE", remote)
    source_head = ledger_git(repo, "rev-parse", "HEAD").stdout
    user_head = git(repo, "rev-parse", "HEAD").stdout
    user_index = (repo / ".git/index").read_bytes()

    with pytest.raises(ValueError, match="differ from the public origin"):
        lifecycle.backup(repo, now=NOW)

    assert not git(public_push, "for-each-ref", "--format=%(refname)").stdout
    assert ledger_git(repo, "rev-parse", "HEAD").stdout == source_head
    assert git(repo, "rev-parse", "HEAD").stdout == user_head
    assert (repo / ".git/index").read_bytes() == user_index
    assert not (repo / "literature/Fixture2000/run-log").exists()


def test_ledger_backup_refuses_multiple_push_destinations(ledger_backup: tuple) -> None:
    from homalg import lifecycle

    repo, public, remote, _ = ledger_backup
    git(repo, "remote", "set-url", "--push", "archive", str(remote))
    git(repo, "remote", "set-url", "--add", "--push", "archive", str(public))
    with pytest.raises(ValueError, match="exactly one push URL"):
        lifecycle.backup(repo, now=NOW)
    assert not (repo / "literature/Fixture2000/run-log").exists()


def test_ledger_backup_rejects_divergent_old_backup_without_force(ledger_backup: tuple) -> None:
    from homalg import lifecycle

    repo, _, remote, private = ledger_backup
    (repo / "old-user-backup.txt").write_text("Different user-Git backup history.\n")
    git(repo, "add", "old-user-backup.txt")
    git(repo, "commit", "-qm", "Legacy user-Git backup")
    git(repo, "push", "archive", "HEAD:refs/heads/backup/alice/work")
    old_remote = git(remote, "rev-parse", "backup/alice/work").stdout
    user_head = git(repo, "rev-parse", "HEAD").stdout
    user_index = (repo / ".git/index").read_bytes()

    result = lifecycle.backup(repo, now=NOW)

    assert result["backed_up"] is False
    assert result["reason"] == "non-fast-forward" and result["operation"] == "work-backup-push"
    assert result["source"] == "ledger"
    assert result["source_commit"] == ledger_git(repo, "rev-parse", "HEAD").stdout.decode().strip()
    assert git(remote, "rev-parse", "backup/alice/work").stdout == old_remote
    assert git(repo, "rev-parse", "HEAD").stdout == user_head
    assert (repo / ".git/index").read_bytes() == user_index
    # The independent private-source push really succeeded before the rejected work push.
    assert git(remote, "rev-parse", "sources").stdout == git(private, "rev-parse", "HEAD").stdout
    assert not (repo / ".archon-horizon/overlay/backup.json").exists()
    assert "retained local commits" in (repo / ".archon-horizon/overlay/hooks.log").read_text()


@pytest.mark.parametrize("invalid", ["file", "directory", "symlink"])
def test_backup_never_falls_back_from_invalid_ledger(publication: tuple, invalid: str) -> None:
    from homalg import lifecycle

    repo, _ = publication
    ledger = repo / ".archon-horizon/vcs/workspace.git"
    ledger.parent.mkdir(parents=True)
    if invalid == "file":
        ledger.write_text("not a Git repository")
    elif invalid == "directory":
        ledger.mkdir()
    else:
        ledger.symlink_to(repo / ".git", target_is_directory=True)
    before = git(repo, "rev-parse", "HEAD").stdout
    index = (repo / ".git/index").read_bytes()
    with pytest.raises((ValueError, RuntimeError)):
        lifecycle.backup(repo, now=NOW)
    assert git(repo, "rev-parse", "HEAD").stdout == before
    assert (repo / ".git/index").read_bytes() == index
    assert not (repo / "literature/Fixture2000/run-log").exists()


@pytest.mark.parametrize("name", ["GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"])
def test_backup_refuses_inherited_git_routing(
    ledger_backup: tuple, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    from homalg import lifecycle

    repo, _, _, _ = ledger_backup
    monkeypatch.setenv(name, str(repo / ".git/index"))
    with pytest.raises(ValueError, match=f"unredirected Git environment: {name}"):
        lifecycle.backup(repo, now=NOW)
    assert not (repo / "literature/Fixture2000/run-log").exists()


def advance_main(repo: Path, remote: Path, path: str, content: str) -> None:
    other = repo.parent / (repo.name + "-main-update")
    git(repo, "clone", "-q", str(remote), str(other))
    git(other, "config", "user.name", "Other")
    git(other, "config", "user.email", "other@example.invalid")
    (other / path).write_text(content)
    git(other, "add", path)
    git(other, "commit", "-qm", "Main update")
    git(other, "push", "-q", "origin", "main")


def test_sync_owned_conflict_keeps_work_and_regenerates(publication: tuple, monkeypatch) -> None:
    from homalg import lifecycle

    repo, remote = publication
    path = "HomAlg/Fixture2000/Thm_1.lean"
    text = (repo / path).read_text()
    advance_main(repo, remote, path, text + "\n-- Main amendment.\n")
    (repo / path).write_text(text + "\n-- Owner contribution.\n")
    git(repo, "add", path)
    git(repo, "commit", "-qm", "Owner update")
    monkeypatch.setattr(lifecycle, "require_idle", lambda *args: None)
    exported = []
    monkeypatch.setattr(lifecycle, "export_lean", lambda repo, key: exported.append(key))
    result = lifecycle.sync_main(repo, now=NOW)
    assert result["owned"] == ["Fixture2000"]
    assert path in result["resolved"]
    assert "Owner contribution" in (repo / path).read_text()
    assert "Main amendment" not in (repo / path).read_text()
    assert exported == ["Fixture2000"]
    assert not git(repo, "status", "--porcelain").stdout
    assert len(git(repo, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()) == 3


def test_sync_unowned_conflict_aborts_to_original_work(publication: tuple, monkeypatch) -> None:
    from homalg import lifecycle

    repo, remote = publication
    path = "HomAlg/Fixture2001/Thm_1.lean"
    text = (repo / path).read_text()
    advance_main(repo, remote, path, text + "\n-- Main amendment.\n")
    (repo / path).write_text(text + "\n-- Unowned local amendment.\n")
    git(repo, "add", path)
    git(repo, "commit", "-qm", "Unowned update")
    before = git(repo, "rev-parse", "HEAD").stdout
    monkeypatch.setattr(lifecycle, "require_idle", lambda *args: None)
    with pytest.raises(ValueError, match="outside owned"):
        lifecycle.sync_main(repo, now=NOW)
    assert git(repo, "rev-parse", "HEAD").stdout == before
    assert not git(repo, "status", "--porcelain").stdout
    assert git(repo, "rev-parse", "--verify", "MERGE_HEAD", check=False).returncode
