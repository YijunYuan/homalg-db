"""Fictional map-label adjudications; no real CE source decision is granted."""

import copy
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner
from test_agent_errata import NODE, RELATIVE, execution
from test_agent_errata import case as case
from test_owner_decisions import git

from homalg import agent_errata as errata
from homalg import proof_map_errata
from homalg.cli import cli
from homalg.headers import code_only, parse_header
from homalg.io import json_text
from homalg.nodeio import header_mapping, replace_header
from homalg.schemas import SchemaStore, load_yaml

ORIGINAL = "The new map $f''$ extends $f'$."
CORRECTED = "The new map $f'$ extends $f_0$."


@pytest.fixture
def map_case(case, monkeypatch):
    """Pin an explicitly fictional profile before the fictional native START."""
    repo = case["repo"]
    source = (
        (repo / RELATIVE)
        .read_text()
        .replace("Fictional typo: $a''\\in A$ maps into A''.", ORIGINAL)
    )
    (repo / RELATIVE).write_text(source)
    header = parse_header(source)
    profile = {
        "id": "fictional-map-labels-v1",
        "node": NODE,
        "source": header.metadata["source"],
        "pdf_sha256": hashlib.sha256((case["private"] / "fixture.pdf").read_bytes()).hexdigest(),
        "statement_sha256": hashlib.sha256(header.sections["Statement"].encode()).hexdigest(),
        "proof_sha256": hashlib.sha256(header.sections["Proof"].encode()).hexdigest(),
        "original": ORIGINAL,
        "corrected": CORRECTED,
    }
    monkeypatch.setattr(proof_map_errata, "PROFILE", profile)
    policy = load_yaml((repo / errata.POLICY).read_text())
    policy["routine_proof_errata"]["map_label_profile_sha256"] = errata.digest(profile)
    (repo / errata.POLICY).write_text(json_text(policy))
    git(repo, "add", RELATIVE, errata.POLICY)
    git(repo, "commit", "-qm", "fictional source-bound map profile and START")
    anchor = git(repo, "rev-parse", "HEAD")
    monkeypatch.setattr(errata, "_authority", lambda _repo: (anchor, True))
    meta = json.loads(case["meta"].read_text()) | {"start_sha": anchor}
    case["meta"].write_text(json_text(meta))
    worker = repo / f".archon-horizon/draft-workspaces/{case['author_workspace']}/record.json"
    record = json.loads(worker.read_text())
    record["promotion"]["source_after"] = anchor
    record["promotion"]["written_receipts"][RELATIVE]["sha256"] = hashlib.sha256(
        source.encode()
    ).hexdigest()
    worker.write_text(json_text(record))
    return case | {"source": source, "anchor": anchor, "profile": profile}


def prepare_map(case):
    path = Path("build/map-proposal.json")
    errata.prepare(
        case["repo"],
        NODE,
        original=ORIGINAL,
        corrected=CORRECTED,
        category=proof_map_errata.CATEGORY,
        author_workspace=case["author_workspace"],
        author_event=case["author_event"],
        out=path,
    )
    return path, json.loads((case["repo"] / path).read_text())


def reviews(case, proposal):
    events = []
    for number in (1, 2):
        actor = f"/root/map_source{number}"
        assessment = {
            "schema_version": 1,
            "kind": errata.ASSESSMENT,
            "proposal_sha256": errata.digest(errata._public(proposal)),
            "reviewer_session": actor,
            "classification": proof_map_errata.CATEGORY,
            "verdict": "unambiguous-local-typo",
            "unique_typing_justification": "Fictional map labels identify the unique antecedent.",
            "comparisons": [
                "Fictional complete source compared.",
                "Fictional types/data compared.",
            ],
            "impact": {
                "statement": "unchanged",
                "hypotheses": "unchanged",
                "data": "unchanged",
                "proof_route": "unchanged",
                "argument": "no_repair",
                "integration_amendment": "none",
            },
            "visual_sha256": proposal["visual_sha256"],
            "integration_amendment_sha256": errata.digest(None),
            "proof_approved": False,
        }
        with case["report"].open("a") as stream:
            stream.write(f"\n```homalg-{errata.ASSESSMENT}\n{json_text(assessment)}```\n")
        events.append(
            execution(
                case["repo"],
                case["provider"],
                case["owner"],
                f"map-reviewer-{number}",
                actor,
                "source-fidelity-reviewer",
                json.dumps(
                    {
                        "kind": "agent-proof-erratum-ack",
                        "proposal_sha256": errata.digest(errata._public(proposal)),
                        "assessment_sha256": errata.digest(assessment),
                    }
                ),
                datetime.now(UTC) + timedelta(seconds=2),
            )
        )
    return events


def test_fictional_map_adjudication_retains_literals_history_and_requires_review(map_case):
    path, proposal = prepare_map(map_case)
    events = reviews(map_case, proposal)
    result = errata.adjudicate(map_case["repo"], NODE, snapshot=path, reviewer_events=events)
    source = (map_case["repo"] / RELATIVE).read_text()
    before, after = parse_header(map_case["source"]), parse_header(source)
    assert after.sections["Statement"] == before.sections["Statement"]
    assert after.sections["Proof"] == before.sections["Proof"]
    assert code_only(source).split() == code_only(map_case["source"]).split()
    assert result["ordinary_review_required"] and not result["proof_approved"]
    assert after.metadata["dispute"]["reason"] == before.metadata["dispute"]["reason"]
    assert after.metadata.get("dispute_history", []) == before.metadata.get("dispute_history", [])
    assert after.metadata["dispute"]["resolution"]["kind"] == errata.KIND
    assert not after.metadata["dispute"].get("confirmed_by")
    assert not after.metadata["fidelity"].get("reviewed")
    assert errata.validate_resolution(map_case["repo"], source)
    assert errata.adjudicate(map_case["repo"], NODE, snapshot=path, reviewer_events=events)[
        "already_applied"
    ]
    assert (map_case["repo"] / RELATIVE).read_text() == source


@pytest.mark.parametrize(
    "change", ["statement", "proof", "duplicate", "already_corrected", "anchor"]
)
def test_profile_refuses_changed_or_ambiguous_source(map_case, change):
    source = map_case["source"]
    source = {
        "statement": source.replace("## Statement", "## Statement\nAltered hypothesis."),
        "proof": source.replace(ORIGINAL, ORIGINAL + " A new argument."),
        "duplicate": source.replace(ORIGINAL, ORIGINAL + " " + ORIGINAL),
        "already_corrected": source.replace(ORIGINAL, CORRECTED),
        "anchor": source,
    }[change]
    if change == "anchor":
        metadata = header_mapping(source)
        metadata["source"]["pages"] = [999]
        source = replace_header(source, metadata, SchemaStore(map_case["repo"] / "schema"))
    with pytest.raises(ValueError):
        errata._eligible(source, ORIGINAL, CORRECTED, category=proof_map_errata.CATEGORY)


@pytest.mark.parametrize(
    "correction", ["The new map $f'$ extends $f_1$.", "A new proof.", ORIGINAL]
)
def test_no_arbitrary_or_identity_replacement(map_case, correction):
    with pytest.raises(ValueError, match="source-bound profile"):
        errata._eligible(
            map_case["source"], ORIGINAL, correction, category=proof_map_errata.CATEGORY
        )


def test_membership_only_start_cannot_enable_map_category(map_case, monkeypatch):
    old = load_yaml((map_case["repo"] / errata.POLICY).read_text())
    old["routine_proof_errata"]["categories"] = [errata.CATEGORY]
    old["routine_proof_errata"].pop("map_label_profile_sha256")
    capability = errata._policy(json_text(old), NODE)
    with pytest.raises(ValueError, match="Trusted START"):
        errata._require_category(capability, NODE, proof_map_errata.CATEGORY)
    original_blob = errata.blob
    monkeypatch.setattr(
        errata,
        "blob",
        lambda repo, anchor, name, **kw: (
            json_text(old) if name == errata.POLICY else original_blob(repo, anchor, name, **kw)
        ),
    )
    with pytest.raises(ValueError, match="changed since native session start"):
        prepare_map(map_case)


@pytest.mark.parametrize("kind", ["missing", "same_child", "forged", "stale", "source_edit"])
def test_new_actual_reviews_and_current_source_required(map_case, kind):
    path, proposal = prepare_map(map_case)
    events = reviews(map_case, proposal)
    if kind == "missing":
        events.pop()
    elif kind == "same_child":
        events[1] = events[0]
    elif kind == "forged":
        events[0] = {"child_id": "invented", "turn_id": "invented"}
    elif kind == "stale":
        proposal["created_at"] = (datetime.now(UTC) + timedelta(days=1)).isoformat()
        (map_case["repo"] / path).write_text(json_text(proposal))
    else:
        (map_case["repo"] / RELATIVE).write_text(map_case["source"] + "\n-- later edit\n")
    with pytest.raises(ValueError):
        errata.adjudicate(map_case["repo"], NODE, snapshot=path, reviewer_events=events)
    assert (
        parse_header((map_case["repo"] / RELATIVE).read_text()).metadata["dispute"]["status"]
        == "open"
    )


def test_i6_1_and_profile_drift_refused(map_case):
    policy = load_yaml((map_case["repo"] / errata.POLICY).read_text())
    with pytest.raises(ValueError):
        errata._policy(json_text(policy), "CartanEilenberg1956.Prop_I_6_1")
    wrong = copy.deepcopy(policy)
    wrong["routine_proof_errata"]["map_label_profile_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        errata._policy(json_text(wrong), NODE)
    assert not SchemaStore(map_case["repo"] / "schema").validate(
        policy, "review-policy.schema.json"
    )
    wrong["routine_proof_errata"].pop("map_label_profile_sha256")
    assert SchemaStore(map_case["repo"] / "schema").validate(wrong, "review-policy.schema.json")


@pytest.mark.parametrize("category", [None, proof_map_errata.CATEGORY, "arbitrary-proof-rewrite"])
def test_cli_explicit_category_and_unchanged_default(repo, monkeypatch, category):
    calls = []

    def prepare(*args, **kwargs):
        calls.append(kwargs)
        return {"approval": False}

    monkeypatch.setattr(errata, "prepare", prepare)
    args = [
        "dispute",
        "prepare-proof-erratum",
        NODE,
        "--repo",
        str(repo),
        "--json",
        "--original",
        ORIGINAL,
        "--corrected",
        CORRECTED,
        "--author-workspace",
        "fictional",
        "--author-event",
        "child",
        "turn",
        "--out",
        "build/proposal.json",
    ]
    if category is not None:
        args += ["--category", category]
    result = CliRunner().invoke(cli, args)
    if category == "arbitrary-proof-rewrite":
        assert result.exit_code == 2 and not calls
    else:
        assert result.exit_code == 0, result.output
        assert calls[0]["category"] == (category or errata.CATEGORY)
