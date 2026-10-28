"""Session orchestration, progress accounting and individually confirmed escalation."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from homalg import lifecycle, publishing
from homalg.documents import dump_metadata, parse_metadata
from homalg.human import HumanApprovalRequired
from homalg.io import json_text
from homalg.runtime_state import document_state, overlay_nodes
from homalg.validate import Finding


@pytest.fixture
def task(repo: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    record = {
        "id": "T-Fixture2000-PROOF",
        "status": "queued",
        "write_set": {"files": ["HomAlg/Fixture2000/Thm_1.lean"]},
        "metadata": {"homalg": {"doc": "Fixture2000", "stage": "PROOF", "attempts": 0}},
    }
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(dump_metadata(record))

    def horizon(repo, *args):
        if args[:2] == ("task", "set"):
            current = parse_metadata(path.read_text())
            current["status"] = args[args.index("--status") + 1]
            path.write_text(dump_metadata(current))
        return "{}"

    monkeypatch.setattr(lifecycle.engine, "horizon", horizon)
    monkeypatch.setattr(publishing, "notify", lambda *args, **kwargs: "I-0001")
    return record


def test_three_stalled_sessions_block_and_progress_resets_attempts(
    repo: Path, task: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    notifications = []
    monkeypatch.setattr(publishing, "notify", lambda *args, **kw: notifications.append(kw))
    for attempt in range(1, 4):
        result = lifecycle.update_attempts(repo, task, {"complete": False}, False, str(attempt))
        assert result["attempts"] == attempt
        assert result["status"] == ("blocked" if attempt == 3 else "queued")
    assert len(notifications) == 1
    assert lifecycle.update_attempts(repo, task, {"complete": False}, False, "3") == result
    progressed = lifecycle.update_attempts(repo, task, {"complete": False}, True, "4")
    assert progressed == {"attempts": 0, "status": "blocked"}
    assert lifecycle.update_attempts(repo, task, {"complete": True}, True, "5")["status"] == "done"


def test_progress_counts_status_and_session_attempt_not_unrelated_prose(
    repo: Path, task: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = document_state(repo, "Fixture2000")
    prior = overlay_nodes(state)
    monkeypatch.setattr(
        lifecycle.scope, "ledger", lambda *args, **kw: SimpleNamespace(returncode=1)
    )
    monkeypatch.setattr(lifecycle.stages, "graph_comments", lambda *args: {})
    session = repo / "session-42"
    assert not lifecycle.progress_made(repo, task, state, prior, "a" * 40, session)
    prior["Fixture2000.Thm_1"]["local_status"] = "planned"
    assert lifecycle.progress_made(repo, task, state, prior, "a" * 40, session)
    prior = overlay_nodes(state)
    monkeypatch.setattr(
        lifecycle.stages,
        "graph_comments",
        lambda *args: {
            "Fixture2000.Thm_1": [
                {"body": "attempt: inspected obstruction", "session": session.name}
            ]
        },
    )
    assert lifecycle.progress_made(repo, task, state, prior, "a" * 40, session)


def test_scope_failure_short_circuits_every_following_step(
    repo: Path, task: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lifecycle.scope, "check_scope", lambda *args: ["taxonomy/tags.yaml"])
    monkeypatch.setattr(
        lifecycle, "private_after_session", lambda *args: pytest.fail("later step ran")
    )
    with pytest.raises(lifecycle.ScopeViolation) as caught:
        lifecycle.after_session(repo, task["id"], repo / "session", "a" * 40, "b" * 40)
    assert caught.value.paths == ["taxonomy/tags.yaml"]
    assert not (repo / "session").exists()


@pytest.mark.parametrize("build_fails", [False, True])
def test_after_session_runs_silent_ordered_pipeline_and_preserves_other_overlay(
    repo: Path, task: dict, monkeypatch: pytest.MonkeyPatch, capsys, build_fails: bool
) -> None:
    calls = []
    monkeypatch.setattr(lifecycle.scope, "check_scope", lambda *args: [])
    monkeypatch.setattr(lifecycle, "private_after_session", lambda *args: {"violations": []})

    def export(repo, key, path):
        calls.append("export")
        print("captured exporter diagnostic")
        if build_fails:
            raise RuntimeError("broken Lean declaration")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")

    def validate(repo, selected, **kwargs):
        assert kwargs["fast"] is build_fails and kwargs["no_build"] is not build_fails
        calls.append("validate")
        return [], [], {"nodes": 15}

    monkeypatch.setattr(lifecycle, "export_lean", export)
    monkeypatch.setattr(lifecycle, "validate_repo", validate)
    monkeypatch.setattr(lifecycle.stages, "evaluate", lambda *args, **kw: {"complete": True})
    monkeypatch.setattr(lifecycle, "progress_made", lambda *args: True)
    monkeypatch.setattr(lifecycle.planning, "plan", lambda *args, **kw: calls.append("plan") or {})

    def offline(*args, **kwargs):
        calls.append("publish")
        raise ValueError("missing local publishing configuration")

    monkeypatch.setattr(publishing, "publish_status", offline)
    monkeypatch.setattr(lifecycle, "backup", lambda *args, **kw: calls.append("backup") or {})
    overlay = repo / ".archon-horizon/overlay/HomAlg.json"
    overlay.parent.mkdir(parents=True, exist_ok=True)
    overlay.write_text(json_text({"Fixture2001.Def_1": {"marker": "preserved"}}))
    session = repo / "session"
    result = lifecycle.after_session(repo, task["id"], session, "a" * 40, "b" * 40)
    assert result["ok"] is not build_fails
    assert calls == ["export", "validate", "plan", "publish", "backup"]
    assert capsys.readouterr().out == ""
    assert "captured exporter diagnostic" in (session / "hooks.log").read_text()
    assert json.loads(overlay.read_text())["Fixture2001.Def_1"] == {"marker": "preserved"}
    report = json.loads((overlay.parent / "validate-Fixture2000.json").read_text())
    assert report["ok"] is not build_fails
    if build_fails:
        assert report["findings"][0]["rule"] == "lean-build"
        assert not result["evaluation"]["complete"]


def test_validation_errors_become_node_scoped_inbox_diagnostics(
    repo: Path, task: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = []
    monkeypatch.setattr(lifecycle.scope, "check_scope", lambda *args: [])
    monkeypatch.setattr(lifecycle, "export_lean", lambda *args: {})
    monkeypatch.setattr(
        lifecycle,
        "validate_repo",
        lambda *args, **kw: (
            [Finding("bridge", "error", "HomAlg/Fixture2000/Thm_1.lean", "bad bridge")],
            [],
            {},
        ),
    )
    monkeypatch.setattr(publishing, "notify", lambda *args, **kw: seen.append(kw))
    monkeypatch.setattr(lifecycle.stages, "evaluate", lambda *args, **kw: {"complete": False})
    monkeypatch.setattr(lifecycle, "progress_made", lambda *args: False)
    monkeypatch.setattr(lifecycle.planning, "plan", lambda *args, **kw: {})
    monkeypatch.setattr(publishing, "publish_status", lambda *args, **kw: {})
    monkeypatch.setattr(lifecycle, "backup", lambda *args, **kw: {})
    result = lifecycle.after_session(repo, task["id"], repo / "session", "a" * 40, "b" * 40)
    assert not result["ok"]
    assert seen[0] == {"rule": "bridge", "node": "Fixture2000.Thm_1", "task": task["id"]}


def test_log_archive_keeps_full_comments_and_scopes_records(repo: Path, monkeypatch) -> None:
    items = [
        {
            "id": "I-0001",
            "scope": {"blueprint_nodes": ["Fixture2000.Thm_1"]},
            "body": "Full private discussion",
            "comments": [{"body": "Entire reply"}],
        },
        {"id": "I-0002", "scope": {"blueprint_nodes": ["Fixture2001.Thm_1"]}, "body": "Other doc"},
    ]
    monkeypatch.setattr(publishing, "inbox_items", lambda repo: items)
    monkeypatch.setattr(
        publishing,
        "graph_comments",
        lambda *args: {
            "Fixture2000.Thm_1": [
                {"file": "C-1.md", "metadata": {"author": "alice"}, "body": "Detailed attempt"}
            ]
        },
    )
    destination = repo / "archive"
    paths = publishing.export_logs(repo, destination, "Fixture2000")
    assert len(paths) == 2
    assert "Entire reply" in (destination / paths[0]).read_text()
    assert "Detailed attempt" in (destination / paths[1]).read_text()
    assert not (destination / "literature/Fixture2001").exists()


@pytest.mark.parametrize(
    "items",
    [
        [],
        [{"id": "I-closed", "kind": "issue", "status": "closed"}],
        [
            {
                "id": "I-linked",
                "kind": "dispute",
                "status": "open",
                "comments": [{"body": "github-issue: https://example.invalid/issues/42"}],
            }
        ],
        [{"id": "I-local", "kind": "question", "status": "open", "comments": []}],
    ],
    ids=["empty-inbox", "closed-item", "already-published", "local-only-item"],
)
def test_escalation_without_candidates_needs_no_human_or_github(
    repo: Path, monkeypatch: pytest.MonkeyPatch, items: list[dict]
) -> None:
    monkeypatch.setenv("ARCHON_HORIZON_SESSION", "synthetic-empty-escalation-test")
    monkeypatch.setattr(publishing, "related_items", lambda *args: items)
    monkeypatch.setattr(
        lifecycle, "check_human_session", lambda *args: pytest.fail("empty escalation used guard")
    )
    monkeypatch.setattr(
        lifecycle, "Client", lambda *args: pytest.fail("empty escalation constructed GitHub client")
    )
    result = lifecycle.escalate(
        repo, "Fixture2000", confirm=lambda item: pytest.fail("empty escalation prompted")
    )
    assert result == {"candidates": 0, "published": []}
    assert not (repo / ".archon-horizon/overlay/escalated-Fixture2000.json").exists()


@pytest.mark.parametrize("kind", ["issue", "dispute", "document-error", "question"])
def test_escalation_with_candidates_still_requires_human_before_any_publication(
    repo: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    monkeypatch.setenv("ARCHON_HORIZON_SESSION", "synthetic-nonempty-escalation-test")
    item = {
        "id": "I-needs-human",
        "kind": kind,
        "status": "open",
        "body": "Synthetic unresolved item",
        "comments": [{"author": "human", "body": "escalate: github"}] if kind == "question" else [],
    }
    monkeypatch.setattr(publishing, "related_items", lambda *args: [item])
    monkeypatch.setattr(
        lifecycle, "Client", lambda *args: pytest.fail("unguarded escalation constructed client")
    )
    with pytest.raises(HumanApprovalRequired, match="requires a human"):
        lifecycle.escalate(
            repo,
            "Fixture2000",
            confirm=lambda item: pytest.fail("unguarded escalation prompted"),
        )
    assert not (repo / ".archon-horizon/overlay/escalated-Fixture2000.json").exists()


def test_escalation_individually_confirms_and_retries_local_record_without_duplicate_issue(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    items = [
        {
            "id": "I-0001",
            "kind": "issue",
            "status": "open",
            "body": "First issue",
            "scope": {"blueprint_nodes": ["Fixture2000.Thm_1"]},
        },
        {
            "id": "I-0002",
            "kind": "dispute",
            "status": "open",
            "body": "Second issue",
            "scope": {"blueprint_nodes": ["Fixture2000.Thm_1"]},
        },
    ]
    guards, created, prompted = [], [], []
    monkeypatch.setattr(lifecycle, "check_human_session", lambda *args: guards.append(True))
    monkeypatch.setattr(publishing, "related_items", lambda *args: items)

    class FakeGitHub:
        def gh(self, *args):
            if args[:2] == ("repo", "view"):
                return '{"nameWithOwner":"alice/homalg-db"}'
            assert args[:2] == ("issue", "create")
            body = Path(args[args.index("--body-file") + 1]).read_text()
            assert "First issue" in body and "#/node/Fixture2000/Thm_1" in body
            created.append(body)
            return "https://github.com/alice/homalg-db/issues/42"

    def broken_comment(*args):
        raise RuntimeError("local inbox unavailable")

    monkeypatch.setattr(lifecycle.engine, "horizon", broken_comment)
    with pytest.raises(RuntimeError, match="inbox unavailable"):
        lifecycle.escalate(
            repo,
            "Fixture2000",
            client=FakeGitHub(),
            confirm=lambda item: prompted.append(item["id"]) or item["id"] == "I-0001",
        )
    assert prompted == ["I-0001", "I-0002"]
    assert len(created) == 1
    monkeypatch.setattr(lifecycle.engine, "horizon", lambda *args: "{}")
    result = lifecycle.escalate(
        repo, "Fixture2000", client=FakeGitHub(), confirm=lambda item: False
    )
    assert len(created) == 1 and result["published"][0]["issue"] == 42
    assert len(guards) == 2
