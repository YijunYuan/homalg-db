"""Prospective agent adjudication of explicitly bounded local proof typos.

This records a new, bounded agent judgment. It is neither owner adoption nor a
human resolution, and never grants a fidelity lock or mathematical proof credit.
"""

import copy
import hashlib
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg import proof_map_errata, workflow
from homalg.disputes import _docstring_marker
from homalg.engine import task
from homalg.headers import parse_header
from homalg.io import (
    atomic_bytes,
    atomic_create,
    atomic_write,
    atomic_write_with_receipt,
    json_text,
)
from homalg.leanexport import compilation_inputs, file_fingerprint, workspace_lock
from homalg.native_review_evidence import completed_ack, completed_turn, parent_commit
from homalg.nodeio import header_mapping, node_path, replace_header
from homalg.owner_decisions import _authority, _safe_file, blob, digest
from homalg.review import authoring_context_inputs, authoring_source_fingerprint
from homalg.schemas import SchemaStore, load_yaml
from homalg.workspaces import _integration_lock, _native_owner, _read

KIND = "agent-routine-proof-erratum"
CATEGORY = "proof-membership-target-typo"
CATEGORIES = (CATEGORY, proof_map_errata.CATEGORY)
POLICY = "horizon/review-policy.yaml"
PROPOSAL = "routine-proof-erratum-proposal"
ASSESSMENT = "routine-proof-erratum-assessment"
RECEIPT = "routine-proof-erratum-receipt"
PUBLIC_PROPOSAL_FIELDS = {
    "schema_version",
    "kind",
    "node",
    "created_at",
    "contract",
    "category",
    "original",
    "corrected",
    "source",
    "author",
    "compiled",
    "source_pages",
    "original_dispute",
    "proof_approved",
    "visual_sha256",
    "documents",
    "inputs_sha256",
}


def _fields(value: Any, fields: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("Unexpected routine proof-erratum contract fields")


def report_path(node: str) -> str:
    key, local = node.split(".", 1)
    return f"literature/{key}/reviews/{local}.md"


def blocks(text: str, kind: str) -> list[dict]:
    result = []
    for encoded in re.findall(rf"(?ms)^```homalg-{re.escape(kind)}\n(.*?)^```\s*$", text):
        value = json.loads(encoded)
        if not isinstance(value, dict) or value.get("kind") != kind:
            raise ValueError("Invalid typed erratum report block")
        if value in result:
            raise ValueError("Duplicate typed erratum report block")
        result.append(value)
    return result


def _policy(text: str | None, node: str) -> dict:
    policy = load_yaml(text or "{}")
    if not isinstance(policy, dict):
        raise ValueError("Invalid trusted review policy")
    capability = policy.get("routine_proof_errata", {}) if isinstance(policy, dict) else {}
    fields = {"enabled", "categories", "excluded_nodes"}
    if isinstance(capability, dict) and "map_label_profile_sha256" in capability:
        fields.add("map_label_profile_sha256")
    _fields(capability, fields)
    categories = capability.get("categories")
    if (
        type(policy.get("schema_version")) is not int
        or policy["schema_version"] != 1
        or policy.get("allow_independent_agent_reviews") is not True
        or capability.get("enabled") is not True
        or not isinstance(categories, list)
        or not categories
        or not all(isinstance(value, str) and value in CATEGORIES for value in categories)
        or len(set(categories)) != len(categories)
        or (
            capability.get("map_label_profile_sha256") != digest(proof_map_errata.PROFILE)
            if proof_map_errata.CATEGORY in categories
            else "map_label_profile_sha256" in capability
        )
        or node in capability.get("excluded_nodes", [])
    ):
        raise ValueError("The trusted start/base policy does not authorize this routine class/node")
    return capability


def _require_category(capability: dict, node: str, category: str) -> None:
    """The category and exact profile must already belong to trusted START policy."""
    if (
        category not in CATEGORIES
        or category not in capability.get("categories", [])
        or node in capability.get("excluded_nodes", [])
        or (
            category == proof_map_errata.CATEGORY
            and (
                node != proof_map_errata.PROFILE["node"]
                or capability.get("map_label_profile_sha256") != digest(proof_map_errata.PROFILE)
            )
        )
    ):
        raise ValueError("Trusted START policy does not authorize this category/profile/node")


def _native_contract(repo: Path, node: str) -> tuple[dict, dict]:
    owner = _native_owner(repo)
    record = task(repo, owner["task"])
    metadata = parse_header(node_path(repo, node).read_text()).metadata
    info = record.get("metadata", {}).get("homalg", {})
    scope = set(record.get("write_set", {}).get("files", []))
    plan = _safe_file(repo, f".archon-horizon/overlay/plan-{metadata['doc']}.json")
    if (
        info.get("stage") != "STMT"
        or info.get("doc") != metadata["doc"]
        or str(node_path(repo, node).relative_to(repo)) not in scope
        or report_path(node) not in scope
        or json.loads(plan.read_text()).get("proofs") != "deferred"
    ):
        raise ValueError(
            "Routine adjudication requires exact native STMT scope with proofs deferred"
        )
    anchor, ledger = _authority(repo)
    if not ledger:
        raise ValueError("Native adjudication requires the immutable session source ledger")
    trusted = blob(repo, anchor, POLICY)
    if trusted != _safe_file(repo, POLICY).read_text():
        raise ValueError("Review policy changed since native session start")
    capability = _policy(trusted, node)
    return owner, {
        "task": workflow._contract(record),
        "start": anchor,
        "policy_sha256": digest(capability),
        "policy": capability,
        "proofs": "deferred",
    }


def _complete_relation(proof: str, original: str) -> bool:
    """Require one complete supported math span, never a target/subject prefix.

    This deliberately small grammar accepts only a bare complete Proof or one
    paired $, $$, \\(, \\[ span, with whitespace and one terminal punctuation mark.
    Unsupported compound/nested math is left for a different explicit route.
    """
    body = re.compile(re.escape(original) + r"\s*[,;.]?")
    if body.fullmatch(proof.strip()):
        return True
    pairs = {"$": "$", "$$": "$$", r"\(": r"\)", r"\[": r"\]"}
    closing = None
    start = 0
    found = False
    for match in re.finditer(r"\$\$|\$|\\(?:\(|\)|\[|\])", proof):
        prefix = proof[: match.start()]
        if (len(prefix) - len(prefix.rstrip("\\"))) % 2:
            continue
        token = match.group()
        if closing is None:
            if token not in pairs:
                return False
            closing, start = pairs[token], match.end()
        elif token != closing:
            return False
        else:
            if body.fullmatch(proof[start : match.start()].strip()):
                found = True
            closing = None
    return found and closing is None


def _eligible(source: str, original: str, corrected: str, *, category: str = CATEGORY) -> dict:
    metadata = parse_header(source).metadata
    dispute = metadata.get("dispute", {})
    reviewed = metadata.get("fidelity", {}).get("reviewed")
    if (
        dispute.get("status") != "open"
        or dispute.get("kind") != "proof"
        or any(key in dispute for key in ("confirmed_by", "confirmed_on", "resolution"))
        or (reviewed and reviewed.get("kind") != "agent")
        or metadata.get("fidelity", {}).get("status") == "foundation"
        or any(key in metadata for key in ("aux", "cited", "informal"))
        or metadata.get("kind") not in {"theorem", "lemma", "proposition", "corollary"}
        or not metadata.get("decls")
    ):
        raise ValueError("Only an unconfirmed theorem proof typo without human locks is eligible")
    sections = parse_header(source).sections
    if not sections.get("Statement") or not sections.get("Proof"):
        raise ValueError("Complete literal Statement and Proof are required")
    if category == proof_map_errata.CATEGORY:
        proof_map_errata.eligible(source, original, corrected)
        return metadata
    if category != CATEGORY:
        raise ValueError("Unsupported routine proof-erratum category")
    # Exactly one membership target, same subject and target base symbol. Prime
    # adornment is the only permitted lexical correction in this first class.
    grammar = r"([A-Za-z](?:'|\\prime)*\\in\s+)([A-Za-z])((?:'|\\prime)*)"
    old, new = re.fullmatch(grammar, original), re.fullmatch(grammar, corrected)
    if (
        not old
        or not new
        or old.group(1, 2) != new.group(1, 2)
        or old.group(3) == new.group(3)
        or sections["Proof"].count(original) != 1
        or not _complete_relation(sections["Proof"], original)
        or any(token in original + corrected for token in ("\n", "/-", "-/", "```"))
    ):
        raise ValueError("Correction must be one unique proof membership target prime typo")
    return metadata


def _visual(repo: Path, node: str) -> dict:
    from homalg.documents import read_document
    from homalg.literature import pdf_path, source_directory
    from homalg.transcription import status

    context = authoring_context_inputs(repo, [node])
    result = {}
    for key, numbers in context["source_pages"].items():
        document = read_document(repo, key)
        directory = source_directory(repo, key)
        pdf = pdf_path(repo, key)
        if file_fingerprint(pdf)["sha256"] != document["pdf"]["sha256"]:
            raise ValueError("Private PDF bytes differ from their registered identity")
        pages = status(repo, key, persist=False)["pages"]
        paths = [pdf, directory / "transcription.yaml"]
        for number in numbers:
            if pages[f"{number:04}"]["status"] != "reviewed":
                raise ValueError("Every selected source page requires current independent review")
            paths += [
                directory / "pages" / f"page-{number:04}.png",
                directory / "tex" / f"page-{number:04}.tex",
            ]
        for path in paths:
            if path.is_symlink() or path.resolve() != path or not path.is_file():
                raise ValueError("Current regular private PDF/images/TeX evidence is required")
            result[str(path)] = file_fingerprint(path)
    return result


def _capture(repo: Path, node: str) -> dict:
    # No nested flock: callers own workspace_lock or the native integration lock.
    return {
        "compilation": compilation_inputs(repo),
        "context": authoring_context_inputs(repo, [node]),
        "visual": _visual(repo, node),
    }


def _import_amendment(before: str, after: str) -> list[str]:
    """Allow only paired explicit HomAlg imports and statement-dependency additions."""
    old, new = header_mapping(before), header_mapping(after)
    previous, current = old["deps"]["statement"], new["deps"]["statement"]
    additions = [item for item in current if item not in previous]
    if not additions or [item for item in current if item in previous] != previous:
        raise ValueError("Integration amendment must only add statement dependencies")
    expected = copy.deepcopy(old)
    for position, node in enumerate(current):
        if node not in previous:
            expected["deps"]["statement"].insert(position, node)
    if expected != new:
        raise ValueError("Integration amendment changed unrelated or protected metadata")
    stripped = after
    for node in additions:
        line = f"import HomAlg.{node}\n"
        if (
            stripped.count(line) != 1
            or line in before
            or stripped.index(line) > parse_header(stripped).start
        ):
            raise ValueError("Each dependency addition needs one matching explicit leading import")
        stripped = stripped.replace(line, "", 1)

    def remove_yaml(text):
        header = parse_header(text)
        opening = text.index("```yaml node", header.start)
        closing = text.index("```", opening + len("```yaml node")) + 3
        return text[:opening] + "```yaml node\n```" + text[closing:]

    if remove_yaml(stripped) != remove_yaml(before):
        raise ValueError("Integration amendment changed source/proof/Lean beyond paired imports")
    from homalg.documents import dump_metadata

    opening = before.index("```yaml node", parse_header(before).start) + len("```yaml node")
    closing = before.index("```", opening)
    expected_source = (
        before[:opening] + "\n" + dump_metadata(expected).rstrip() + "\n" + before[closing:]
    )
    if authoring_source_fingerprint(stripped) != authoring_source_fingerprint(expected_source):
        raise ValueError("Integration amendment altered retained metadata/comment content")
    return additions


def _author(
    repo: Path,
    node: str,
    worker: str,
    event: dict[str, str],
    integration_commit: str | None = None,
) -> dict:
    record = _read(repo, worker)
    promotion = record.get("promotion", {})
    relative = str(node_path(repo, node).relative_to(repo))
    owner = record.get("native_owner")
    if (
        not owner
        or record.get("status") != "promoted"
        or promotion.get("state") != "committed"
        or relative not in record.get("files", [])
        or promotion.get("author") != record.get("author")
        or promotion.get("native_owner") != owner
        or relative not in promotion.get("files", [])
    ):
        raise ValueError("Original author requires an actual collected native workspace")
    committed = blob(repo, promotion.get("source_after", ""), relative)
    if (
        not committed
        or promotion.get("written_receipts", {}).get(relative, {}).get("sha256")
        != hashlib.sha256(committed.encode()).hexdigest()
    ):
        raise ValueError("Collected author commit lacks its exact owned write receipt")
    from homalg.owner_decisions import _git

    _git(repo, "merge-base", "--is-ancestor", promotion["source_after"], "HEAD")
    amendment = None
    delivered = committed
    if integration_commit is not None:
        if not re.fullmatch(r"[0-9a-f]{40,64}", integration_commit):
            raise ValueError("Integration amendment requires an exact immutable commit")
        parents = _git(repo, "show", "-s", "--format=%P", integration_commit).strip().split()
        if parents != [promotion["source_after"]]:
            raise ValueError("Integration amendment must directly follow the collected delivery")
        _git(repo, "merge-base", "--is-ancestor", integration_commit, "HEAD")
        delivered = blob(repo, integration_commit, relative)
        if delivered is None:
            raise ValueError("Integration amendment has no node source")
        additions = _import_amendment(committed, delivered)
        subject = _git(repo, "show", "-s", "--format=%s", integration_commit).strip()
        integrator = parent_commit(
            repo,
            owner,
            integration_commit,
            subject,
            not_before=promotion["finished_at"],
        )
        amendment = {
            "commit": integration_commit,
            "parent": promotion["source_after"],
            "source_before": committed,
            "source_after": delivered,
            "statement_dependencies_added": additions,
            "integrator": integrator,
        }
    if authoring_source_fingerprint(delivered) != authoring_source_fingerprint(
        node_path(repo, node).read_text()
    ):
        raise ValueError("Current authored bytes lack an exact writer/integrator delivery chain")
    evidence = completed_turn(
        repo,
        owner,
        event,
        acknowledgement=None,
        not_before=record["created_at"],
        forbidden_paths={"/root"},
        role="node-writer",
    )
    if evidence["agent_path"] != record["author"]:
        raise ValueError("Collected author differs from the actual completed native writer")
    return {
        "worker": worker,
        "event": event,
        "author_session": record["author"],
        "source_after": promotion["source_after"],
        "execution": evidence,
        "record_sha256": digest(record),
        "integration_amendment": amendment,
    }


def _author_evidence_current(repo: Path, author: dict) -> bool:
    record = _read(repo, author["worker"])
    if digest(record) != author["record_sha256"]:
        return False
    evidence = completed_turn(
        repo,
        record["native_owner"],
        author["event"],
        acknowledgement=None,
        not_before=record["created_at"],
        forbidden_paths={"/root"},
        role="node-writer",
    )
    if evidence != author["execution"]:
        return False
    amendment = author.get("integration_amendment")
    if amendment:
        from homalg.owner_decisions import _git

        subject = _git(repo, "show", "-s", "--format=%s", amendment["commit"]).strip()
        return (
            parent_commit(
                repo,
                record["native_owner"],
                amendment["commit"],
                subject,
                not_before=record["promotion"]["finished_at"],
            )
            == amendment["integrator"]
        )
    return True


def prepare(
    repo: Path,
    node: str,
    *,
    original: str,
    corrected: str,
    author_workspace: str,
    author_event: dict[str, str],
    out: Path,
    integration_commit: str | None = None,
    category: str = CATEGORY,
) -> dict:
    """Freeze a proposal after fresh ordinary build/validation; this grants no decision."""
    repo = repo.resolve()
    target = workflow._local_output(repo, out)
    with workspace_lock(repo):
        owner, contract = _native_contract(repo, node)
        _require_category(contract["policy"], node, category)
        source = node_path(repo, node).read_text()
        metadata = _eligible(source, original, corrected, category=category)
        author = _author(repo, node, author_workspace, author_event, integration_commit)
        before = _capture(repo, node)
        handoff = workflow.prepare(
            repo,
            owner["task"],
            author_session=author["author_session"],
            node_ids=(node,),
            out=Path(str(out) + ".handoff.json"),
        )
        declarations = handoff["compiled"]["declarations"][node]
        if not handoff["ready_for_review"] or any(
            item.get("kind") != "theorem"
            or item.get("is_prop") is not True
            or item.get("direct_sorry") is not True
            for item in declarations
        ):
            raise ValueError(
                "Fresh valid compiled theorem statements with deferred proofs required"
            )
        if _capture(repo, node) != before or _native_contract(repo, node) != (owner, contract):
            raise ValueError("Proposal inputs or native task changed during fresh compilation")
        proposal = {
            "schema_version": 1,
            "kind": PROPOSAL,
            "node": node,
            "created_at": datetime.now(UTC).isoformat(),
            "owner": owner,
            "contract": contract,
            "category": category,
            "original": original,
            "corrected": corrected,
            "source": source,
            "author": author,
            "inputs": before,
            "compiled": handoff["compiled"],
            "validation": handoff["validation"],
            "source_pages": before["context"]["source_pages"],
            "original_dispute": metadata["dispute"],
            "proof_approved": False,
            "visual_sha256": digest(before["visual"]),
            "documents": {
                key: load_yaml((repo / f"literature/{key}/document.yaml").read_text()).get("pdf")
                for key in before["context"]["source_pages"]
            },
        }
        if (
            _capture(repo, node) != before
            or _native_contract(repo, node) != (owner, contract)
            or _author(repo, node, author_workspace, author_event, integration_commit) != author
        ):
            raise ValueError("Proposal evidence changed before publication")
        _validate_proposal(proposal, private=True)
        atomic_create(target, json_text(proposal))
        return {
            "proposal": str(target),
            "proposal_sha256": digest(_public(proposal)),
            "approval": False,
        }


def _assessment(value: dict, proposal: dict) -> None:
    _fields(
        value,
        {
            "schema_version",
            "kind",
            "proposal_sha256",
            "reviewer_session",
            "classification",
            "verdict",
            "unique_typing_justification",
            "comparisons",
            "impact",
            "visual_sha256",
            "integration_amendment_sha256",
            "proof_approved",
        },
    )
    impact = value["impact"]
    expected = {
        "statement": "unchanged",
        "hypotheses": "unchanged",
        "data": "unchanged",
        "proof_route": "unchanged",
        "argument": "no_repair",
        "integration_amendment": "reviewed-current-claim-and-data"
        if proposal["author"].get("integration_amendment")
        else "none",
    }
    if (
        value["schema_version"] != 1
        or value["kind"] != ASSESSMENT
        or value["proposal_sha256"] != digest(_public(proposal))
        or value["classification"] != proposal["category"]
        or value["verdict"] != "unambiguous-local-typo"
        or value["proof_approved"] is not False
        or impact != expected
        or value["visual_sha256"] != proposal["visual_sha256"]
        or value["integration_amendment_sha256"]
        != digest(proposal["author"].get("integration_amendment"))
        or not isinstance(value["unique_typing_justification"], str)
        or not value["unique_typing_justification"].strip()
        or not isinstance(value["comparisons"], list)
        or len(value["comparisons"]) < 2
        or not all(isinstance(row, str) and row.strip() for row in value["comparisons"])
    ):
        raise ValueError(
            "Assessment must independently establish exact local typing and unaffected impact"
        )


def _postimage(source: str, receipt: dict, schemas: SchemaStore) -> str:
    proposal = receipt["proposal"]
    metadata = header_mapping(source)
    metadata["dispute"] = copy.deepcopy(proposal["original_dispute"])
    metadata["dispute"].update(
        status="resolved",
        resolution=json.loads(json_text(receipt["resolution"]))
        | {"receipt_sha256": digest(receipt)},
    )
    fidelity = metadata["fidelity"]
    fidelity.pop("reviewed", None)
    fidelity["status"] = "deviates"
    note = (
        f"Agent-adjudicated local proof membership typo: `{proposal['original']}` becomes "
        f"`{proposal['corrected']}`. Literal source Proof retained; Lean proof deferred."
    )
    if proposal["category"] == proof_map_errata.CATEGORY:
        note = (
            f"Agent-adjudicated proof map-label typo ({proof_map_errata.PROFILE['id']}): "
            "the resulting extension label f'' is read as f', and its antecedent f' as f_0. "
            "Literal source Proof retained; Lean proof deferred."
        )
    fidelity.setdefault("deviations", []).append(
        {
            "kind": "erratum",
            "what": note,
            "why": "Two independent source/data-impact reviews establish the unique correction.",
        }
    )
    text = replace_header(source, metadata, schemas)
    header = parse_header(text)
    body = text[header.start : header.end - 2]
    history = re.search(r"(?m)^## History\s*$", body)
    position = header.start + history.start() if history else header.end - 2
    heading = "" if "Formalization notes" in header.sections else "## Formalization notes\n\n"
    annotation = (
        heading
        + "### Agent proof erratum\n\n"
        + note
        + "\nAdjudication: "
        + receipt["id"]
        + ". Agent judgment; no human confirmation or proof approval.\n\n"
    )
    text = text[:position] + "\n" + annotation + text[position:]
    return _docstring_marker(text, metadata["decls"][0], None)


def _public(proposal: dict) -> dict:
    if "inputs" not in proposal:
        return proposal
    return {
        key: proposal[key]
        for key in (
            "schema_version",
            "kind",
            "node",
            "created_at",
            "contract",
            "category",
            "original",
            "corrected",
            "source",
            "author",
            "compiled",
            "source_pages",
            "original_dispute",
            "proof_approved",
            "visual_sha256",
            "documents",
        )
    } | {"inputs_sha256": digest(proposal["inputs"])}


def _validate_proposal(proposal: dict, *, private: bool) -> None:
    fields = PUBLIC_PROPOSAL_FIELDS
    if private:
        fields = (fields - {"inputs_sha256"}) | {"owner", "inputs", "validation"}
    _fields(proposal, fields)
    _require_category(proposal["contract"]["policy"], proposal["node"], proposal["category"])
    original = _eligible(
        proposal["source"],
        proposal["original"],
        proposal["corrected"],
        category=proposal["category"],
    )
    if (
        proposal["category"] == proof_map_errata.CATEGORY
        and proposal["documents"].get(original["doc"], {}).get("sha256")
        != proof_map_errata.PROFILE["pdf_sha256"]
    ):
        raise ValueError("Map-label profile requires its exact registered source PDF")
    amendment = proposal["author"].get("integration_amendment")
    if amendment:
        _fields(
            amendment,
            {
                "commit",
                "parent",
                "source_before",
                "source_after",
                "statement_dependencies_added",
                "integrator",
            },
        )
        if (
            _import_amendment(amendment["source_before"], amendment["source_after"])
            != amendment["statement_dependencies_added"]
            or authoring_source_fingerprint(amendment["source_after"])
            != authoring_source_fingerprint(proposal["source"])
            or amendment["integrator"].get("actor") != "/root"
            or amendment["integrator"].get("role") != "native-lead"
            or amendment["integrator"].get("commit") != amendment["commit"]
            or amendment["parent"] != proposal["author"]["source_after"]
        ):
            raise ValueError("Invalid original-writer/canonical-integrator source chain")
    _fields(proposal["compiled"], {"fresh_build", "raw_sha256", "declarations"})
    declarations = proposal["compiled"]["declarations"]
    if (
        type(proposal["schema_version"]) is not int
        or proposal["schema_version"] != 1
        or proposal["kind"] != PROPOSAL
        or proposal["category"] not in CATEGORIES
        or proposal["node"] != original["id"]
        or proposal["proof_approved"] is not False
        or proposal["original_dispute"] != original["dispute"]
        or proposal["compiled"]["fresh_build"] is not True
        or set(declarations) != {original["id"]}
        or {item.get("name") for item in declarations[original["id"]]} != set(original["decls"])
        or any(
            item.get("kind") != "theorem"
            or item.get("is_prop") is not True
            or item.get("direct_sorry") is not True
            for item in declarations[original["id"]]
        )
        or proposal["contract"].get("proofs") != "deferred"
        or proposal["contract"].get("policy_sha256") != digest(proposal["contract"].get("policy"))
    ):
        raise ValueError(
            "Proposal must preserve its exact original dispute and deferred compiled statements"
        )
    if private and (
        proposal["visual_sha256"] != digest(proposal["inputs"]["visual"])
        or any(item["severity"] == "error" for item in proposal["validation"]["findings"])
    ):
        raise ValueError("Proposal has changed private evidence or failed fresh validation")


def _read_proposal(repo: Path, path: Path) -> tuple[dict, dict]:
    path = repo / path
    if path.resolve() != path or not path.is_relative_to(repo / "build") or not path.is_file():
        raise ValueError("Proposal must be a regular local build artifact")
    fingerprint = file_fingerprint(path)
    proposal = json.loads(path.read_text())
    if file_fingerprint(path) != fingerprint:
        raise ValueError("Proposal changed while reading")
    _validate_proposal(proposal, private=True)
    return proposal, {"path": str(path.relative_to(repo)), "fingerprint": fingerprint}


def _reviewers(repo: Path, proposal: dict, events: list[dict], report: str) -> list[dict]:
    if len(events) != 2:
        raise ValueError("Exactly two independent completed reviews are required")
    assessments = [
        item
        for item in blocks(report, ASSESSMENT)
        if item.get("proposal_sha256") == digest(_public(proposal))
    ]
    if len(assessments) != 2:
        raise ValueError("Exactly two current typed assessments are required")
    found = []
    forbidden = {"/root", proposal["author"]["author_session"]}
    for event in events:
        matches = []
        for assessment in assessments:
            _assessment(assessment, proposal)
            acknowledgement = {
                "kind": "agent-proof-erratum-ack",
                "proposal_sha256": digest(_public(proposal)),
                "assessment_sha256": digest(assessment),
            }
            try:
                evidence = completed_ack(
                    repo,
                    proposal["owner"],
                    event,
                    acknowledgement=acknowledgement,
                    not_before=proposal["created_at"],
                    forbidden_paths=forbidden,
                )
            except ValueError:
                continue
            if evidence["agent_path"] == assessment["reviewer_session"]:
                matches.append({"assessment": assessment, "event": event, "execution": evidence})
        if len(matches) != 1:
            raise ValueError("Review must join its actual native execution and exact assessment")
        item = matches[0]
        found.append(item)
        forbidden.add(item["execution"]["agent_path"])
    if len({item["execution"]["child_id"] for item in found}) != 2:
        raise ValueError("Reviewers must be two distinct actual native children")
    return sorted(found, key=lambda item: item["execution"]["child_id"])


def _receipt(proposal: dict, reviews: list[dict], snapshot: dict) -> dict:
    identity = digest({"proposal": _public(proposal), "reviews": reviews})
    owner = proposal["owner"]
    resolution = {
        "kind": KIND,
        "via": "erratum",
        "by": "native-lead",
        "session": f"{owner['run']}/{owner['session']}",
        "on": datetime.now(UTC).date().isoformat(),
        "adjudication_id": identity,
        "receipt": report_path(proposal["node"]),
        "policy_sha256": proposal["contract"]["policy_sha256"],
        "note": "Two independent agents adjudicated a local membership typo; proof deferred.",
    }
    if proposal["category"] == proof_map_errata.CATEGORY:
        resolution["note"] = (
            "Two independent agents adjudicated the source-bound map-label typo; proof deferred."
        )
    return {
        "schema_version": 1,
        "kind": RECEIPT,
        "id": identity,
        "proposal": _public(proposal),
        "reviews": reviews,
        "resolution": resolution,
        "snapshot": snapshot,
        "native": {key: owner[key] for key in ("run", "session", "task")},
        "proof_approved": False,
    }


def _receipt_for(source: str, current: Callable[[str], str | None]) -> dict | None:
    metadata = parse_header(source).metadata
    resolution = metadata.get("dispute", {}).get("resolution", {})
    if resolution.get("kind") != KIND:
        return None
    if resolution.get("receipt") != report_path(metadata["id"]):
        raise ValueError("Agent adjudication receipt belongs to a different node")
    candidates = [
        item
        for item in blocks(current(resolution["receipt"]) or "", RECEIPT)
        if item.get("id") == resolution.get("adjudication_id")
    ]
    if len(candidates) != 1 or digest(candidates[0]) != resolution.get("receipt_sha256"):
        raise ValueError("Agent adjudication receipt is absent, changed or ambiguous")
    receipt = candidates[0]
    _fields(
        receipt,
        {
            "schema_version",
            "kind",
            "id",
            "proposal",
            "reviews",
            "resolution",
            "snapshot",
            "native",
            "proof_approved",
        },
    )
    proposal = receipt["proposal"]
    _validate_proposal(proposal, private=False)
    _eligible(
        proposal["source"],
        proposal["original"],
        proposal["corrected"],
        category=proposal["category"],
    )
    if (
        receipt["schema_version"] != 1
        or receipt["proof_approved"] is not False
        or proposal["proof_approved"] is not False
        or proposal["node"] != metadata["id"]
        or receipt["id"] != digest({"proposal": proposal, "reviews": receipt["reviews"]})
        or resolution != receipt["resolution"] | {"receipt_sha256": digest(receipt)}
        or metadata["dispute"]
        != proposal["original_dispute"] | {"status": "resolved", "resolution": resolution}
        or resolution["policy_sha256"] != digest(proposal["contract"]["policy"])
        or len(receipt["reviews"]) != 2
    ):
        raise ValueError("Invalid agent adjudication identity or original dispute binding")
    report = current(resolution["receipt"]) or ""
    actors, children = set(), set()
    for item in receipt["reviews"]:
        _fields(item, {"assessment", "event", "execution"})
        assessment, execution = item["assessment"], item["execution"]
        _assessment(assessment, proposal)
        if assessment not in blocks(report, ASSESSMENT):
            raise ValueError("A bound original assessment block was changed or deleted")
        if (
            execution["agent_path"] != assessment["reviewer_session"]
            or execution["agent_path"] in {"/root", proposal["author"]["author_session"]}
            or execution["role"] != "source-fidelity-reviewer"
            or execution["child_id"] != item["event"]["child_id"]
            or execution["turn_id"] != item["event"]["turn_id"]
        ):
            raise ValueError("Invalid historical reviewer binding")
        actors.add(execution["agent_path"])
        children.add(execution["child_id"])
    if len(actors) != 2 or len(children) != 2:
        raise ValueError("Historical adjudication lacks independent real reviewer identities")
    return receipt


def _prose(source: str) -> str:
    header = parse_header(source)
    text = source[header.start : header.end]
    opening = text.index("```yaml node")
    closing = text.index("```", opening + len("```yaml node")) + 3
    return text[:opening] + text[closing:]


def _previously_trusted(receipt: dict, trusted: Callable[[str], str | None]) -> bool:
    node = receipt["proposal"]["node"]
    source = trusted("HomAlg/" + node.replace(".", "/") + ".lean")
    if source is None or receipt not in blocks(trusted(report_path(node)) or "", RECEIPT):
        return False
    metadata = parse_header(source).metadata
    records = [metadata.get("dispute", {}), *metadata.get("dispute_history", [])]
    expected = receipt["resolution"] | {"receipt_sha256": digest(receipt)}
    return any(record.get("resolution") == expected for record in records)


def validate_resolution(
    repo: Path,
    source: str,
    *,
    anchor: str | None = None,
    ledger: bool = True,
) -> dict | None:
    """Validate historical public bindings; never claim a new private-image inspection."""
    metadata = parse_header(source).metadata
    records = [metadata.get("dispute", {}), *metadata.get("dispute_history", [])]
    if not any(record.get("resolution", {}).get("kind") == KIND for record in records):
        return None
    if anchor is None:
        anchor, ledger = _authority(repo)
    return validate_snapshot(
        source,
        trusted=lambda name: blob(repo, anchor, name, ledger=ledger),
        current=lambda name: _safe_file(repo, name).read_text(),
        schemas=SchemaStore(repo / "schema"),
    )


def validate_snapshot(
    source: str,
    *,
    trusted: Callable[[str], str | None],
    current: Callable[[str], str | None],
    schemas: SchemaStore,
) -> dict | None:
    metadata = parse_header(source).metadata
    for record in metadata.get("dispute_history", []):
        if record.get("resolution", {}).get("kind") == KIND:
            historical = copy.deepcopy(metadata)
            historical["dispute"] = record
            # Check immutable historical evidence against its own saved source,
            # never against the source of a later reopened dispute.
            saved = _receipt_for(replace_header(source, historical, schemas), current)
            if not saved:
                raise ValueError("Archived agent erratum evidence is unavailable")
            if not _previously_trusted(saved, trusted):
                capability = _policy(trusted(POLICY), metadata["id"])
                if digest(capability) != saved["resolution"]["policy_sha256"]:
                    raise ValueError("Archived agent decision lacks its trusted policy binding")
    receipt = _receipt_for(source, current)
    if receipt is None:
        return None
    proposal = receipt["proposal"]
    if not _previously_trusted(receipt, trusted):
        capability = _policy(trusted(POLICY), proposal["node"])
        if digest(capability) != receipt["resolution"]["policy_sha256"]:
            raise ValueError("Agent erratum differs from the prospective trusted policy")
    expected = _postimage(proposal["source"], receipt, schemas)
    if _prose(source) != _prose(expected):
        raise ValueError("Literal source/erratum annotation changed after agent adjudication")
    actual, anticipated = parse_header(source).metadata, parse_header(expected).metadata
    if actual["source"] != anticipated["source"] or actual["doc"] != anticipated["doc"]:
        raise ValueError("Agent adjudication cannot retarget its original source anchor")
    for key, identity in proposal["documents"].items():
        document = load_yaml(current(f"literature/{key}/document.yaml") or "{}")
        if document.get("pdf") != identity:
            raise ValueError("Registered source PDF identity changed after adjudication")
    if actual.get("dispute_history", []) != anticipated.get("dispute_history", []):
        raise ValueError("Agent adjudication cannot erase or extend dispute history")
    if not all(
        item in actual["fidelity"].get("deviations", [])
        for item in anticipated["fidelity"].get("deviations", [])
    ):
        raise ValueError("Agent erratum explanation was removed")
    return receipt


def history_error(before: dict, after: dict) -> bool:
    old, new = before.get("dispute_history", []), after.get("dispute_history", [])
    if new[: len(old)] != old:
        return any(item.get("resolution", {}).get("kind") == KIND for item in old + new)
    additions = [item for item in new[len(old) :] if item.get("resolution", {}).get("kind") == KIND]
    previous, current = before.get("dispute", {}), after.get("dispute", {})
    if additions and not (
        additions == [previous] and current.get("status") == "open" and new == old + [previous]
    ):
        return True
    if previous.get("resolution", {}).get("kind") == KIND and current != previous:
        return not (current.get("status") == "open" and new == old + [previous])
    return False


def authorized_transition(
    before: str,
    after: str,
    *,
    trusted: Callable[[str], str | None],
    current: Callable[[str], str | None],
    schemas: SchemaStore,
    native_repo: Path | None = None,
    native_bounds: tuple[str, str, str] | None = None,
) -> bool:
    old, new = parse_header(before).metadata, parse_header(after).metadata
    if new.get("dispute", {}).get("resolution", {}).get("kind") != KIND or history_error(old, new):
        return False
    for metadata in (old, new):
        lock = metadata.get("fidelity", {}).get("reviewed")
        if lock and lock.get("kind") != "agent":
            return False
    receipt = validate_snapshot(after, trusted=trusted, current=current, schemas=schemas)
    if not receipt or old.get("dispute") != receipt["proposal"]["original_dispute"]:
        return False
    expected = _postimage(receipt["proposal"]["source"], receipt, schemas)
    if authoring_source_fingerprint(after) != authoring_source_fingerprint(expected):
        return False
    if old.get("dispute_history", []) != new.get("dispute_history", []):
        return False
    if native_repo is not None:
        if native_bounds is None:
            return False
        task_id, since, until = native_bounds
        native = receipt["native"]
        if native["task"] != task_id or receipt["proposal"]["contract"]["start"] != since:
            return False
        meta_path = f".archon-horizon/runs/{native['run']}/sessions/{native['session']}/meta.json"
        meta = json.loads(_safe_file(native_repo, meta_path).read_text())
        if meta.get("task_id") != task_id or meta.get("start_sha") != since:
            return False
        if meta.get("end_sha") != until:
            owner = _native_owner(native_repo)
            if any(owner[key] != native[key] for key in ("run", "session", "task")):
                return False
        journal = json.loads(
            _safe_file(
                native_repo, f".archon-horizon/cache/agent-errata-transactions/{receipt['id']}.json"
            ).read_text()
        )
        if (
            journal.get("state") != "committed"
            or journal.get("receipt_sha256") != digest(receipt)
            or journal.get("native") != native
            or journal.get("start") != since
            or journal.get("postimage_sha256") != authoring_source_fingerprint(after)
        ):
            return False
        proposal, snapshot = _read_proposal(native_repo, Path(receipt["snapshot"]["path"]))
        if snapshot != receipt["snapshot"] or _public(proposal) != receipt["proposal"]:
            return False
        if not _author_evidence_current(native_repo, proposal["author"]):
            return False
        actual = _reviewers(
            native_repo,
            proposal,
            [item["event"] for item in receipt["reviews"]],
            current(report_path(new["id"])) or "",
        )
        if actual != receipt["reviews"]:
            return False
    else:
        # Public CI can inspect historical evidence but cannot mint a fresh
        # native judgment from report JSON without the actual execution context.
        if not _previously_trusted(receipt, trusted):
            return False
    return True


def adjudicate(repo: Path, node: str, *, snapshot: Path, reviewer_events: list[dict]) -> dict:
    """Apply one reviewed lexical erratum atomically; ordinary fidelity must follow."""
    repo = repo.resolve()
    owner, contract = _native_contract(repo, node)
    proposal, reference = _read_proposal(repo, snapshot)
    if (
        proposal.get("node") != node
        or proposal.get("owner") != owner
        or proposal.get("contract") != contract
    ):
        raise ValueError("Proposal belongs to a different native task/session/contract")
    source_path = node_path(repo, node)
    report = _safe_file(repo, report_path(node))
    with _integration_lock(repo, native_owner=owner) as verify_locks:
        journals = repo / ".archon-horizon/cache/agent-errata-transactions"
        for path in journals.glob("*.json"):
            if json.loads(path.read_text()).get("state") in {"prepared", "recovery-required"}:
                raise ValueError("Unfinished agent erratum transaction requires explicit recovery")
        report_before = report.read_text()
        reviews = _reviewers(repo, proposal, reviewer_events, report_before)
        current_source = source_path.read_text()
        previous = _receipt_for(current_source, lambda name: _safe_file(repo, name).read_text())
        identity = digest({"proposal": _public(proposal), "reviews": reviews})
        if previous:
            if previous["id"] != identity or previous["snapshot"] != reference:
                raise ValueError("Conflicting agent adjudication cannot be retried")
            journal = json.loads((journals / f"{identity}.json").read_text())
            if journal.get("state") != "committed" or journal.get("receipt_sha256") != digest(
                previous
            ):
                raise ValueError("Idempotent retry requires its committed application receipt")
            validate_resolution(repo, current_source)
            verify_locks()
            return {"id": identity, "already_applied": True, "approval": False}
        _eligible(
            current_source,
            proposal["original"],
            proposal["corrected"],
            category=proposal["category"],
        )
        if current_source != proposal["source"] or _capture(repo, node) != proposal["inputs"]:
            raise ValueError("Source/private/compiled inputs changed after the reviewed proposal")
        if (
            _author(
                repo,
                node,
                proposal["author"]["worker"],
                proposal["author"]["event"],
                (proposal["author"].get("integration_amendment") or {}).get("commit"),
            )
            != proposal["author"]
        ):
            raise ValueError("Original actual author evidence changed")
        receipt = _receipt(proposal, reviews, reference)
        updated = _postimage(current_source, receipt, SchemaStore(repo / "schema"))
        report_after = (
            report_before.rstrip() + f"\n\n```homalg-{RECEIPT}\n" + json_text(receipt) + "```\n"
        )
        expected_inputs = copy.deepcopy(proposal["inputs"])
        expected_report = report_before
        originals = {report: report.read_bytes(), source_path: source_path.read_bytes()}
        written = {}
        journal_path = journals / f"{identity}.json"
        journal = {
            "schema_version": 1,
            "id": identity,
            "state": "prepared",
            "node": node,
            "native": receipt["native"],
            "start": contract["start"],
            "receipt_sha256": digest(receipt),
            "postimage_sha256": authoring_source_fingerprint(updated),
        }

        def guard():
            verify_locks()
            if (
                _native_contract(repo, node) != (owner, contract)
                or _read_proposal(repo, snapshot)[1] != reference
                or _capture(repo, node) != expected_inputs
                or report.read_text() != expected_report
                or _reviewers(repo, proposal, reviewer_events, expected_report) != reviews
                or not _author_evidence_current(repo, proposal["author"])
            ):
                raise ValueError("Adjudication inputs, task, report or actual reviews changed")

        guard()
        atomic_write(journal_path, json_text(journal))
        try:
            for path, text in ((report, report_after), (source_path, updated)):
                guard()
                written[path] = atomic_write_with_receipt(path, text)
                if path == report:
                    expected_report = report_after
                else:
                    expected_inputs["compilation"]["files"][str(source_path)] = written[path]
                guard()
            journal["state"] = "committed"
            verify_locks()
            atomic_write(journal_path, json_text(journal))
            guard()
        except BaseException:
            conflicts = []
            for path in reversed(list(written)):
                try:
                    ours = file_fingerprint(path) == written[path]
                except OSError:
                    ours = False
                if ours:
                    atomic_bytes(path, originals[path])
                else:
                    conflicts.append(str(path.relative_to(repo)))
            journal.update(
                state="recovery-required" if conflicts else "rolled-back", conflicts=conflicts
            )
            atomic_write(journal_path, json_text(journal))
            raise
        return {
            "id": identity,
            "already_applied": False,
            "approval": False,
            "ordinary_review_required": True,
            "proof_approved": False,
        }
