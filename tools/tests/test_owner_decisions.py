"""Fictional owner-direction relays preserve immutable trust and ordinary review gates."""

import copy
import json
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

from homalg.classify import approval_reasons
from homalg.documents import dump_metadata, read_document
from homalg.headers import parse_header
from homalg.io import json_text
from homalg.nodeio import header_mapping, replace_header
from homalg.owner_decisions import (
    KIND,
    POLICY,
    authorized_transition,
    blob,
    digest,
    evidence_projection,
    receipt_path,
    record,
    replay,
    source_binding,
    validate_resolution,
)
from homalg.schemas import SchemaStore, load_yaml
from homalg.scope import check_scope, human_fields_changed

NODE = "Fixture2000.Def_1"
NODE_PATH = "HomAlg/Fixture2000/Def_1.lean"
DECISION = "fictional-fixture-correction"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        [
            "git",
            "--git-dir",
            str(repo / ".archon-horizon/vcs/workspace.git"),
            "--work-tree",
            str(repo),
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def snapshot(repo: Path) -> str:
    git(repo, "add", "HomAlg", "literature", "horizon", "schema")
    git(repo, "commit", "-qm", "fictional test snapshot")
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def prepared(repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """All approvals here are fictional fixture data, never live owner directions."""
    import homalg.workspaces
    from homalg.disputes import _docstring_marker

    @contextmanager
    def isolated_lock(*args, **kwargs):
        yield lambda: None

    monkeypatch.setattr(homalg.workspaces, "_integration_lock", isolated_lock)
    path = repo / NODE_PATH
    source = path.read_text()
    metadata = header_mapping(source)
    metadata["dispute"] = {
        "status": "open",
        "kind": "statement",
        "reason": "Fictional fixture typo",
        "inbox": "I-0010",
        "opened_by": "fixture-author",
        "on": "2026-11-04",
    }
    metadata["fidelity"] = {
        "status": "deviates",
        "deviations": [
            {
                "kind": "erratum",
                "what": "Fictional fixture corrected wording",
                "why": "Fictional adopted owner direction, exercised only in tests",
            }
        ],
    }
    source = replace_header(source, metadata, SchemaStore(repo / "schema"))
    source = source.replace(
        "## Description",
        "## Statement (corrected)\n\nFictional corrected wording.\n\n## Description",
    )
    source = _docstring_marker(source, metadata["decls"][0], "STATEMENT-DISPUTED:")
    path.write_text(source)
    evidence = {
        "id": "I-0022",
        "provider": "local",
        "kind": "operator",
        "body": "Fictional fixture relay only",
        "author": "fixture-operator",
        "created_at": "2026-11-04T00:00:00Z",
    }
    item = repo / ".archon-horizon/inbox/local/items/I-0022.yaml"
    item.parent.mkdir(parents=True)
    item.write_text(dump_metadata(evidence))
    profile = {
        "id": DECISION,
        "node_id": NODE,
        "owner": "fictional-owner",
        "instruction": "Fictional instruction, no real approval",
        "binding_sha256": digest(
            source_binding(source, read_document(repo, "Fixture2000"), metadata["dispute"])
        ),
        "evidence": [{"id": "I-0022", "sha256": digest(evidence_projection(evidence))}],
    }
    (repo / "horizon").mkdir()
    (repo / POLICY).write_text(json_text({"schema_version": 1, "decisions": [profile]}))
    subprocess.run(
        ["git", "init", "--bare", "-q", str(repo / ".archon-horizon/vcs/workspace.git")], check=True
    )
    git(repo, "config", "user.name", "Fictional Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    snapshot(repo)
    return repo


def attest(repo: Path) -> dict:
    return record(
        repo, DECISION, by="fixture-operator", session="outer-fixture", attest_existing=True
    )


def apply(repo: Path) -> dict:
    return replay(repo, NODE, decision=DECISION, by="fixture-agent", session="native-fixture")


def task_scope(repo: Path, *extra: str) -> str:
    identifier = "Fixture2000.STMT.Unit_Def_1"
    path = repo / f".archon-horizon/tasks/items/{identifier}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        dump_metadata(
            {
                "id": identifier,
                "metadata": {"homalg": {"doc": "Fixture2000", "stage": "STMT"}},
                "write_set": {"files": [NODE_PATH, *extra]},
            }
        )
    )
    return identifier


def test_attestation_replay_preserves_history_and_requires_review(prepared: Path) -> None:
    repo = prepared
    original = parse_header((repo / NODE_PATH).read_text()).metadata["dispute"]
    receipt = attest(repo)
    # Tracked public receipts must match their source-ledger projection before
    # native workers are created; local private handoffs keep their default mode.
    path = repo / f"literature/Fixture2000/owner-decisions/{DECISION}.json"
    assert path.stat().st_mode & 0o777 == 0o644
    assert attest(repo) == receipt
    start = git(repo, "rev-parse", "HEAD")
    assert receipt["kind"] == "recorded-owner-instruction-attestation"
    assert receipt["attested_by"] == "fixture-operator"
    result = apply(repo)
    assert result["resolution"]["kind"] == KIND
    assert result["resolution"]["by"] == "fixture-agent"
    assert {key: value for key, value in result.items() if key not in {"status", "resolution"}} == {
        key: value for key, value in original.items() if key != "status"
    }
    assert "confirmed_by" not in result and "confirmed_on" not in result
    source = (repo / NODE_PATH).read_text()
    assert "STATEMENT-DISPUTED:" not in source
    assert "reviewed" not in parse_header(source).metadata["fidelity"]
    assert apply(repo) == result
    assert validate_resolution(repo, source, anchor=start)["decision_id"] == DECISION
    end = snapshot(repo)
    assert check_scope(repo, task_scope(repo), start, end) == []
    from homalg.review import _prepare_review

    with pytest.raises((ValueError, FileNotFoundError)):
        _prepare_review(
            repo,
            NODE,
            by="reviewer",
            session="independent",
            author_session="native-fixture",
            human=False,
            now=None,
        )


def test_same_session_mint_commit_does_not_create_authority(prepared: Path) -> None:
    start = git(prepared, "rev-parse", "HEAD")
    receipt = attest(prepared)
    apply(prepared)
    end = snapshot(prepared)
    relative = receipt_path({"id": DECISION, "node_id": NODE})
    violations = check_scope(prepared, task_scope(prepared, relative, POLICY), start, end)
    assert NODE_PATH in violations and relative in violations
    assert receipt["decision_id"] == DECISION
    with pytest.raises(ValueError):
        validate_resolution(prepared, (prepared / NODE_PATH).read_text(), anchor=start)


@pytest.mark.parametrize("variable", ["ARCHON_HORIZON_SESSION", "HOMALG_SESSION_MAIN_ROOT"])
def test_native_and_draft_cannot_issue_receipts(prepared: Path, monkeypatch, variable: str) -> None:
    monkeypatch.setenv(variable, "fictional-session")
    with pytest.raises(ValueError, match="cannot issue"):
        attest(prepared)


def test_intake_requires_explicit_attestation_and_exact_profile(prepared: Path) -> None:
    with pytest.raises(ValueError, match="Explicit"):
        record(prepared, DECISION, by="fixture-operator", session="outer-fixture")
    with pytest.raises(ValueError, match="explicitly authorized"):
        record(
            prepared,
            "new-unapproved-decision",
            by="fixture-operator",
            session="outer",
            attest_existing=True,
        )
    path = prepared / NODE_PATH
    path.write_text(path.read_text().replace("Fictional corrected wording.", "A new decision."))
    with pytest.raises(ValueError, match="differs from the authorized"):
        attest(prepared)


@pytest.mark.parametrize("field", ["body", "author", "id", "created_at"])
def test_evidence_spoof_is_rejected(prepared: Path, field: str) -> None:
    path = prepared / ".archon-horizon/inbox/local/items/I-0022.yaml"
    evidence = load_yaml(path.read_text())
    evidence[field] = "spoof"
    path.write_text(dump_metadata(evidence))
    with pytest.raises(ValueError, match="evidence changed"):
        attest(prepared)


def test_delivery_acknowledgements_do_not_invalidate_evidence(prepared: Path) -> None:
    path = prepared / ".archon-horizon/inbox/local/items/I-0022.yaml"
    evidence = load_yaml(path.read_text())
    evidence.update(read_by=["someone"], updated_at="2026-11-05T00:00:00Z")
    path.write_text(dump_metadata(evidence))
    attest(prepared)
    apply(prepared)


@pytest.mark.parametrize(
    "change",
    ["correction", "literal", "source", "pdf", "history", "reason", "target", "receipt", "profile"],
)
def test_bound_content_or_authority_changes_invalidate(prepared: Path, change: str) -> None:
    attest(prepared)
    start = git(prepared, "rev-parse", "HEAD")
    apply(prepared)
    path = prepared / NODE_PATH
    source = path.read_text()
    metadata = header_mapping(source)
    document = read_document(prepared, "Fixture2000")
    if change == "correction":
        source = source.replace("Fictional corrected wording.", "New correction.")
    elif change == "literal":
        source = source.replace(
            "A toy chain complex consists", "A changed literal statement consists"
        )
    elif change == "source":
        metadata["source"]["pages"] = [2]
    elif change == "pdf":
        document["pdf"] = {"page_offset": 1}
    elif change == "history":
        metadata["dispute_history"] = [copy.deepcopy(metadata["dispute"])]
    elif change == "reason":
        metadata["dispute"]["reason"] = "Different question"
    elif change == "target":
        metadata["id"] = "Fixture2000.Def_2"
    elif change in {"receipt", "profile"}:
        relative = POLICY if change == "profile" else metadata["dispute"]["resolution"]["receipt"]
        (prepared / relative).write_text((prepared / relative).read_text() + "\n")
    if change in {"source", "history", "reason", "target"}:
        source = replace_header(source, metadata, SchemaStore(prepared / "schema"))
    with pytest.raises(ValueError):
        validate_resolution(prepared, source, anchor=start, document=document)


@pytest.mark.parametrize(
    "lock",
    [
        {"kind": "human", "by": "fixture-human", "on": "2026-11-04"},
        {"by": "fixture-human", "on": "2026-11-04"},
    ],
)
def test_human_and_legacy_locks_are_never_replaced(prepared: Path, lock: dict) -> None:
    attest(prepared)
    path = prepared / NODE_PATH
    source = path.read_text()
    metadata = header_mapping(source)
    metadata["fidelity"]["reviewed"] = lock
    # Intentionally inject legacy metadata without schema-dependent normalization.
    opening = source.index("```yaml node") + len("```yaml node")
    closing = source.index("```", opening)
    source = source[:opening] + "\n" + dump_metadata(metadata) + source[closing:]
    path.write_text(source)
    with pytest.raises(ValueError, match="human fidelity lock"):
        apply(prepared)
    assert path.read_text() == source


def test_scope_and_pr_base_remain_authoritative(prepared: Path) -> None:
    attest(prepared)
    start = git(prepared, "rev-parse", "HEAD")
    before = (prepared / NODE_PATH).read_text()
    apply(prepared)
    after = (prepared / NODE_PATH).read_text()
    end = snapshot(prepared)

    def reader(anchor):
        def read(path):
            try:
                return blob(prepared, anchor, path)
            except ValueError:
                return None

        return read

    assert human_fields_changed(parse_header(before).metadata, parse_header(after).metadata)
    assert authorized_transition(
        before,
        after,
        read_document(prepared, "Fixture2000"),
        trusted=reader(start),
        current=reader(end),
    )
    assert approval_reasons([NODE_PATH], reader(start), reader(end)) == []
    assert approval_reasons([NODE_PATH], lambda path: None, reader(end)) == [
        f"untrusted-owner-decision-replay:{NODE_PATH}"
    ]
    relative = receipt_path({"id": DECISION, "node_id": NODE})
    assert approval_reasons([relative], lambda path: None, reader(end)) == [
        f"owner-decision-authority:{relative}"
    ]
    (prepared / POLICY).write_text((prepared / POLICY).read_text() + "\n")
    changed = snapshot(prepared)
    assert POLICY in check_scope(prepared, task_scope(prepared, POLICY), end, changed)


def test_draft_cannot_replay_or_widen_native_scope(prepared: Path, monkeypatch) -> None:
    attest(prepared)
    monkeypatch.setenv("HOMALG_SESSION_MAIN_ROOT", str(prepared))
    with pytest.raises(ValueError, match="Draft workers"):
        apply(prepared)
    monkeypatch.delenv("HOMALG_SESSION_MAIN_ROOT")
    monkeypatch.setenv("ARCHON_HORIZON_SESSION", "native-fixture")
    import homalg.workspaces

    monkeypatch.setattr(
        homalg.workspaces,
        "_native_owner",
        lambda repo: {"session": "native-fixture", "task": task_scope(repo)},
    )
    with pytest.raises(ValueError, match="exact node scope"):
        replay(
            prepared,
            "Fixture2000.Def_2",
            decision=DECISION,
            by="fixture-agent",
            session="native-fixture",
        )


def test_replay_history_only_accepts_exact_legitimate_reopening(prepared: Path) -> None:
    from homalg.owner_decisions import replay_history_error

    attest(prepared)
    apply(prepared)
    source = (prepared / NODE_PATH).read_text()
    old = parse_header(source).metadata
    reopened = copy.deepcopy(old)
    reopened["dispute_history"] = [old["dispute"]]
    reopened["dispute"] = {
        "status": "open",
        "kind": "statement",
        "reason": "Fictional new question",
    }
    assert not replay_history_error(old, reopened)
    forged = copy.deepcopy(reopened)
    forged["dispute_history"][0]["resolution"]["decision_id"] = "forged"
    assert replay_history_error(old, forged)
    assert replay_history_error({}, reopened)
    duplicate = copy.deepcopy(reopened)
    duplicate["dispute_history"].append(copy.deepcopy(reopened["dispute_history"][0]))
    assert replay_history_error(reopened, duplicate)
    after = replace_header(source, forged, SchemaStore(prepared / "schema"))
    reasons = approval_reasons([NODE_PATH], lambda path: source, lambda path: after)
    assert f"untrusted-owner-decision-history:{NODE_PATH}" in reasons


def test_exact_proof_typo_is_distinct_from_proof_route_or_proof_completion(prepared: Path) -> None:
    path = prepared / NODE_PATH
    source = path.read_text()
    metadata = header_mapping(source)
    metadata["dispute"]["kind"] = "proof"
    metadata["dispute"]["reason"] = "Fictional proof display typo"
    source = replace_header(source, metadata, SchemaStore(prepared / "schema"))
    source = source.replace("STATEMENT-DISPUTED:", "PROOF-DISPUTED:")
    source = source.replace(
        "## Description",
        r"""## Proof

Fictional literal proof: x + typo.

## Formalization notes

Only the displayed typo was previously adopted; no proof-route change.
\[
\tag{fixture, corrected}x + correction
\]

## Description""",
    )
    path.write_text(source)
    policy = json.loads((prepared / POLICY).read_text())
    profile = policy["decisions"][0]
    profile["binding_sha256"] = digest(
        source_binding(source, read_document(prepared, "Fixture2000"), metadata["dispute"])
    )
    artifact = prepared / "build/fictional-decision.json"
    artifact.parent.mkdir()
    artifact.write_text('{"fictional":true}\n')
    import hashlib

    profile["artifacts"] = [
        {
            "path": "build/fictional-decision.json",
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        }
    ]
    (prepared / POLICY).write_text(json_text(policy))
    snapshot(prepared)
    attest(prepared)
    result = apply(prepared)
    assert result["kind"] == "proof" and result["resolution"]["via"] == "erratum"
    assert (
        parse_header(path.read_text()).sections["Proof"] == parse_header(source).sections["Proof"]
    )
    assert "reviewed" not in parse_header(path.read_text()).metadata["fidelity"]
    changed = path.read_text().replace("x + correction", "x + new-route")
    with pytest.raises(ValueError, match="stale"):
        validate_resolution(prepared, changed)
    artifact.write_text("changed")
    with pytest.raises(ValueError, match="artifact changed"):
        apply(prepared)


def test_review_context_binds_receipt_and_profile(prepared: Path) -> None:
    from homalg.review import authoring_context_inputs

    attest(prepared)
    apply(prepared)
    context = authoring_context_inputs(prepared, [NODE])
    # Evidence is named relative to the workspace so it survives isolated checkouts.
    receipt = Path(receipt_path({"id": DECISION, "node_id": NODE}))
    receipt = receipt.relative_to(prepared) if receipt.is_absolute() else receipt
    assert POLICY in context["files"]
    assert receipt.as_posix() in context["files"]


def test_authority_cannot_be_replaced_after_start_even_with_new_commit(prepared: Path) -> None:
    attest(prepared)
    start = git(prepared, "rev-parse", "HEAD")
    apply(prepared)
    relative = receipt_path({"id": DECISION, "node_id": NODE})
    receipt = json.loads((prepared / relative).read_text())
    receipt["attested_by"] = "forged-agent"
    (prepared / relative).write_text(json_text(receipt))
    end = snapshot(prepared)
    assert relative in check_scope(prepared, task_scope(prepared, relative), start, end)
    with pytest.raises(ValueError, match="receipt absent or changed"):
        validate_resolution(prepared, (prepared / NODE_PATH).read_text(), anchor=start)


@pytest.fixture
def isolated_replay(prepared: Path, monkeypatch: pytest.MonkeyPatch):
    """Fictional replay with actual isolated layout, process identity and held lease."""
    import fcntl
    import hashlib
    import os
    import shutil
    import socket

    policy = json.loads((prepared / POLICY).read_text())
    artifacts = []
    for relative in (
        "build/fictional-decision.json",
        "literature/.private/Fixture2000/tex/page-0001.tex",
    ):
        path = prepared / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Fictional bound evidence: " + relative)
        artifacts.append(
            {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        )
    policy["decisions"][0]["artifacts"] = artifacts
    (prepared / POLICY).write_text(json_text(policy))
    snapshot(prepared)
    attest(prepared)
    apply(prepared)
    start = snapshot(prepared)
    isolated = prepared / ".archon-horizon/session-worktrees" / ("a" * 32)
    isolated.mkdir(parents=True)
    for directory in ("HomAlg", "literature", "schema", "horizon"):
        shutil.copytree(
            prepared / directory, isolated / directory, ignore=shutil.ignore_patterns(".private")
        )
    (isolated / "literature/.private").symlink_to(
        prepared / "literature/.private", target_is_directory=True
    )
    shutil.copytree(
        prepared / ".archon-horizon/vcs/workspace.git",
        isolated / ".archon-horizon/vcs/workspace.git",
    )
    run, session, task_id = "fictional-run", "fictional-session", "Fixture2000.STMT.1"
    directory = prepared / f".archon-horizon/runs/{run}/sessions/{session}"
    directory.mkdir(parents=True)
    (directory / "meta.json").write_text(
        json_text(
            {
                "role": "horizon",
                "status": "running",
                "task_id": task_id,
                "start_sha": start,
                "session_ledger": isolated.name,
            }
        )
    )
    (directory.parent.parent / "process.json").write_text(
        json_text({"pid": os.getpid(), "host": socket.gethostname()})
    )
    (prepared / "config.yaml").write_text("workspace: {session_ledger: true}\n")
    for mount in ("runs", "inbox"):
        (isolated / ".archon-horizon" / mount).symlink_to(
            prepared / ".archon-horizon" / mount, target_is_directory=True
        )
    for key, value in {
        "ROOT": str(isolated),
        "RUN": run,
        "SESSION": session,
        "SESSION_DIR": str(directory),
        "TASK": task_id,
    }.items():
        monkeypatch.setenv("ARCHON_HORIZON_" + key, value)
    monkeypatch.setenv("HOMALG_SESSION_MAIN_ROOT", str(prepared))
    lock = prepared / ".archon-horizon/locks/run-policy.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield isolated, prepared, directory, stream


def test_isolated_replay_validation_reads_authenticated_runtime(isolated_replay) -> None:
    isolated, control, directory, _ = isolated_replay
    source = (isolated / NODE_PATH).read_text()
    assert (isolated / ".archon-horizon/runs").is_symlink()
    assert (isolated / ".archon-horizon/inbox").is_symlink()
    assert (isolated / "literature/.private").is_symlink()
    assert not (isolated / "build/fictional-decision.json").exists()
    result = validate_resolution(isolated, source, evidence=True)
    assert result["decision_id"] == DECISION
    # Mutable canonical source is not the isolated session's trusted START input.
    (control / POLICY).write_text("not the isolated policy")
    (control / receipt_path({"id": DECISION, "node_id": NODE})).write_text("changed")
    assert validate_resolution(isolated, source, evidence=True) == result
    assert json.loads((directory / "meta.json").read_text())["status"] == "running"
    with pytest.raises(ValueError, match="Draft workers"):
        apply(isolated)
    with pytest.raises(ValueError, match="cannot issue"):
        attest(isolated)


@pytest.mark.parametrize(
    "target", ["meta", "inbox", "receipt", "policy", "build_artifact", "private_artifact"]
)
def test_isolated_replay_still_rejects_symlinked_evidence(isolated_replay, target: str) -> None:
    isolated, control, directory, _ = isolated_replay
    paths = {
        "meta": directory / "meta.json",
        "inbox": control / ".archon-horizon/inbox/local/items/I-0022.yaml",
        "receipt": isolated / receipt_path({"id": DECISION, "node_id": NODE}),
        "policy": isolated / POLICY,
        "build_artifact": control / "build/fictional-decision.json",
        "private_artifact": control / "literature/.private/Fixture2000/tex/page-0001.tex",
    }
    path = paths[target]
    outside = control.parent / ("fictional-redirect-" + target)
    outside.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        validate_resolution(isolated, (isolated / NODE_PATH).read_text(), evidence=True)


@pytest.mark.parametrize("change", ["pid", "status", "task", "lease", "root", "session_dir"])
def test_isolated_replay_requires_live_matching_native_owner(
    isolated_replay, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    import fcntl

    isolated, control, directory, stream = isolated_replay
    if change == "pid":
        path = directory.parent.parent / "process.json"
        data = json.loads(path.read_text())
        data["pid"] = 1
        path.write_text(json_text(data))
    elif change in {"status", "task"}:
        path = directory / "meta.json"
        data = json.loads(path.read_text())
        data["status" if change == "status" else "task_id"] = "fictional-other"
        path.write_text(json_text(data))
    elif change == "lease":
        fcntl.flock(stream, fcntl.LOCK_UN)
    elif change == "root":
        monkeypatch.setenv("HOMALG_SESSION_MAIN_ROOT", str(control.parent))
    else:
        monkeypatch.setenv("ARCHON_HORIZON_SESSION_DIR", str(isolated / "forged-session"))
    with pytest.raises(ValueError):
        validate_resolution(isolated, (isolated / NODE_PATH).read_text(), evidence=True)


@pytest.mark.parametrize(
    "target", ["policy", "receipt", "inbox", "build_artifact", "private_artifact"]
)
def test_isolated_replay_rejects_changed_bound_inputs(isolated_replay, target: str) -> None:
    isolated, control, _, _ = isolated_replay
    if target == "inbox":
        path = control / ".archon-horizon/inbox/local/items/I-0022.yaml"
        value = load_yaml(path.read_text())
        value["body"] = "Fictional forged decision"
        path.write_text(dump_metadata(value))
    elif target.endswith("_artifact"):
        relative = (
            "build/fictional-decision.json"
            if target == "build_artifact"
            else "literature/.private/Fixture2000/tex/page-0001.tex"
        )
        path = control / relative
        if target == "build_artifact":
            # A matching local copy cannot hide changed canonical historical evidence.
            shadow = isolated / relative
            shadow.parent.mkdir(parents=True)
            shadow.write_bytes(path.read_bytes())
        path.write_text("Fictional changed artifact")
    else:
        relative = POLICY if target == "policy" else receipt_path({"id": DECISION, "node_id": NODE})
        path = isolated / relative
        path.write_text(path.read_text() + "\n")
        # Even a later local commit cannot replace immutable START authority.
        snapshot(isolated)
    with pytest.raises(ValueError, match="changed"):
        validate_resolution(isolated, (isolated / NODE_PATH).read_text(), evidence=True)


def test_isolated_replay_rejects_symlinked_canonical_private_directory(isolated_replay) -> None:
    import shutil

    isolated, control, _, _ = isolated_replay
    private = control / "literature/.private"
    outside = control.parent / "fictional-private-redirect"
    shutil.move(private, outside)
    private.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        validate_resolution(isolated, (isolated / NODE_PATH).read_text(), evidence=True)


def test_dispute_validation_pipeline_supports_only_authenticated_isolation(isolated_replay) -> None:
    from homalg.validate import validate_repo

    isolated, _, directory, _ = isolated_replay
    findings, skipped, _ = validate_repo(isolated, ("Fixture2000",), only=("dispute-valid",))
    assert findings == [] and skipped == []
    path = directory / "meta.json"
    metadata = json.loads(path.read_text())
    metadata["status"] = "completed"
    path.write_text(json_text(metadata))
    findings, skipped, _ = validate_repo(isolated, ("Fixture2000",), only=("dispute-valid",))
    assert not skipped
    assert any(
        finding.rule == "dispute-valid" and "live Horizon session" in finding.message
        for finding in findings
    )


CORRECTED_NOTE = (
    "### Owner-adopted proof erratum\n\n"
    "Fictional corrected proof display:\n"
    "\\[\n\\tag{1, corrected}x=y\n\\]\n"
    "The rest of the literal Proof is unchanged."
)


@pytest.fixture
def pinned(repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fictional proof dispute whose adopted correction exists only in the profile."""
    import homalg.workspaces
    from homalg.disputes import _docstring_marker
    from homalg.owner_decisions import apply_correction

    @contextmanager
    def isolated_lock(*args, **kwargs):
        yield lambda: None

    monkeypatch.setattr(homalg.workspaces, "_integration_lock", isolated_lock)
    path = repo / "HomAlg/Fixture2000/Thm_1.lean"
    source = path.read_text()
    metadata = header_mapping(source)
    metadata["dispute"] = {
        "status": "open",
        "kind": "proof",
        "reason": "Fictional fixture proof slip",
        "inbox": "I-0011",
        "opened_by": "fixture-author",
        "on": "2026-11-05",
    }
    schemas = SchemaStore(repo / "schema")
    source = replace_header(source, metadata, schemas)
    source = _docstring_marker(source, metadata["decls"][0], "PROOF-DISPUTED:")
    path.write_text(source)
    evidence = {
        "id": "I-0023",
        "provider": "local",
        "kind": "operator",
        "body": "Fictional fixture relay only",
        "author": "fixture-operator",
        "created_at": "2026-11-05T00:00:00Z",
    }
    item = repo / ".archon-horizon/inbox/local/items/I-0023.yaml"
    item.parent.mkdir(parents=True)
    item.write_text(dump_metadata(evidence))
    profile = {
        "id": "fictional-pinned-correction",
        "node_id": "Fixture2000.Thm_1",
        "owner": "fictional-owner",
        "instruction": "Fictional instruction, no real approval",
        "evidence": [{"id": "I-0023", "sha256": digest(evidence_projection(evidence))}],
        "correction": {
            "deviation": {
                "kind": "erratum",
                "what": "Fictional corrected proof sentence",
                "why": "Fictional adopted owner direction, exercised only in tests",
            },
            "note": CORRECTED_NOTE,
        },
    }
    corrected = apply_correction(source, profile, schemas)
    profile["binding_sha256"] = digest(
        source_binding(corrected, read_document(repo, "Fixture2000"), metadata["dispute"])
    )
    (repo / "horizon").mkdir()
    (repo / POLICY).write_text(json_text({"schema_version": 1, "decisions": [profile]}))
    subprocess.run(
        ["git", "init", "--bare", "-q", str(repo / ".archon-horizon/vcs/workspace.git")], check=True
    )
    git(repo, "config", "user.name", "Fictional Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    snapshot(repo)
    return repo


def test_pinned_correction_is_attested_before_and_written_by_replay(pinned: Path) -> None:
    repo, node = pinned, "Fixture2000.Thm_1"
    path = repo / "HomAlg/Fixture2000/Thm_1.lean"
    before = path.read_text()
    receipt = record(
        repo,
        "fictional-pinned-correction",
        by="fixture-operator",
        session="outer-fixture",
        attest_existing=True,
    )
    # Attestation binds the corrected content but never edits the node itself.
    assert path.read_text() == before
    start = git(repo, "rev-parse", "HEAD")
    result = replay(
        repo, node, decision="fictional-pinned-correction", by="fixture-agent", session="native"
    )
    assert result["resolution"]["decision_id"] == receipt["decision_id"]
    source = path.read_text()
    header = parse_header(source)
    fidelity = header.metadata["fidelity"]
    assert fidelity["status"] == "deviates" and "reviewed" not in fidelity
    assert fidelity["deviations"][-1]["what"] == "Fictional corrected proof sentence"
    assert CORRECTED_NOTE in header.sections["Formalization notes"]
    assert header.sections["Proof"] == parse_header(before).sections["Proof"]
    assert "PROOF-DISPUTED:" not in source
    assert validate_resolution(repo, source, anchor=start)["decision_id"] == receipt["decision_id"]
    # Replaying again is a no-op; editing the pinned correction makes it stale.
    replay(repo, node, decision="fictional-pinned-correction", by="fixture-agent", session="native")
    assert path.read_text() == source
    # The outer hook's scope check accepts the replay within the unit's node scope.
    identifier = "Fixture2000.STMT.Unit_Thm_1"
    task_file = repo / f".archon-horizon/tasks/items/{identifier}.yaml"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    task_file.write_text(
        dump_metadata(
            {
                "id": identifier,
                "metadata": {"homalg": {"doc": "Fixture2000", "stage": "STMT"}},
                "write_set": {"files": ["HomAlg/Fixture2000/Thm_1.lean"]},
            }
        )
    )
    assert check_scope(repo, identifier, start, snapshot(repo)) == []
    tampered = source.replace("x=y", "x=z")
    with pytest.raises(ValueError, match="stale"):
        validate_resolution(repo, tampered, anchor=start)
