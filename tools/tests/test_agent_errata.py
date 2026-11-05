"""Fictional routine agent adjudications; no real source decision is granted here."""

import copy
import json
import shutil
import subprocess
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from test_owner_decisions import git
from test_workflow import GOLDEN, ROOT, register

from homalg import agent_errata as errata
from homalg import leanexport, native_review_evidence, owner_decisions
from homalg.disputes import _docstring_marker
from homalg.documents import dump_metadata
from homalg.headers import code_only, parse_header
from homalg.io import json_text
from homalg.nodeio import header_mapping, replace_header
from homalg.schemas import SchemaStore, load_yaml

NODE = "Fixture2000.Thm_1"
RELATIVE = "HomAlg/Fixture2000/Thm_1.lean"
ORIGINAL = r"a''\in A"
CORRECTED = r"a''\in A''"


def execution(repo, provider, owner, child, actor, role, message, started):
    """Build explicit fictional provider records, including actual assistant output."""
    parent_id = "fictional-native-parent"
    birth, end = started - timedelta(seconds=1), started + timedelta(seconds=1)

    def stamp(value):
        return value.isoformat()

    reference = {"child_id": child, "turn_id": child + "-turn"}
    source = provider / f"rollout-{child}.jsonl"
    raw = [
        {
            "type": "session_meta",
            "timestamp": stamp(birth),
            "payload": {
                "id": child,
                "timestamp": stamp(birth),
                "cwd": str(repo),
                "agent_path": actor,
                "agent_role": role,
                "parent_thread_id": parent_id,
                "forked_from_id": parent_id,
                "source": {
                    "subagent": {
                        "thread_spawn": {
                            "parent_thread_id": parent_id,
                            "depth": 1,
                            "agent_path": actor,
                            "agent_role": role,
                        }
                    }
                },
            },
        },
        {
            "type": "event_msg",
            "timestamp": stamp(started),
            "payload": {
                "type": "task_started",
                "turn_id": reference["turn_id"],
                "root_turn_id": "root-turn",
                "started_at": int(started.timestamp()),
            },
        },
        {
            "type": "response_item",
            "timestamp": stamp(end),
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": message}],
            },
        },
        {
            "type": "event_msg",
            "timestamp": stamp(end),
            "payload": {
                "type": "task_complete",
                "turn_id": reference["turn_id"],
                "started_at": int(started.timestamp()),
                "duration_ms": 1000,
                "last_agent_message": message,
            },
        },
    ]
    provider.mkdir(exist_ok=True)
    source.write_text("".join(json.dumps(item) + "\n" for item in raw))
    parent = (
        repo / f".archon-horizon/runs/{owner['run']}/sessions/{owner['session']}/transcript.jsonl"
    )
    parent.parent.mkdir(parents=True, exist_ok=True)
    rows = (
        [json.loads(line) for line in parent.read_text().splitlines()]
        if parent.exists()
        else [
            {"kind": "session_meta", "data": {"session_id": parent_id}},
        ]
    )
    data = {
        "subagent_thread_id": child,
        "parent_thread_id": parent_id,
        "agent_path": actor,
        "agent_role": role,
        "source": str(source),
    }
    rows += [
        {"kind": "subagent_start", "at": stamp(birth), "data": data},
        {
            "kind": "subagent_end",
            "at": stamp(end),
            "data": data | {"status": "completed", "duration_seconds": 1},
        },
    ]
    parent.write_text("".join(json.dumps(item) + "\n" for item in rows))
    return reference


@pytest.fixture
def case(repo, monkeypatch):
    source = (repo / RELATIVE).read_text()
    source = source.replace(
        "## Proof\n", "## Proof\n\nFictional typo: $" + ORIGINAL + "$ maps into A''.\n"
    )
    source = source.replace("exact add_zero_natural c.degree", "sorry")
    source = source.replace("exact (degree_add_zero c).trans h", "sorry")
    metadata = header_mapping(source)
    metadata["dispute"] = {"status": "open", "kind": "proof", "reason": "Fictional membership typo"}
    source = replace_header(source, metadata, SchemaStore(repo / "schema"))
    source = _docstring_marker(
        source, metadata["decls"][0], "PROOF-DISPUTED: Fictional membership typo"
    )
    (repo / RELATIVE).write_text(source)
    record = register(repo)
    record["write_set"]["files"].append(errata.report_path(NODE))
    taskpath = repo / f".archon-horizon/tasks/items/{record['id']}.yaml"
    taskpath.write_text(dump_metadata(record))
    report = repo / errata.report_path(NODE)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Fictional source review history\n")
    (repo / "horizon").mkdir()
    shutil.copyfile(ROOT / errata.POLICY, repo / errata.POLICY)
    overlay = repo / ".archon-horizon/overlay"
    overlay.mkdir()
    (overlay / "plan-Fixture2000.json").write_text(json_text({"proofs": "deferred"}))
    private = repo / "literature/.private"
    private.mkdir()
    (private / ".git").mkdir()
    directory = private / "Fixture2000"
    (directory / "tex").mkdir(parents=True)
    (directory / "pages").mkdir()
    pdf = directory / "fixture.pdf"
    pdf.write_bytes(b"Fictional PDF bytes for input guards")
    pdf_hash = leanexport.file_fingerprint(pdf)["sha256"]
    docpath = repo / "literature/Fixture2000/document.yaml"
    doc = json.loads(docpath.read_text())
    doc["type"] = "book"
    doc["pdf"] = {
        "file": "fixture.pdf",
        "sha256": pdf_hash,
        "pages": 4,
        "page_offset": 0,
        "license": {"id": "CC0-1.0"},
    }
    docpath.write_text(json_text(doc))
    pages = {}
    for number in range(1, 5):
        tex = directory / "tex" / f"page-{number:04}.tex"
        tex.write_text(
            f"% source: fixture.pdf\n% pdf_page: {number}\n% retrieved: 2026-11-05\n"
            "% transcribed_by: fictional\nFictional text.\n"
        )
        (directory / "pages" / f"page-{number:04}.png").write_bytes(b"fictional image")
        sha = leanexport.file_fingerprint(tex)["sha256"]
        pages[f"{number:04}"] = {
            "status": "reviewed",
            "file_sha256": sha,
            "transcribed_by": {"session": "fictional-transcriber", "at": "2026-11-05T00:00:00Z"},
            "reviews": [
                {
                    "status": "satisfactory",
                    "by": "fictional-page-reviewer",
                    "at": "2026-11-05T00:00:01Z",
                    "file_sha256": sha,
                }
            ],
        }
    (directory / "transcription.yaml").write_text(
        json_text(
            {
                "schema_version": 1,
                "doc_key": "Fixture2000",
                "pdf_sha256": pdf_hash,
                "pages": pages,
            }
        )
    )
    ledger = repo / ".archon-horizon/vcs/workspace.git"
    subprocess.run(["git", "init", "--bare", "-q", str(ledger)], check=True)
    git(repo, "config", "user.email", "fictional@example.invalid")
    git(repo, "config", "user.name", "Fictional")
    git(
        repo,
        "add",
        "HomAlg",
        "horizon",
        "schema",
        "literature/Fixture2000",
        "literature/Fixture2001",
    )
    git(repo, "commit", "-qm", "fictional immutable start")
    anchor = git(repo, "rev-parse", "HEAD")
    owner = {
        "run": "0001",
        "session": "0001-horizon-fictional",
        "task": record["id"],
        "pid": 1,
        "process_start": "fictional",
    }
    meta = repo / f".archon-horizon/runs/{owner['run']}/sessions/{owner['session']}/meta.json"
    meta.parent.mkdir(parents=True)
    meta.write_text(json_text({"start_sha": anchor, "task_id": owner["task"]}))
    monkeypatch.setattr(errata, "_native_owner", lambda _repo: copy.deepcopy(owner))
    monkeypatch.setattr(errata, "_authority", lambda _repo: (anchor, True))
    provider = repo / "build/fictional-provider"
    provider.parent.mkdir()
    monkeypatch.setattr(native_review_evidence, "provider_root", lambda: provider)
    started = datetime.now(UTC) - timedelta(minutes=3)
    event = execution(
        repo,
        provider,
        owner,
        "fictional-author",
        "/root/author",
        "node-writer",
        "Fictional authored statement delivered.",
        started,
    )
    worker = "fictional-writer"
    worker_path = repo / f".archon-horizon/draft-workspaces/{worker}/record.json"
    worker_path.parent.mkdir(parents=True)
    worker_path.write_text(
        json_text(
            {
                "schema_version": 1,
                "id": worker,
                "source_root": str(repo),
                "status": "promoted",
                "native_owner": owner,
                "author": "/root/author",
                "files": [RELATIVE],
                "created_at": (started - timedelta(seconds=2)).isoformat(),
                "promotion": {
                    "state": "committed",
                    "author": "/root/author",
                    "source_after": anchor,
                    "finished_at": (started + timedelta(seconds=2)).isoformat(),
                    "native_owner": owner,
                    "files": [RELATIVE],
                    "written_receipts": {
                        RELATIVE: {
                            "sha256": leanexport.file_fingerprint(repo / RELATIVE)["sha256"]
                        },
                    },
                },
            }
        )
    )

    @contextmanager
    def integration(*args, **kwargs):
        with leanexport.workspace_lock(repo):
            yield lambda: None

    monkeypatch.setattr(errata, "_integration_lock", integration)
    raw = json.loads(GOLDEN.read_text())
    for item in leanexport.declaration_map(raw)["HomAlg." + NODE].values():
        item.update(direct_sorry=True, transitive_sorry=True)
    calls = []

    def run(_repo, command):
        calls.append(command)
        return "" if command[1] == "build" else json_text(raw)

    monkeypatch.setattr(leanexport, "run_tool", run)
    return {
        "repo": repo,
        "source": source,
        "node": NODE,
        "owner": owner,
        "anchor": anchor,
        "author_workspace": worker,
        "author_event": event,
        "provider": provider,
        "report": report,
        "calls": calls,
        "private": directory,
        "meta": meta,
    }


def prepare_case(case, integration_commit=None):
    out = Path("build/proposal.json")
    errata.prepare(
        case["repo"],
        NODE,
        original=ORIGINAL,
        corrected=CORRECTED,
        author_workspace=case["author_workspace"],
        author_event=case["author_event"],
        out=out,
        integration_commit=integration_commit,
    )
    proposal = json.loads((case["repo"] / out).read_text())
    events = []
    for number in (1, 2):
        actor = f"/root/source{number}"
        assessment = {
            "schema_version": 1,
            "kind": errata.ASSESSMENT,
            "proposal_sha256": errata.digest(errata._public(proposal)),
            "reviewer_session": actor,
            "classification": errata.CATEGORY,
            "verdict": "unambiguous-local-typo",
            "unique_typing_justification": "Fictional codomain fixes the target uniquely.",
            "comparisons": [
                "Fictional printed membership compared.",
                "Fictional compiled data compared.",
            ],
            "impact": {
                "statement": "unchanged",
                "hypotheses": "unchanged",
                "data": "unchanged",
                "proof_route": "unchanged",
                "argument": "no_repair",
                "integration_amendment": "reviewed-current-claim-and-data"
                if proposal["author"].get("integration_amendment")
                else "none",
            },
            "visual_sha256": proposal["visual_sha256"],
            "integration_amendment_sha256": errata.digest(
                proposal["author"].get("integration_amendment")
            ),
            "proof_approved": False,
        }
        with case["report"].open("a") as stream:
            stream.write(f"\n```homalg-{errata.ASSESSMENT}\n{json_text(assessment)}```\n")
        acknowledgement = {
            "kind": "agent-proof-erratum-ack",
            "proposal_sha256": errata.digest(errata._public(proposal)),
            "assessment_sha256": errata.digest(assessment),
        }
        events.append(
            execution(
                case["repo"],
                case["provider"],
                case["owner"],
                f"reviewer-{number}",
                actor,
                "source-fidelity-reviewer",
                json.dumps(acknowledgement),
                datetime.now(UTC) + timedelta(seconds=2),
            )
        )
    return out, events, proposal


def test_true_agent_adjudication_preserves_source_and_defers_ordinary_review(case):
    out, events, proposal = prepare_case(case)
    result = errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)
    after = (case["repo"] / RELATIVE).read_text()
    metadata = parse_header(after).metadata
    assert result["ordinary_review_required"] and not result["proof_approved"]
    assert code_only(after).split() == code_only(case["source"]).split()
    assert parse_header(after).sections["Proof"] == parse_header(case["source"]).sections["Proof"]
    assert metadata["dispute"]["reason"] == proposal["original_dispute"]["reason"]
    assert not metadata["dispute"].get("confirmed_by") and not metadata["fidelity"].get("reviewed")
    assert errata.validate_resolution(case["repo"], after)
    assert errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)[
        "already_applied"
    ]
    assert [command[1] for command in case["calls"]] == ["build", "exe"]


@pytest.mark.parametrize("which", ["source", "image", "tex", "report", "task"])
def test_stale_inputs_reject_before_applying(case, which):
    out, events, _ = prepare_case(case)
    targets = {
        "source": case["repo"] / RELATIVE,
        "image": case["private"] / "pages/page-0002.png",
        "tex": case["private"] / "tex/page-0002.tex",
        "report": case["report"],
        "task": case["repo"] / f".archon-horizon/tasks/items/{case['owner']['task']}.yaml",
    }
    target = targets[which]
    if which == "report":
        target.write_text(target.read_text().replace("unambiguous-local-typo", "unknown"))
    elif which == "task":
        record = load_yaml(target.read_text())
        record["objective"] = "A changed task objective"
        target.write_text(dump_metadata(record))
    else:
        target.write_bytes(target.read_bytes() + b" changed")
    before = (case["repo"] / RELATIVE).read_bytes()
    with pytest.raises((ValueError, KeyError)):
        errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)
    assert (case["repo"] / RELATIVE).read_bytes() == before


def test_native_transition_requires_current_audited_task_start_and_committed_application(case):
    out, events, _ = prepare_case(case)
    errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)
    after = (case["repo"] / RELATIVE).read_text()

    def current(name):
        return (case["repo"] / name).read_text()

    def trusted(name):
        return owner_decisions.blob(case["repo"], case["anchor"], name)

    arguments = {
        "trusted": trusted,
        "current": current,
        "schemas": SchemaStore(case["repo"] / "schema"),
        "native_repo": case["repo"],
    }
    bounds = (case["owner"]["task"], case["anchor"], "f" * 40)
    assert errata.authorized_transition(case["source"], after, native_bounds=bounds, **arguments)
    assert not errata.authorized_transition(case["source"], after, **arguments)
    for wrong in (("another-task", bounds[1], bounds[2]), (bounds[0], "a" * 40, bounds[2])):
        assert not errata.authorized_transition(
            case["source"], after, native_bounds=wrong, **arguments
        )
    journal = next(
        (case["repo"] / ".archon-horizon/cache/agent-errata-transactions").glob("*.json")
    )
    data = json.loads(journal.read_text())
    data["state"] = "prepared"
    journal.write_text(json_text(data))
    assert not errata.authorized_transition(
        case["source"], after, native_bounds=bounds, **arguments
    )


def test_public_new_transition_is_sensitive_but_historical_lean_work_is_not_re_adjudicated(case):
    from homalg.classify import approval_reasons

    out, events, _ = prepare_case(case)
    errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)
    path = case["repo"] / RELATIVE

    def current(name):
        return (case["repo"] / name).read_text()

    def trusted(name):
        return owner_decisions.blob(case["repo"], case["anchor"], name)

    assert f"untrusted-agent-erratum:{RELATIVE}" in approval_reasons([RELATIVE], trusted, current)
    # Historical lexical disposition does not certify or forbid future Lean work.
    after = path.read_text().replace("by\n  sorry", "by\n  exact add_zero_natural c.degree", 1)
    assert errata.validate_resolution(case["repo"], after)
    metadata = header_mapping(after)
    metadata["source"]["pages"] = [3]
    with pytest.raises(ValueError, match="source anchor"):
        errata.validate_resolution(
            case["repo"], replace_header(after, metadata, SchemaStore(case["repo"] / "schema"))
        )


@pytest.mark.parametrize(
    "bad", ["statement", "confirmed", "human", "legacy", "ambiguous", "argument"]
)
def test_routine_class_cannot_widen_to_other_authorities_or_argument_changes(case, bad):
    source = case["source"]
    metadata = header_mapping(source)
    if bad == "statement":
        metadata["dispute"]["kind"] = "statement"
    elif bad == "confirmed":
        metadata["dispute"].update(confirmed_by="fictional-human", confirmed_on="2026-11-05")
    elif bad in {"human", "legacy"}:
        metadata["fidelity"]["reviewed"] = {"by": "fictional-human", "on": "2026-11-05"}
        if bad == "human":
            metadata["fidelity"]["reviewed"]["kind"] = "human"
    if bad not in {"human", "legacy"}:
        source = replace_header(source, metadata, SchemaStore(case["repo"] / "schema"))
    else:
        # Deliberately exercise legacy metadata too, without relying on a strict writer.
        opening = source.index("```yaml node") + len("```yaml node")
        closing = source.index("```", opening)
        source = source[:opening] + "\n" + dump_metadata(metadata) + source[closing:]
    if bad == "ambiguous":
        source = source.replace(ORIGINAL, ORIGINAL + " and " + ORIGINAL)
    correction = "different argument" if bad == "argument" else CORRECTED
    with pytest.raises(ValueError):
        errata._eligible(source, ORIGINAL, correction)


def test_same_session_policy_enablement_and_explicit_exclusion_fail(case):
    policy = case["repo"] / errata.POLICY
    policy.write_text(policy.read_text().replace("enabled: true", "enabled: false"))
    with pytest.raises(ValueError, match="policy changed"):
        errata.prepare(
            case["repo"],
            NODE,
            original=ORIGINAL,
            corrected=CORRECTED,
            author_workspace=case["author_workspace"],
            author_event=case["author_event"],
            out=Path("build/refused.json"),
        )
    original_policy = owner_decisions.blob(case["repo"], case["anchor"], errata.POLICY)
    with pytest.raises(ValueError, match="does not authorize"):
        errata._policy(original_policy, "CartanEilenberg1956.Prop_I_6_1")


def test_ordinary_fidelity_is_still_independent_after_adjudication(case):
    from homalg.review import _prepare_review

    out, events, _ = prepare_case(case)
    errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)
    with pytest.raises(ValueError, match="provenance|report|Session|Author"):
        _prepare_review(
            case["repo"],
            NODE,
            by="fictional-reviewer",
            session="new-review",
            author_session="/root/author",
            human=False,
            now=None,
        )


def add_integration_amendment(case, *, transform=None):
    """Exact fictional shape of a native lead's later paired import/dependency fix."""
    import shlex

    repo = case["repo"]
    path = repo / RELATIVE
    before = path.read_text()
    metadata = header_mapping(before)
    metadata["deps"]["statement"].append("Fixture2000.Def_2")
    after = "import HomAlg.Fixture2000.Def_2\n" + replace_header(
        before, metadata, SchemaStore(repo / "schema")
    )
    if transform:
        after = transform(after)
    path.write_text(after)
    subject = "Fictional exactness statement dependency amendment"
    git(repo, "add", RELATIVE)
    git(repo, "commit", "-qm", subject)
    commit = git(repo, "rev-parse", "HEAD")
    parent_id, turn = "fictional-native-parent", "fictional-native-root-turn"
    command = ["/usr/bin/zsh", "-c", f'"$HORIZON_GIT" commit -m "{subject}" -- {RELATIVE}']
    output = f"[main {commit[:7]}] {subject}\n 1 file changed\n"
    now = datetime.now(UTC)
    born = now - timedelta(minutes=5)
    raw = [
        {
            "type": "session_meta",
            "timestamp": born.isoformat(),
            "payload": {
                "id": parent_id,
                "timestamp": born.isoformat(),
                "cwd": str(repo),
                "source": "cli",
            },
        },
        {
            "type": "event_msg",
            "timestamp": born.isoformat(),
            "payload": {
                "type": "task_started",
                "turn_id": turn,
                "root_turn_id": turn,
                "started_at": int(born.timestamp()),
            },
        },
        {
            "type": "event_msg",
            "timestamp": now.isoformat(),
            "payload": {
                "type": "item_completed",
                "thread_id": parent_id,
                "turn_id": turn,
                "started_at_ms": int(now.timestamp() * 1000),
                "completed_at_ms": int(now.timestamp() * 1000) + 1,
                "item": {
                    "type": "CommandExecution",
                    "id": "fictional-root-command",
                    "status": "completed",
                    "exit_code": 0,
                    "cwd": repo.as_uri(),
                    "command": command,
                    "aggregated_output": output,
                },
            },
        },
    ]
    raw_path = case["provider"] / f"rollout-{parent_id}.jsonl"
    raw_path.write_text("".join(json.dumps(row) + "\n" for row in raw))
    owner = case["owner"]
    normalized = (
        repo / f".archon-horizon/runs/{owner['run']}/sessions/{owner['session']}/transcript.jsonl"
    )
    with normalized.open("a") as stream:
        for row in (
            {
                "kind": "tool_call",
                "tool": "Bash",
                "at": now.isoformat(),
                "data": {"command": shlex.join(command)},
            },
            {
                "kind": "tool_result",
                "tool": "Bash",
                "at": now.isoformat(),
                "data": {"content": output, "exit_code": 0},
            },
        ):
            stream.write(json.dumps(row) + "\n")
    return {
        "commit": commit,
        "before": before,
        "after": after,
        "raw": raw_path,
        "normalized": normalized,
    }


def test_exact_integrator_amendment_preserves_real_writer_and_requires_two_assessments(case):
    amendment = add_integration_amendment(case)
    out, events, proposal = prepare_case(case, amendment["commit"])
    chain = proposal["author"]["integration_amendment"]
    assert proposal["author"]["author_session"] == "/root/author"
    assert chain["integrator"]["actor"] == "/root"
    assert chain["source_before"] == amendment["before"]
    assert chain["source_after"] == amendment["after"]
    assert chain["statement_dependencies_added"] == ["Fixture2000.Def_2"]
    assert errata.adjudicate(case["repo"], NODE, snapshot=out, reviewer_events=events)[
        "ordinary_review_required"
    ]
    assert errata.validate_resolution(case["repo"], (case["repo"] / RELATIVE).read_text())


@pytest.mark.parametrize(
    "proof",
    [
        ORIGINAL,
        "  " + ORIGINAL + "  ",
        ORIGINAL + ".",
        "$" + ORIGINAL + "$",
        "Given $" + ORIGINAL + "$ and $c\\in C$, continue.",
        "$x$ then $ " + ORIGINAL + ", $ afterwards.",
        "$$\n" + ORIGINAL + "\n$$",
        r"\( " + ORIGINAL + r" \)",
        r"\[ " + ORIGINAL + r"; \]",
    ],
)
def test_complete_membership_math_span_positive(case, proof):
    source = case["source"]
    previous = parse_header(source).sections["Proof"]
    assert errata._eligible(source.replace(previous, proof, 1), ORIGINAL, CORRECTED)


@pytest.mark.parametrize(
    "proof",
    [
        "$" + ORIGINAL + "''$",
        "$" + ORIGINAL + "b$",
        "$" + ORIGINAL + "α$",
        "$" + ORIGINAL + "′$",
        "$" + ORIGINAL + "″$",
        "$" + ORIGINAL + "_1$",
        "$" + ORIGINAL + r"^\prime$",
        "$" + ORIGINAL + r"\prime$",
        "$" + ORIGINAL + " ''$",
        "$" + ORIGINAL + r" _1$",
        "$" + ORIGINAL + r" ^{\prime}$",
        "$" + ORIGINAL + r" \otimes B$",
        "$b" + ORIGINAL + "$",
        "$b " + ORIGINAL + "$",
        "$x_" + ORIGINAL + "$",
        "$\\" + ORIGINAL + "$",
        "$x$ " + ORIGINAL + " $y$",
        "$" + ORIGINAL,
        "$$" + ORIGINAL + "$",
        "$" + ORIGINAL + "$$",
        r"\(" + ORIGINAL + r"\]",
        r"\$" + ORIGINAL + r"\$",
        "$" + ORIGINAL + r"\$",
        "$" + ORIGINAL + "$ and $" + ORIGINAL + "$",
    ],
)
def test_membership_prefix_and_unsupported_span_reject(case, proof):
    source = case["source"]
    previous = parse_header(source).sections["Proof"]
    with pytest.raises(ValueError, match="unique proof membership"):
        errata._eligible(source.replace(previous, proof, 1), ORIGINAL, CORRECTED)
