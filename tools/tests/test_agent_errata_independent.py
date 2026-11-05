"""Independent adversarial tests using explicitly fictional execution evidence."""

import copy
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pytest
from test_agent_errata import (
    CORRECTED,
    NODE,
    ORIGINAL,
    RELATIVE,
    add_integration_amendment,
    prepare_case,
)
from test_agent_errata import case as case
from test_owner_decisions import git

from homalg import agent_errata as errata
from homalg import native_review_evidence, review
from homalg.classify import approval_reasons
from homalg.disputes import _docstring_marker
from homalg.documents import dump_metadata
from homalg.headers import parse_header
from homalg.io import json_text
from homalg.nodeio import header_mapping, replace_header
from homalg.owner_decisions import blob
from homalg.schemas import SchemaStore, load_yaml
from homalg.status import compute_status, local_status
from homalg.workspaces import _protected


def _seconds(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


@dataclass
class FictionalReview:
    repo: Path
    provider: Path
    parent_file: Path
    child_file: Path
    raw: list[dict]
    parent: list[dict]
    owner: dict
    reference: dict
    acknowledgement: dict
    not_before: str

    def write(self) -> None:
        for path, records in ((self.parent_file, self.parent), (self.child_file, self.raw)):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(json.dumps(record) + "\n" for record in records))

    def check(self, *, forbidden_paths: set[str] | None = None) -> dict:
        return native_review_evidence.completed_ack(
            self.repo,
            self.owner,
            self.reference,
            acknowledgement=self.acknowledgement,
            not_before=self.not_before,
            forbidden_paths=forbidden_paths or {"/root", "/root/author"},
        )


@pytest.fixture
def fictional_review(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FictionalReview:
    """A completed fictional child, with no real source or real agent approvals."""
    repo = tmp_path / "repo"
    repo.mkdir()
    provider = tmp_path / "provider-sessions"
    child_file = provider / "2026/11/05/rollout-fictional-child.jsonl"
    owner = {"run": "0001", "session": "0001-horizon-Fixture2000.STMT.Unit_1"}
    parent_file = (
        repo
        / ".archon-horizon/runs"
        / owner["run"]
        / "sessions"
        / owner["session"]
        / "transcript.jsonl"
    )
    reference = {"child_id": "fictional-child", "turn_id": "fictional-review-turn"}
    acknowledgement = {
        "kind": "fictional-review-ack",
        "proposal_sha256": "a" * 64,
        "assessment_sha256": "b" * 64,
    }
    message = json.dumps(acknowledgement)
    born, started, completed = (
        "2026-11-05T10:00:00Z",
        "2026-11-05T10:02:00Z",
        "2026-11-05T10:02:01Z",
    )
    actor, parent_id, role = "/root/source_reviewer", "fictional-parent", "source-fidelity-reviewer"
    lineage = {
        "parent_thread_id": parent_id,
        "depth": 1,
        "agent_path": actor,
        "agent_role": role,
    }
    raw = [
        {
            "type": "session_meta",
            "timestamp": born,
            "payload": {
                "id": reference["child_id"],
                "timestamp": born,
                "parent_thread_id": parent_id,
                "forked_from_id": parent_id,
                "agent_path": actor,
                "agent_role": role,
                "cwd": str(repo),
                "source": {"subagent": {"thread_spawn": lineage}},
            },
        },
        {
            "type": "event_msg",
            "timestamp": started,
            "payload": {
                "type": "task_started",
                "turn_id": reference["turn_id"],
                "root_turn_id": "fictional-parent-turn",
                "started_at": _seconds(started),
            },
        },
        {
            "type": "response_item",
            "timestamp": completed,
            "payload": {
                "type": "message",
                "role": "assistant",
                "channel": "final",
                "content": [{"type": "output_text", "text": message}],
            },
        },
        {
            "type": "event_msg",
            "timestamp": completed,
            "payload": {
                "type": "task_complete",
                "turn_id": reference["turn_id"],
                "started_at": _seconds(started),
                "completed_at": _seconds(completed),
                "duration_ms": 1000,
                "last_agent_message": message,
            },
        },
    ]
    parent = [
        {"kind": "session_meta", "at": born, "data": {"session_id": parent_id}},
        {
            "kind": "subagent_start",
            "at": born,
            "data": {
                **lineage,
                "subagent_thread_id": reference["child_id"],
                "source": str(child_file),
            },
        },
        {
            "kind": "subagent_end",
            "at": completed,
            "data": {
                "subagent_thread_id": reference["child_id"],
                "source": str(child_file),
                "status": "completed",
                "duration_seconds": 1,
            },
        },
    ]
    result = FictionalReview(
        repo,
        provider,
        parent_file,
        child_file,
        raw,
        parent,
        owner,
        reference,
        acknowledgement,
        "2026-11-05T10:01:00Z",
    )
    result.write()
    monkeypatch.setattr(native_review_evidence, "provider_root", lambda: provider)
    return result


def test_real_shape_completed_turn_binds_all_six_evidence_rows(fictional_review) -> None:
    result = fictional_review.check()
    assert result["child_id"] == "fictional-child"
    assert result["turn_id"] == "fictional-review-turn"
    assert result["agent_path"] == "/root/source_reviewer"
    assert set(result["evidence_sha256"]) == {
        "session_meta",
        "dispatch",
        "start",
        "assistant",
        "completion",
        "parent_observation",
    }
    assert all(len(value) == 64 for value in result["evidence_sha256"].values())
    assert fictional_review.check() == result


@pytest.mark.parametrize("role", ["node-writer", "source-fidelity-reviewer"])
@pytest.mark.parametrize("aliases", ["key_only", "matching_both"])
def test_actual_completion_alias_shapes_preserve_the_same_opaque_identity(
    fictional_review, role, aliases
):
    fixture = fictional_review
    fixture.raw[0]["payload"]["agent_role"] = role
    fixture.raw[0]["payload"]["source"]["subagent"]["thread_spawn"]["agent_role"] = role
    fixture.parent[1]["data"]["agent_role"] = role
    observation = fixture.parent[2]["data"]
    observation["subagent_key"] = fixture.reference["child_id"]
    if aliases == "key_only":
        del observation["subagent_thread_id"]
    # Actual parent transcripts may repeat the same root identity after replay.
    fixture.parent.append(copy.deepcopy(fixture.parent[0]))
    fixture.write()
    result = native_review_evidence.completed_turn(
        fixture.repo,
        fixture.owner,
        fixture.reference,
        acknowledgement=fixture.acknowledgement if role == "source-fidelity-reviewer" else None,
        not_before=fixture.not_before,
        forbidden_paths={"/root"},
        role=role,
    )
    assert result["child_id"] == fixture.reference["child_id"]
    assert result["turn_id"] == fixture.reference["turn_id"]
    assert result["role"] == role
    assert len(result["evidence_sha256"]) == 6


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "renamed_key",
        "nickname",
        "actor_path",
        "provider_path",
        "different_key",
        "conflicting_key",
        "conflicting_thread",
        "empty_key",
        "null_key",
        "empty_thread",
        "null_thread",
        "nonscalar_key",
        "bool_key",
    ],
)
def test_completion_aliases_cannot_replace_or_contradict_the_opaque_child(fictional_review, defect):
    fixture = fictional_review
    observation = fixture.parent[2]["data"]
    child = observation.pop("subagent_thread_id")
    observation["subagent_key"] = child
    if defect == "missing":
        del observation["subagent_key"]
    elif defect == "renamed_key":
        observation["child_id"] = observation.pop("subagent_key")
    elif defect == "nickname":
        observation["subagent_key"] = "source_reviewer"
    elif defect == "actor_path":
        observation["subagent_key"] = "/root/source_reviewer"
    elif defect == "provider_path":
        observation["subagent_key"] = str(fixture.child_file)
    elif defect == "different_key":
        observation["subagent_key"] = "unrelated-child"
    elif defect == "conflicting_key":
        observation.update(subagent_thread_id=child, subagent_key="unrelated-child")
    elif defect == "conflicting_thread":
        observation["subagent_thread_id"] = "unrelated-child"
    elif defect == "empty_key":
        observation.update(subagent_thread_id=child, subagent_key="")
    elif defect == "null_key":
        observation.update(subagent_thread_id=child, subagent_key=None)
    elif defect == "empty_thread":
        observation["subagent_thread_id"] = ""
    elif defect == "null_thread":
        observation["subagent_thread_id"] = None
    elif defect == "nonscalar_key":
        observation["subagent_key"] = {"id": child}
    else:
        observation["subagent_key"] = True
    fixture.write()
    with pytest.raises(ValueError):
        fixture.check()


@pytest.mark.parametrize(
    "defect",
    [
        "wrong_source",
        "wrong_time",
        "wrong_duration",
        "wrong_status",
        "wrong_raw_role",
        "wrong_raw_parent",
        "wrong_raw_depth",
        "wrong_provider_id",
        "inherited_turn",
        "missing_raw_completion",
        "wrong_proposal",
        "duplicate_observation",
    ],
)
def test_key_only_completion_keeps_raw_identity_content_and_observation_guards(
    fictional_review, defect
):
    fixture = fictional_review
    observation = fixture.parent[2]["data"]
    observation["subagent_key"] = observation.pop("subagent_thread_id")
    if defect == "wrong_source":
        observation["source"] = str(fixture.provider / "other.jsonl")
    elif defect == "wrong_time":
        fixture.parent[2]["at"] = "2026-11-05T10:02:02Z"
    elif defect == "wrong_duration":
        observation["duration_seconds"] = 2
    elif defect == "wrong_status":
        observation["status"] = "running"
    elif defect == "wrong_raw_role":
        fixture.raw[0]["payload"]["agent_role"] = "honesty-reviewer"
    elif defect == "wrong_raw_parent":
        fixture.raw[0]["payload"]["parent_thread_id"] = "unrelated-parent"
    elif defect == "wrong_raw_depth":
        fixture.raw[0]["payload"]["source"]["subagent"]["thread_spawn"]["depth"] = 2
    elif defect == "wrong_provider_id":
        fixture.raw[0]["payload"]["id"] = "unrelated-child"
    elif defect == "inherited_turn":
        fixture.raw[1]["payload"]["root_turn_id"] = fixture.reference["turn_id"]
    elif defect == "missing_raw_completion":
        fixture.raw.pop()
    elif defect == "wrong_proposal":
        fixture.acknowledgement["proposal_sha256"] = "e" * 64
    else:
        fixture.parent.append(copy.deepcopy(fixture.parent[2]))
    fixture.write()
    with pytest.raises(ValueError):
        fixture.check()


def test_inherited_normalized_dispatch_does_not_replace_the_actual_child_dispatch(fictional_review):
    fixture = fictional_review
    observation = fixture.parent[2]["data"]
    observation["subagent_key"] = observation.pop("subagent_thread_id")
    # Real fork replay includes the ancestor's tool-call key, tagged with the
    # receiving child's thread ID. This row has no own role or parent lineage.
    fixture.parent.append(
        {
            "kind": "subagent_start",
            "at": fixture.raw[1]["timestamp"],
            "data": {
                "subagent_thread_id": fixture.reference["child_id"],
                "subagent_key": "call_inherited_parent_dispatch",
                "source": str(fixture.child_file),
                "codex_source": str(fixture.child_file),
            },
        }
    )
    fixture.write()
    assert fixture.check()["child_id"] == fixture.reference["child_id"]


def test_actual_dispatch_cannot_supply_contradictory_child_aliases(fictional_review):
    fixture = fictional_review
    fixture.parent[1]["data"]["subagent_key"] = "unrelated-child"
    fixture.write()
    with pytest.raises(ValueError):
        fixture.check()


@pytest.mark.parametrize(
    "defect",
    [
        "user_message_only",
        "wrong_proposal",
        "missing_start",
        "missing_completion",
        "missing_parent_observation",
        "different_raw_actor",
        "different_raw_parent",
        "inherited_root_turn",
        "replayed_old_payload_start",
        "different_observed_source",
        "duplicate_opaque_dispatch",
    ],
)
def test_native_receipts_reject_copied_incomplete_and_stale_evidence(fictional_review, defect):
    fixture = fictional_review
    if defect == "user_message_only":
        fixture.raw[2]["payload"]["role"] = "user"
    elif defect == "wrong_proposal":
        fixture.acknowledgement["proposal_sha256"] = "c" * 64
    elif defect == "missing_start":
        del fixture.raw[1]
    elif defect == "missing_completion":
        fixture.raw.pop()
    elif defect == "missing_parent_observation":
        fixture.parent.pop()
    elif defect == "different_raw_actor":
        fixture.raw[0]["payload"]["agent_path"] = "/root/author"
    elif defect == "different_raw_parent":
        fixture.raw[0]["payload"]["forked_from_id"] = "unrelated-parent"
    elif defect == "inherited_root_turn":
        fixture.raw[1]["payload"]["root_turn_id"] = fixture.reference["turn_id"]
    elif defect == "replayed_old_payload_start":
        # A real rollout may reserialize inherited events with a later envelope
        # timestamp. Its original started_at must still precede the proposal.
        old = _seconds("2026-11-05T10:00:30Z")
        fixture.raw[1]["payload"]["started_at"] = old
        fixture.raw[3]["payload"]["started_at"] = old
    elif defect == "different_observed_source":
        fixture.parent[2]["data"]["source"] = str(fixture.provider / "other.jsonl")
    elif defect == "duplicate_opaque_dispatch":
        duplicate = copy.deepcopy(fixture.parent[1])
        duplicate["data"]["agent_path"] = "/root/second_reviewer_alias"
        fixture.parent.append(duplicate)
    fixture.write()
    with pytest.raises(ValueError):
        fixture.check()


def test_actual_author_identity_cannot_review_under_another_requested_name(fictional_review):
    with pytest.raises(ValueError, match="independent"):
        fictional_review.check(forbidden_paths={"/root/source_reviewer"})


def test_provider_file_symlink_cannot_supply_review_evidence(fictional_review):
    original = fictional_review.child_file
    replacement = original.with_name("real-rollout.jsonl")
    original.rename(replacement)
    original.symlink_to(replacement)
    with pytest.raises(ValueError, match="provider session path"):
        fictional_review.check()


def test_inherited_assistant_ack_before_current_turn_is_not_its_completion(fictional_review):
    inherited = fictional_review.raw.pop(2)
    fictional_review.raw.insert(1, inherited)
    fictional_review.write()
    with pytest.raises(ValueError, match="assistant output"):
        fictional_review.check()


def _applied(case):
    out, events, proposal = prepare_case(case)
    result = errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)
    return out, events, proposal, result


def _public_read(repo, relative):
    path = repo / relative
    return path.read_text() if path.is_file() else None


def test_new_public_decision_cannot_authorize_itself_with_policy_alone(case):
    _applied(case)
    repo = case["repo"]
    with pytest.raises(ValueError, match="Draft integration"):
        _protected(case["source"].encode(), (repo / RELATIVE).read_bytes(), RELATIVE)
    assert not errata.authorized_transition(
        case["source"],
        (repo / RELATIVE).read_text(),
        trusted=lambda relative: blob(repo, case["anchor"], relative),
        current=lambda relative: _public_read(repo, relative),
        schemas=SchemaStore(repo / "schema"),
    )
    # An unused report block smuggled into an earlier base is not an already
    # adopted decision when that base's actual node still has the open dispute.
    assert not errata.authorized_transition(
        case["source"],
        (repo / RELATIVE).read_text(),
        trusted=lambda relative: (
            case["report"].read_text()
            if relative == errata.report_path(NODE)
            else blob(repo, case["anchor"], relative)
        ),
        current=lambda relative: _public_read(repo, relative),
        schemas=SchemaStore(repo / "schema"),
    )


@pytest.mark.parametrize("change", ["source_page", "pdf_identity"])
def test_historical_adjudication_cannot_retarget_source_identity(case, change):
    _applied(case)
    repo, source_path = case["repo"], case["repo"] / RELATIVE
    if change == "source_page":
        source = source_path.read_text()
        metadata = header_mapping(source)
        metadata["source"]["pages"] = [4]
        source_path.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))
    else:
        path = repo / "literature/Fixture2000/document.yaml"
        document = load_yaml(path.read_text())
        document["pdf"]["sha256"] = "c" * 64
        path.write_text(dump_metadata(document))
    with pytest.raises(ValueError, match="source anchor|PDF identity"):
        errata.validate_resolution(repo, source_path.read_text())


def test_fresh_ordinary_review_is_required_and_retry_preserves_its_lock(case):
    out, events, proposal, _ = _applied(case)
    repo, path = case["repo"], case["repo"] / RELATIVE
    identity = {
        "by": "fictional-reviewer",
        "session": "/root/ordinary_reviewer",
        "author_session": "/root/author",
    }
    assert not parse_header(path.read_text()).metadata["fidelity"].get("reviewed")
    initial_calls = list(case["calls"])
    with pytest.raises(ValueError, match="Session:|Latest source-fidelity"):
        review.review_fidelity(repo, NODE, **identity)
    assert case["calls"] == initial_calls
    with case["report"].open("a") as stream:
        for kind in ("source-fidelity", "honesty"):
            stream.write(
                f"\n## {kind} — separate fictional ordinary review\n"
                "Session: /root/ordinary_reviewer\nAuthor-session: /root/author\n"
                "Status: satisfactory\nVerdict: Fictional final statement and data inspected.\n"
                "| Source | Lean |\n| --- | --- |\n"
                "| Fictional hypothesis and construction | Same hypothesis and construction |\n"
            )
    review.review_fidelity(repo, NODE, **identity)
    assert [command[1] for command in case["calls"][len(initial_calls) :]] == ["build", "exe"]
    before = {item: item.read_bytes() for item in (path, case["report"])}
    metadata = parse_header(path.read_text()).metadata
    assert metadata["fidelity"]["reviewed"]["kind"] == "agent"
    compiled = {item["name"]: item for item in proposal["compiled"]["declarations"][NODE]}
    assert compute_status(
        metadata,
        {"local_status": local_status(metadata["decls"], compiled)},
        compiled,
        [],
    ) == ("stated", "statement-complete")
    assert errata.adjudicate(repo, NODE, snapshot=out, reviewer_events=events)["already_applied"]
    assert all(item.read_bytes() == content for item, content in before.items())


@pytest.mark.parametrize("late_change", ["image", "support", "task", "provider_completion"])
def test_late_change_after_report_write_rolls_back_owned_changes(case, monkeypatch, late_change):
    out, events, _ = prepare_case(case)
    repo, source = case["repo"], case["repo"] / RELATIVE
    original = {item: item.read_bytes() for item in (source, case["report"])}
    real_write = errata.atomic_write_with_receipt
    injected = False

    def write_then_change(path, content, **kwargs):
        nonlocal injected
        receipt = real_write(path, content, **kwargs)
        if path == case["report"] and not injected:
            injected = True
            if late_change == "image":
                image = case["private"] / "pages/page-0002.png"
                image.write_bytes(image.read_bytes() + b" changed by another editor")
            elif late_change == "support":
                support = repo / "HomAlg/Fixture2000/Def_1.lean"
                support.write_bytes(
                    support.read_bytes() + b"\n-- Changed supporting data context.\n"
                )
            elif late_change == "task":
                task = repo / f".archon-horizon/tasks/items/{case['owner']['task']}.yaml"
                record = load_yaml(task.read_text())
                record["write_set"]["files"].remove(errata.report_path(NODE))
                task.write_text(dump_metadata(record))
            else:
                child = case["provider"] / "rollout-reviewer-1.jsonl"
                records = [json.loads(line) for line in child.read_text().splitlines()]
                records[-1]["payload"]["last_agent_message"] = "changed completion"
                child.write_text("".join(json.dumps(record) + "\n" for record in records))
        return receipt

    monkeypatch.setattr(errata, "atomic_write_with_receipt", write_then_change)
    with pytest.raises(ValueError):
        errata.adjudicate(repo, NODE, snapshot=out, reviewer_events=events)
    assert injected
    assert all(path.read_bytes() == value for path, value in original.items())
    journals = repo / ".archon-horizon/cache/agent-errata-transactions"
    assert [json.loads(path.read_text())["state"] for path in journals.glob("*.json")] == [
        "rolled-back"
    ]


def test_foreign_node_edit_is_preserved_and_unfinished_retry_cannot_succeed(case, monkeypatch):
    out, events, _ = prepare_case(case)
    repo, source = case["repo"], case["repo"] / RELATIVE
    real_write = errata.atomic_write_with_receipt
    foreign = foreign_report = None

    def interfere(path, content, **kwargs):
        nonlocal foreign, foreign_report
        receipt = real_write(path, content, **kwargs)
        if path == source:
            foreign = path.read_bytes() + b"\n-- Fictional concurrent author's retained edit.\n"
            path.write_bytes(foreign)
            # Both now contain a valid-looking application but neither inode
            # can be rolled back over its unrelated editor's later change.
            foreign_report = case["report"].read_bytes() + b"\nFictional concurrent audit note.\n"
            case["report"].write_bytes(foreign_report)
        return receipt

    monkeypatch.setattr(errata, "atomic_write_with_receipt", interfere)
    with pytest.raises(ValueError):
        errata.adjudicate(repo, NODE, snapshot=out, reviewer_events=events)
    assert foreign is not None and source.read_bytes() == foreign
    assert foreign_report is not None and case["report"].read_bytes() == foreign_report
    journals = list((repo / ".archon-horizon/cache/agent-errata-transactions").glob("*.json"))
    assert len(journals) == 1
    assert json.loads(journals[0].read_text())["state"] == "recovery-required"
    monkeypatch.setattr(errata, "atomic_write_with_receipt", real_write)
    with pytest.raises(ValueError):
        errata.adjudicate(repo, NODE, snapshot=out, reviewer_events=events)
    assert source.read_bytes() == foreign


@pytest.mark.parametrize("change", ["assessment", "receipt"])
def test_reopened_dispute_still_protects_its_historical_receipt_and_assessments(case, change):
    _applied(case)
    repo, path = case["repo"], case["repo"] / RELATIVE
    source = path.read_text()
    metadata = header_mapping(source)
    metadata.setdefault("dispute_history", []).append(copy.deepcopy(metadata["dispute"]))
    metadata["dispute"] = {
        "status": "open",
        "kind": "proof",
        "reason": "Fictional later independent question, not a withdrawal of history",
    }
    reopened = replace_header(source, metadata, SchemaStore(repo / "schema"))
    reopened = _docstring_marker(reopened, metadata["decls"][0], "PROOF-DISPUTED: Later question")
    path.write_text(reopened)
    errata.validate_resolution(repo, reopened)
    report = case["report"].read_text()
    if change == "assessment":
        report = report.replace(
            "Fictional codomain fixes the target uniquely.", "Changed audit.", 1
        )
    else:
        marker = f"```homalg-{errata.RECEIPT}\n"
        start = report.index(marker)
        end = report.index("```", start + len(marker)) + 3
        report = report[:start] + report[end:]
    case["report"].write_text(report)
    with pytest.raises(ValueError):
        errata.validate_resolution(repo, reopened)


@pytest.mark.parametrize("defect", ["one_reviewer", "same_opaque_child"])
def test_two_real_reviews_cannot_be_replaced_by_names_or_repeated_events(case, defect):
    out, events, _ = prepare_case(case)
    events = events[:1] if defect == "one_reviewer" else [events[0], copy.deepcopy(events[0])]
    original = {path: path.read_bytes() for path in (case["repo"] / RELATIVE, case["report"])}
    with pytest.raises(ValueError):
        errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)
    assert all(path.read_bytes() == content for path, content in original.items())


def test_native_scope_revalidates_audited_start_and_committed_application(case):
    _, _, _, result = _applied(case)
    repo = case["repo"]
    git(repo, "add", RELATIVE, errata.report_path(NODE))
    git(repo, "commit", "-qm", "fictional adjudication boundary")
    until = git(repo, "rev-parse", "HEAD")
    metadata = json.loads(case["meta"].read_text())
    metadata["end_sha"] = until
    case["meta"].write_text(json_text(metadata))
    arguments = {
        "trusted": lambda relative: blob(repo, case["anchor"], relative),
        "current": lambda relative: _public_read(repo, relative),
        "schemas": SchemaStore(repo / "schema"),
        "native_repo": repo,
        "native_bounds": (case["owner"]["task"], case["anchor"], until),
    }
    after = (repo / RELATIVE).read_text()
    assert errata.authorized_transition(case["source"], after, **arguments)
    assert not errata.authorized_transition(
        case["source"],
        after,
        **(arguments | {"native_bounds": (case["owner"]["task"], "d" * 40, until)}),
    )
    journal = repo / f".archon-horizon/cache/agent-errata-transactions/{result['id']}.json"
    stored = json.loads(journal.read_text())
    stored["state"] = "prepared"
    journal.write_text(json_text(stored))
    assert not errata.authorized_transition(case["source"], after, **arguments)


@pytest.mark.parametrize("change", ["insert", "replace", "delete"])
def test_report_only_receipt_changes_remain_sensitive_in_public_pr(change):
    relative = errata.report_path(NODE)
    plain = "# Fictional report history\n"
    receipt = (
        f"```homalg-{errata.RECEIPT}\n"
        + json_text({"kind": errata.RECEIPT, "id": "a" * 64})
        + "```\n"
    )
    before = plain if change == "insert" else plain + receipt
    after = plain if change == "delete" else plain + receipt
    if change == "replace":
        after = after.replace("a" * 64, "b" * 64)
    reasons = approval_reasons(
        [relative],
        lambda name: before if name == relative else None,
        lambda name: after if name == relative else None,
    )
    assert reasons and any("erratum" in reason for reason in reasons)


def test_ordinary_report_append_does_not_change_typed_decision_authority():
    relative = errata.report_path(NODE)
    before = (
        f"```homalg-{errata.RECEIPT}\n"
        + json_text({"kind": errata.RECEIPT, "id": "a" * 64})
        + "```\n"
    )
    after = before + "\n## source-fidelity — fictional later independent assessment\n"
    assert (
        approval_reasons(
            [relative],
            lambda name: before if name == relative else None,
            lambda name: after if name == relative else None,
        )
        == []
    )


@pytest.mark.parametrize("ineligible", ["statement", "confirmed", "human_lock", "foundation"])
def test_prepare_cannot_reclassify_protected_or_nonroutine_evidence(case, ineligible):
    repo, path = case["repo"], case["repo"] / RELATIVE
    source = path.read_text()
    metadata = header_mapping(source)
    if ineligible == "statement":
        metadata["dispute"]["kind"] = "statement"
    elif ineligible == "confirmed":
        metadata["dispute"].update(confirmed_by="fictional-owner", confirmed_on="2026-11-05")
    elif ineligible == "human_lock":
        metadata["fidelity"]["reviewed"] = {
            "kind": "human",
            "by": "fictional-owner",
            "on": "2026-11-05",
            "status": "satisfactory",
            "decl_hashes": {},
        }
    else:
        metadata["fidelity"]["status"] = "foundation"
    path.write_text(replace_header(source, metadata, SchemaStore(repo / "schema")))
    before = path.read_bytes()
    with pytest.raises(ValueError, match="eligible|foundation|theorem|human|ordinary"):
        errata.prepare(
            repo,
            NODE,
            original=ORIGINAL,
            corrected=CORRECTED,
            author_workspace=case["author_workspace"],
            author_event=case["author_event"],
            out=Path("build/ineligible-proposal.json"),
        )
    assert path.read_bytes() == before and not case["calls"]
    assert not (repo / "build/ineligible-proposal.json").exists()


@pytest.mark.parametrize("forgery", ["human_original", "compiled_not_deferred", "unknown_owner"])
def test_matched_reviewer_acknowledgements_cannot_validate_a_malformed_proposal(case, forgery):
    out, events, proposal = prepare_case(case)
    public = copy.deepcopy(errata._public(proposal))
    if forgery == "human_original":
        for value in (proposal, public):
            value["original_dispute"].update(
                confirmed_by="fictional-owner", confirmed_on="2026-11-05"
            )
    elif forgery == "compiled_not_deferred":
        for value in (proposal, public):
            value["compiled"]["declarations"][NODE][0]["direct_sorry"] = False
    else:
        proposal["owner_adopted_correction"] = True
    (case["repo"] / out).write_text(json_text(proposal))
    report = case["report"].read_text()
    assessments = errata.blocks(report, errata.ASSESSMENT)
    for number, original_assessment in enumerate(assessments, 1):
        assessment = copy.deepcopy(original_assessment)
        assessment["proposal_sha256"] = errata.digest(public)
        report = report.replace(json_text(original_assessment), json_text(assessment))
        acknowledgement = json.dumps(
            {
                "kind": "agent-proof-erratum-ack",
                "proposal_sha256": errata.digest(public),
                "assessment_sha256": errata.digest(assessment),
            }
        )
        provider = case["provider"] / f"rollout-reviewer-{number}.jsonl"
        records = [json.loads(line) for line in provider.read_text().splitlines()]
        records[2]["payload"]["content"][0]["text"] = acknowledgement
        records[3]["payload"]["last_agent_message"] = acknowledgement
        provider.write_text("".join(json.dumps(record) + "\n" for record in records))
    case["report"].write_text(report)
    original = {path: path.read_bytes() for path in (case["repo"] / RELATIVE, case["report"])}
    with pytest.raises(ValueError):
        errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)
    assert all(path.read_bytes() == content for path, content in original.items())


def test_original_writer_and_actual_integrator_keep_separate_provenance(case):
    amendment = add_integration_amendment(case)
    author = errata._author(
        case["repo"], NODE, case["author_workspace"], case["author_event"], amendment["commit"]
    )
    assert author["author_session"] == "/root/author"
    assert author["execution"]["role"] == "node-writer"
    chain = author["integration_amendment"]
    assert chain["parent"] == case["anchor"]
    assert chain["integrator"]["actor"] == "/root"
    assert chain["integrator"]["role"] == "native-lead"
    assert chain["integrator"]["parent_id"] == "fictional-native-parent"
    assert chain["source_before"] == amendment["before"]
    assert chain["source_after"] == amendment["after"]
    assert chain["statement_dependencies_added"] == ["Fixture2000.Def_2"]


@pytest.mark.parametrize(
    "defect",
    [
        "normalized_child_copy",
        "raw_child_thread",
        "raw_child_metadata",
        "missing_own_start",
        "different_output",
        "failed_execution",
        "pre_delivery_execution",
        "duplicate_own_execution",
    ],
)
def test_integration_amendment_requires_original_parent_execution(case, defect):
    amendment = add_integration_amendment(case)
    raw = [json.loads(line) for line in amendment["raw"].read_text().splitlines()]
    parent = [json.loads(line) for line in amendment["normalized"].read_text().splitlines()]
    if defect == "normalized_child_copy":
        for row in parent[-2:]:
            row["data"]["subagent_thread_id"] = "fictional-inheriting-child"
            row["data"]["agent_path"] = "/root/copied_history"
    elif defect == "raw_child_thread":
        raw[-1]["payload"]["thread_id"] = "fictional-inheriting-child"
    elif defect == "raw_child_metadata":
        raw[0]["payload"]["parent_thread_id"] = "another-parent"
        raw[0]["payload"]["source"] = {"subagent": {"thread_spawn": {}}}
    elif defect == "missing_own_start":
        del raw[1]
    elif defect == "different_output":
        parent[-1]["data"]["content"] += "Not the provider's actual output.\n"
    elif defect == "failed_execution":
        raw[-1]["payload"]["item"]["exit_code"] = 1
    elif defect == "pre_delivery_execution":
        raw[-1]["payload"]["started_at_ms"] = _seconds(raw[0]["timestamp"]) * 1000
    else:
        raw.append(copy.deepcopy(raw[-1]))
    amendment["raw"].write_text("".join(json.dumps(row) + "\n" for row in raw))
    amendment["normalized"].write_text("".join(json.dumps(row) + "\n" for row in parent))
    with pytest.raises(ValueError):
        errata._author(
            case["repo"], NODE, case["author_workspace"], case["author_event"], amendment["commit"]
        )


@pytest.mark.parametrize(
    "change",
    ["statement", "proof", "lean_body", "metadata", "remove_dependency", "import", "dependency"],
)
def test_real_integrator_execution_cannot_authorize_an_unpaired_or_semantic_change(case, change):
    def transform(source):
        if change == "statement":
            return source.replace("## Statement\n", "## Statement\n\nAn additional premise.\n", 1)
        if change == "proof":
            return source.replace("Fictional typo:", "A different source argument:", 1)
        if change == "lean_body":
            return source.replace(":= by\n  sorry", ":= by\n  exact False.elim (by sorry)", 1)
        if change == "import":
            return source.replace("import HomAlg.Fixture2000.Def_2\n", "", 1)
        metadata = header_mapping(source)
        if change == "metadata":
            metadata["source"]["pages"] = [4]
        elif change == "remove_dependency":
            metadata["deps"]["statement"].pop(0)
        else:
            metadata["deps"]["statement"].remove("Fixture2000.Def_2")
        return replace_header(source, metadata, SchemaStore(case["repo"] / "schema"))

    amendment = add_integration_amendment(case, transform=transform)
    with pytest.raises(ValueError, match="amendment|dependency|import"):
        errata._author(
            case["repo"], NODE, case["author_workspace"], case["author_event"], amendment["commit"]
        )


def test_integrator_evidence_changed_after_report_write_aborts_application(case, monkeypatch):
    amendment = add_integration_amendment(case)
    out, events, _ = prepare_case(case, amendment["commit"])
    before = {path: path.read_bytes() for path in (case["repo"] / RELATIVE, case["report"])}
    real_write = errata.atomic_write_with_receipt

    def change_integrator_after_write(path, text, **kwargs):
        receipt = real_write(path, text, **kwargs)
        if path == case["report"]:
            raw = [json.loads(line) for line in amendment["raw"].read_text().splitlines()]
            raw[-1]["payload"]["item"]["id"] = "different-execution"
            amendment["raw"].write_text("".join(json.dumps(row) + "\n" for row in raw))
        return receipt

    monkeypatch.setattr(errata, "atomic_write_with_receipt", change_integrator_after_write)
    with pytest.raises(ValueError):
        errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)
    assert all(path.read_bytes() == content for path, content in before.items())


def test_reviewers_must_explicitly_assess_the_actual_integration_amendment(case):
    amendment = add_integration_amendment(case)
    _, _, proposal = prepare_case(case, amendment["commit"])
    assessments = errata.blocks(case["report"].read_text(), errata.ASSESSMENT)
    for assessment in assessments:
        assert assessment["integration_amendment_sha256"] == errata.digest(
            proposal["author"]["integration_amendment"]
        )
        assessment["impact"]["integration_amendment"] = "none"
        assessment["integration_amendment_sha256"] = errata.digest(None)
        with pytest.raises(ValueError):
            errata._assessment(assessment, proposal)


def test_import_amendment_does_not_mask_a_yaml_fence_inside_later_lean_data(repo):
    before = (repo / RELATIVE).read_text()
    before += '\ndef fictionalPayload : String := "```yaml node\nold value\n```"\n'
    metadata = header_mapping(before)
    metadata["deps"]["statement"].append("Fixture2000.Def_2")
    after = "import HomAlg.Fixture2000.Def_2\n" + replace_header(
        before, metadata, SchemaStore(repo / "schema")
    )
    after = after.replace("old value", "changed data")
    with pytest.raises(ValueError, match="beyond paired imports|retained metadata"):
        errata._import_amendment(before, after)


def _membership_source(repo, proof):
    """Replace only the fictional fixture's prose in memory, never a real source."""
    source = (repo / RELATIVE).read_text()
    metadata = header_mapping(source)
    metadata["fidelity"].pop("reviewed", None)
    metadata["dispute"] = {
        "status": "open",
        "kind": "proof",
        "reason": "Fictional complete-expression boundary check",
    }
    source = replace_header(source, metadata, SchemaStore(repo / "schema"))
    start = source.index("## Proof\n") + len("## Proof\n")
    end = source.index("\n## Description", start)
    return source[:start] + "\n" + proof + "\n" + source[end:]


@pytest.mark.parametrize(
    "proof",
    [
        f"Fictional setup: ${ORIGINAL}$, $c\\in C$; choose $a\\in A$.",
        f"$ \n {ORIGINAL} \n $",
        f"$$\n{ORIGINAL};\n$$",
        r"\(" + ORIGINAL + r"\)",
        r"\[ " + ORIGINAL + r". \]",
        ORIGINAL,
        ORIGINAL + ",",
        f"$x=0$ before ${ORIGINAL}$ after " + r"\(y=1\)",
        r"An escaped dollar \$5 precedes " + f"${ORIGINAL}$.",
        r"\\" + f"${ORIGINAL}$",
    ],
)
def test_complete_relation_accepts_only_declared_supported_positive_forms(repo, proof):
    assert errata._eligible(_membership_source(repo, proof), ORIGINAL, CORRECTED)["id"] == NODE


@pytest.mark.parametrize(
    "expression",
    [
        ORIGINAL + "''",
        ORIGINAL + "'",
        ORIGINAL + "b",
        ORIGINAL + "_1",
        ORIGINAL + " _1",
        ORIGINAL + r"^\prime",
        ORIGINAL + r" ^{\prime}",
        ORIGINAL + r"\prime",
        ORIGINAL + " ''",
        ORIGINAL + "\n ''",
        ORIGINAL + "′",
        ORIGINAL + "″",
        ORIGINAL + "α",
        ORIGINAL + "\u0301",
        ORIGINAL + r" \otimes C",
        ORIGINAL + r"\setminus B",
        "b" + ORIGINAL,
        "b " + ORIGINAL,
        "x_" + ORIGINAL,
        "\\" + ORIGINAL,
        "2" + ORIGINAL,
        ORIGINAL + r", b\in B",
        ORIGINAL + ";;",
    ],
)
def test_membership_substrings_cannot_stand_for_the_complete_source_relation(repo, expression):
    source = _membership_source(repo, "$" + expression + "$")
    with pytest.raises(ValueError, match="membership|relation|prime|complete"):
        errata._eligible(source, ORIGINAL, CORRECTED)


@pytest.mark.parametrize(
    "proof",
    [
        r"\$" + ORIGINAL + r"\$",
        r"\$" + ORIGINAL + "$",
        "$" + ORIGINAL + r"\$",
        "$" + ORIGINAL,
        r"\(" + ORIGINAL + "$",
        "$$" + ORIGINAL + "$",
        "$" + ORIGINAL + "$$",
        "$x$ " + ORIGINAL + " $y$",
        r"\(x\) " + ORIGINAL + r" \(y\)",
        "$x + " + r"\(" + ORIGINAL + r"\)$",
        f"${ORIGINAL}$ followed by an unclosed $x",
        f"${ORIGINAL}$ and ${ORIGINAL}$",
        f"${ORIGINAL}$ and ${ORIGINAL}''$",
    ],
)
def test_unbalanced_escaped_cross_span_and_duplicate_relations_fail_closed(repo, proof):
    with pytest.raises(ValueError, match="membership|relation|prime|complete"):
        errata._eligible(_membership_source(repo, proof), ORIGINAL, CORRECTED)
