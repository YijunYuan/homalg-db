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
    assert str(prepared / POLICY) in context["files"]
    assert str(prepared / receipt_path({"id": DECISION, "node_id": NODE})) in context["files"]


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
