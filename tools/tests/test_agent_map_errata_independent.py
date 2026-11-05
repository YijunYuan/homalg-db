"""Independent map-profile guards, using fictional sources and provider evidence only."""

import copy
import hashlib
import json

import pytest
from test_agent_errata import NODE, RELATIVE, prepare_case
from test_agent_errata import case as case
from test_owner_decisions import git
from test_proof_map_errata import CORRECTED, ORIGINAL, prepare_map, reviews
from test_proof_map_errata import map_case as map_case

from homalg import agent_errata as errata
from homalg import proof_map_errata, review
from homalg.disputes import _docstring_marker
from homalg.headers import parse_header
from homalg.io import json_text
from homalg.nodeio import header_mapping, replace_header
from homalg.schemas import SchemaStore, load_yaml


def _reviewed(case):
    path, proposal = prepare_map(case)
    events = reviews(case, proposal)
    return path, proposal, events


def _replace_assessment(case, proposal, mutate):
    """Keep the fictional raw ACKs exact, so semantic checks must reject the lie."""
    report = case["report"].read_text()
    for number, original in enumerate(errata.blocks(report, errata.ASSESSMENT), 1):
        assessment = copy.deepcopy(original)
        mutate(assessment)
        report = report.replace(json_text(original), json_text(assessment))
        acknowledgement = json.dumps(
            {
                "kind": "agent-proof-erratum-ack",
                "proposal_sha256": errata.digest(errata._public(proposal)),
                "assessment_sha256": errata.digest(assessment),
            }
        )
        provider = case["provider"] / f"rollout-map-reviewer-{number}.jsonl"
        rows = [json.loads(line) for line in provider.read_text().splitlines()]
        rows[2]["payload"]["content"][0]["text"] = acknowledgement
        rows[3]["payload"]["last_agent_message"] = acknowledgement
        provider.write_text("".join(json.dumps(row) + "\n" for row in rows))
    case["report"].write_text(report)


def _assert_rejected_without_writes(case, path, events):
    paths = (case["repo"] / RELATIVE, case["report"])
    before = {item: item.read_bytes() for item in paths}
    with pytest.raises(ValueError):
        errata.adjudicate(case["repo"], NODE, snapshot=path, reviewer_events=events)
    assert all(item.read_bytes() == content for item, content in before.items())


@pytest.mark.parametrize("defect", ["classification", "argument", "hypotheses", "data", "proof"])
def test_matched_real_acks_cannot_approve_an_argument_or_different_class(map_case, defect):
    path, proposal, events = _reviewed(map_case)

    def mutate(assessment):
        if defect == "classification":
            assessment["classification"] = errata.CATEGORY
        elif defect == "proof":
            assessment["proof_approved"] = True
        else:
            assessment["impact"][defect] = "changed"

    _replace_assessment(map_case, proposal, mutate)
    _assert_rejected_without_writes(map_case, path, events)


@pytest.mark.parametrize("defect", ["registered_pdf", "pdf_bytes", "private_image", "profile"])
def test_current_map_proposal_cannot_survive_source_or_profile_drift(map_case, monkeypatch, defect):
    path, _, events = _reviewed(map_case)
    if defect == "registered_pdf":
        document = map_case["repo"] / "literature/Fixture2000/document.yaml"
        metadata = load_yaml(document.read_text())
        metadata["pdf"]["sha256"] = "f" * 64
        document.write_text(json_text(metadata))
    elif defect == "profile":
        profile = copy.deepcopy(proof_map_errata.PROFILE)
        profile["corrected"] += " A new argument."
        monkeypatch.setattr(proof_map_errata, "PROFILE", profile)
    else:
        private = map_case["private"] / (
            "fixture.pdf" if defect == "pdf_bytes" else "pages/page-0002.png"
        )
        private.write_bytes(private.read_bytes() + b" fictional changed source")
    _assert_rejected_without_writes(map_case, path, events)


def test_registered_pdf_must_match_profile_even_with_self_consistent_snapshot(map_case):
    _, proposal = prepare_map(map_case)
    forged = copy.deepcopy(proposal)
    forged["documents"]["Fixture2000"]["sha256"] = "f" * 64
    with pytest.raises(ValueError, match="exact registered source PDF"):
        errata._validate_proposal(forged, private=True)


@pytest.mark.parametrize("defect", ["confirmed", "human_lock", "statement_dispute", "cited"])
def test_exact_map_passage_never_overwrites_human_or_nonroutine_protection(map_case, defect):
    source = map_case["source"]
    metadata = header_mapping(source)
    if defect == "confirmed":
        metadata["dispute"].update(confirmed_by="fictional-owner", confirmed_on="2026-11-05")
    elif defect == "human_lock":
        metadata["fidelity"]["reviewed"] = {
            "kind": "human",
            "by": "fictional-owner",
            "on": "2026-11-05",
            "status": "satisfactory",
            "decl_hashes": {},
        }
    elif defect == "statement_dispute":
        metadata["dispute"]["kind"] = "statement"
    else:
        metadata["cited"] = {"source": {"kind": "mathlib"}}
    # Pure eligibility uses the same parsed metadata without needing an unrelated
    # fixture schema shape for the deliberately prohibited cited record.
    header = parse_header(source)
    start = source.index("```yaml node", header.start)
    end = source.index("```", start + len("```yaml node")) + 3
    changed = source[:start] + "```yaml node\n" + json_text(metadata) + "```" + source[end:]
    with pytest.raises(ValueError, match="unconfirmed theorem proof typo"):
        errata._eligible(changed, ORIGINAL, CORRECTED, category=proof_map_errata.CATEGORY)


@pytest.mark.parametrize("defect", ["argument", "statement", "anchor", "node", "duplicate"])
def test_whole_source_profile_refuses_semantic_and_anchor_changes(map_case, defect):
    source = map_case["source"]
    if defect == "argument":
        source = source.replace(ORIGINAL, ORIGINAL + "\nA different proof route is required.")
    elif defect == "statement":
        source = source.replace("## Statement", "## Statement\nAn extra hypothesis.")
    elif defect == "duplicate":
        source = source.replace(ORIGINAL, ORIGINAL + "\n" + ORIGINAL)
    else:
        metadata = header_mapping(source)
        if defect == "anchor":
            metadata["source"]["pages"] = [999]
        else:
            metadata["id"] = "CartanEilenberg1956.Prop_I_6_1"
        source = replace_header(source, metadata, SchemaStore(map_case["repo"] / "schema"))
    with pytest.raises(ValueError, match="source-bound profile"):
        errata._eligible(source, ORIGINAL, CORRECTED, category=proof_map_errata.CATEGORY)


def test_current_only_enablement_cannot_upgrade_a_membership_start(map_case, monkeypatch):
    policy = load_yaml((map_case["repo"] / errata.POLICY).read_text())
    old = copy.deepcopy(policy)
    old["routine_proof_errata"]["categories"] = [errata.CATEGORY]
    old["routine_proof_errata"].pop("map_label_profile_sha256")
    old_capability = errata._policy(json_text(old), NODE)
    assert set(old_capability) == {"enabled", "categories", "excluded_nodes"}
    with pytest.raises(ValueError, match="Trusted START"):
        errata._require_category(old_capability, NODE, proof_map_errata.CATEGORY)
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
    assert not map_case["calls"]


def test_map_adjudication_still_requires_fresh_ordinary_review_and_preserves_retry(map_case):
    path, _, events = _reviewed(map_case)
    repo, node = map_case["repo"], map_case["repo"] / RELATIVE
    errata.adjudicate(repo, NODE, snapshot=path, reviewer_events=events)
    assert not parse_header(node.read_text()).metadata["fidelity"].get("reviewed")
    identity = {
        "by": "fictional-map-final-reviewer",
        "session": "/root/ordinary_map_reviewer",
        "author_session": "/root/author",
    }
    with pytest.raises(ValueError, match="Session:|Latest source-fidelity"):
        review.review_fidelity(repo, NODE, **identity)
    with map_case["report"].open("a") as stream:
        for kind in ("source-fidelity", "honesty"):
            stream.write(
                f"\n## {kind} — fictional final review\n"
                "Session: /root/ordinary_map_reviewer\nAuthor-session: /root/author\n"
                "Status: satisfactory\nVerdict: Fictional complete statement and data checked.\n"
                "| Source | Lean |\n| --- | --- |\n"
                "| Fictional assumptions and construction | Same assumptions and construction |\n"
            )
    before_calls = len(map_case["calls"])
    review.review_fidelity(repo, NODE, **identity)
    assert [command[1] for command in map_case["calls"][before_calls:]] == ["build", "exe"]
    before = {p: p.read_bytes() for p in (node, map_case["report"])}
    assert errata.adjudicate(repo, NODE, snapshot=path, reviewer_events=events)["already_applied"]
    assert all(p.read_bytes() == content for p, content in before.items())


def test_reopened_map_history_keeps_its_bound_original_assessment(map_case):
    path, _, events = _reviewed(map_case)
    repo, node = map_case["repo"], map_case["repo"] / RELATIVE
    errata.adjudicate(repo, NODE, snapshot=path, reviewer_events=events)
    source = node.read_text()
    metadata = header_mapping(source)
    metadata.setdefault("dispute_history", []).append(copy.deepcopy(metadata["dispute"]))
    metadata["dispute"] = {"status": "open", "kind": "proof", "reason": "Fictional later issue"}
    source = replace_header(source, metadata, SchemaStore(repo / "schema"))
    source = _docstring_marker(
        source, metadata["decls"][0], "PROOF-DISPUTED: Fictional later issue"
    )
    node.write_text(source)
    errata.validate_resolution(repo, source)
    report = map_case["report"].read_text()
    original = errata.blocks(report, errata.ASSESSMENT)[0]
    changed = copy.deepcopy(original)
    changed["unique_typing_justification"] = "Changed fictional assessment."
    assert json_text(original) in report
    report = report.replace(json_text(original), json_text(changed), 1)
    map_case["report"].write_text(report)
    with pytest.raises(ValueError, match="assessment block"):
        errata.validate_resolution(repo, source)


def test_old_v4_three_field_membership_receipt_remains_historically_valid(case, monkeypatch):
    repo = case["repo"]
    policy = load_yaml((repo / errata.POLICY).read_text())
    old = copy.deepcopy(policy)
    old["routine_proof_errata"]["categories"] = [errata.CATEGORY]
    old["routine_proof_errata"].pop("map_label_profile_sha256")
    (repo / errata.POLICY).write_text(json_text(old))
    git(repo, "add", errata.POLICY)
    git(repo, "commit", "-qm", "fictional original V4 membership START")
    anchor = git(repo, "rev-parse", "HEAD")
    monkeypatch.setattr(errata, "_authority", lambda _repo: (anchor, True))
    meta = json.loads(case["meta"].read_text()) | {"start_sha": anchor}
    case["meta"].write_text(json_text(meta))
    record_path = repo / f".archon-horizon/draft-workspaces/{case['author_workspace']}/record.json"
    record = json.loads(record_path.read_text())
    record["promotion"]["source_after"] = anchor
    record_path.write_text(json_text(record))
    path, events, proposal = prepare_case(case)
    assert set(proposal["contract"]["policy"]) == {"enabled", "categories", "excluded_nodes"}
    errata.adjudicate(repo, NODE, snapshot=path, reviewer_events=events)
    source = (repo / RELATIVE).read_text()
    assert errata.validate_resolution(repo, source)
    # The exact historical source and report are now trusted, while a later
    # policy version enables the new route prospectively.
    (repo / errata.POLICY).write_text(json_text(policy))
    git(repo, "add", RELATIVE, errata.report_path(NODE), errata.POLICY)
    git(repo, "commit", "-qm", "fictional preserved old receipt and new prospective policy")
    later = git(repo, "rev-parse", "HEAD")
    assert errata.validate_resolution(repo, source, anchor=later)


def test_late_profile_change_rolls_back_owned_map_transaction(map_case, monkeypatch):
    path, _, events = _reviewed(map_case)
    originals = {p: p.read_bytes() for p in (map_case["repo"] / RELATIVE, map_case["report"])}
    original_write = errata.atomic_write_with_receipt
    injected = False

    def write_then_change(target, text, **kwargs):
        nonlocal injected
        receipt = original_write(target, text, **kwargs)
        if target == map_case["report"] and not injected:
            injected = True
            profile = copy.deepcopy(proof_map_errata.PROFILE)
            profile["proof_sha256"] = hashlib.sha256(b"fictional different proof").hexdigest()
            monkeypatch.setattr(proof_map_errata, "PROFILE", profile)
        return receipt

    monkeypatch.setattr(errata, "atomic_write_with_receipt", write_then_change)
    with pytest.raises(ValueError):
        errata.adjudicate(map_case["repo"], NODE, snapshot=path, reviewer_events=events)
    assert injected
    assert all(p.read_bytes() == content for p, content in originals.items())
    journals = map_case["repo"] / ".archon-horizon/cache/agent-errata-transactions"
    assert [json.loads(p.read_text())["state"] for p in journals.glob("*.json")] == ["rolled-back"]
