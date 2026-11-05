"""Replay narrowly bound, preexisting owner directions without impersonating a human.

The trusted profile is an explicit administrative authorization boundary. An
inbox relay is evidence of the operator's attestation, not a human signature.
Native sessions can consume a profile and receipt present at their start; they
cannot mint either. Independent mathematical review remains a separate gate.
"""

import copy
import hashlib
import json
import os
import re
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg.documents import read_document
from homalg.headers import parse_header
from homalg.io import atomic_create, atomic_write, json_text
from homalg.nodeio import header_mapping, node_path, replace_header
from homalg.schemas import SchemaStore, load_yaml

POLICY = "horizon/owner-decision-replays.json"
KIND = "owner-decision-replay"


def digest(value: Any) -> str:
    return hashlib.sha256(json_text(value).encode()).hexdigest()


def protected_path(path: str) -> bool:
    return path == POLICY or bool(
        re.fullmatch(r"literature/[^/]+/owner-decisions/[^/]+\.json", path)
    )


def _safe_file(repo: Path, relative: str) -> Path:
    path = repo / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Owner decision path must remain inside the repository")
    if any(part.is_symlink() for part in [path, *path.parents] if part != repo):
        raise ValueError("Owner decision evidence must not use symlinks")
    if not path.resolve().is_relative_to(repo.resolve()):
        raise ValueError("Owner decision path escapes the repository")
    return path


def _git(repo: Path, *args: str, ledger: bool = True) -> str:
    command = ["git"]
    if ledger:
        directory = _safe_file(repo, ".archon-horizon/vcs/workspace.git")
        if not directory.is_dir():
            raise ValueError("Owner decision replay requires the source ledger")
        command += ["--git-dir", str(directory), "--work-tree", str(repo)]
    result = subprocess.run(
        [*command, *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
    )
    if result.returncode:
        raise ValueError("Owner decision trust check failed: " + result.stderr.strip())
    return result.stdout


def blob(repo: Path, anchor: str, relative: str, *, ledger: bool = True) -> str:
    if not re.fullmatch(r"[0-9a-f]{40,64}", anchor):
        raise ValueError("Owner decision trust requires an immutable commit")
    _safe_file(repo, relative)
    return _git(repo, "show", f"{anchor}:{relative}", ledger=ledger)


def evidence_projection(value: dict[str, Any]) -> dict[str, Any]:
    """Bind the relay itself, excluding mutable delivery/read acknowledgements."""
    return {
        key: value.get(key)
        for key in ("id", "provider", "kind", "body", "author", "created_at", "scope", "audience")
    }


def source_binding(
    source: str, document: dict[str, Any], original: dict[str, Any]
) -> dict[str, Any]:
    header = parse_header(source)
    node = header.metadata
    binding = {
        "node_id": node["id"],
        "source": node["source"],
        "pdf": document.get("pdf", {}),
        "statement": header.sections.get("Statement", ""),
        "corrected_statement": header.sections.get("Statement (corrected)", ""),
        "errata": [
            {"kind": entry["kind"], "what": entry.get("what", "")}
            for entry in node.get("fidelity", {}).get("deviations", [])
            if entry.get("kind") == "erratum"
        ],
        "original_dispute": original,
        "dispute_history": node.get("dispute_history", []),
    }
    if original.get("kind") == "proof":
        binding["proof"] = header.sections.get("Proof", "")
        # Only explicitly labelled corrected displays are adopted, never a new proof route.
        binding["corrected_proof_displays"] = re.findall(
            r"\\\[\s*\\tag\{[^}]+, corrected\}[\s\S]*?\\\]",
            header.sections.get("Formalization notes", ""),
        )
    return binding


def _profile(policy_text: str, decision: str) -> dict[str, Any]:
    policy = json.loads(policy_text)
    if policy.get("schema_version") != 1 or not isinstance(policy.get("decisions"), list):
        raise ValueError("Invalid recorded-owner-decision policy")
    matches = [entry for entry in policy["decisions"] if entry.get("id") == decision]
    if len(matches) != 1:
        raise ValueError("Decision is not explicitly authorized by the trusted replay profile")
    return matches[0]


def receipt_path(profile: dict[str, Any]) -> str:
    decision = profile["id"]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", decision):
        raise ValueError("Invalid owner decision id")
    return f"literature/{profile['node_id'].split('.', 1)[0]}/owner-decisions/{decision}.json"


def _check_sources(repo: Path, profile: dict[str, Any]) -> None:
    control = repo
    if os.environ.get("HOMALG_SESSION_MAIN_ROOT"):
        from homalg.workspaces import _control_root, _native_owner

        # Only an authenticated native session may read its shared runtime evidence.
        # Policies and receipts remain bound to the local checkout and immutable START.
        _native_owner(repo)
        control, _ = _control_root(repo)
    for item in profile.get("artifacts", []):
        # Historical private/build evidence is shared, and bound by the trusted hash.
        path = _safe_file(control, item["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Recorded owner decision artifact changed: {item['path']}")
    for item in profile["evidence"]:
        identifier = item["id"]
        if not re.fullmatch(r"I-[0-9]{4,}", identifier):
            raise ValueError("Invalid owner decision inbox reference")
        path = _safe_file(control, f".archon-horizon/inbox/local/items/{identifier}.yaml")
        value = load_yaml(path.read_text())
        if value.get("id") != identifier or digest(evidence_projection(value)) != item["sha256"]:
            raise ValueError(f"Recorded owner decision evidence changed: {identifier}")


def record(
    repo: Path, decision: str, *, by: str, session: str, attest_existing: bool = False
) -> dict[str, Any]:
    """Record an actual outer operator's attestation at an idle boundary only.

    The profile, including exact source/evidence bindings, must already be in the
    source ledger. This command cannot create a new mathematical decision.
    """
    from homalg.workspaces import _integration_lock

    repo = repo.resolve()
    if os.environ.get("ARCHON_HORIZON_SESSION") or os.environ.get("HOMALG_SESSION_MAIN_ROOT"):
        raise ValueError("Native sessions and draft workers cannot issue owner-decision receipts")
    if not attest_existing or not by.strip() or not session.strip():
        raise ValueError(
            "Explicit existing-instruction attestation and actual operator/session required"
        )
    with _integration_lock(repo) as verify_locks:
        anchor = _git(repo, "rev-parse", "HEAD").strip()
        policy = blob(repo, anchor, POLICY)
        if _safe_file(repo, POLICY).read_text() != policy:
            raise ValueError("Replay profile differs from the trusted source-ledger baseline")
        profile = _profile(policy, decision)
        _check_sources(repo, profile)
        source = node_path(repo, profile["node_id"]).read_text()
        header = parse_header(source)
        original = header.metadata.get("dispute", {})
        if original.get("status") != "open" or any(
            field in original for field in ("confirmed_by", "confirmed_on", "resolution")
        ):
            raise ValueError("Replay receipts require an unconfirmed open dispute")
        document = read_document(repo, header.metadata["doc"])
        binding = source_binding(source, document, original)
        if (
            original.get("kind") not in {"statement", "proof"}
            or (original["kind"] == "statement" and not binding["corrected_statement"])
            or (
                original["kind"] == "proof"
                and (not binding.get("proof") or not binding.get("corrected_proof_displays"))
            )
            or not binding["errata"]
            or digest(binding) != profile["binding_sha256"]
        ):
            raise ValueError(
                "Node, dispute, PDF or corrected source differs from the authorized decision"
            )
        value = {
            "schema_version": 1,
            "kind": "recorded-owner-instruction-attestation",
            "decision_id": decision,
            "node_id": profile["node_id"],
            "owner": profile["owner"],
            "attested_by": by,
            "attestation_session": session,
            "recorded_at": datetime.now(UTC).isoformat(),
            "profile_sha256": digest(profile),
            "binding_sha256": digest(binding),
            "original_dispute": original,
            "original_history": header.metadata.get("dispute_history", []),
            "evidence": profile["evidence"],
            "artifacts": profile.get("artifacts", []),
            "instruction": profile["instruction"],
            "authority": "operator-attestation-of-preexisting-owner-direction",
        }
        errors = SchemaStore(repo / "schema").validate(value, "owner-decision.schema.json")
        if errors:
            raise ValueError(errors[0].message)
        path = _safe_file(repo, receipt_path(profile))
        if path.exists():
            previous = json.loads(path.read_text())
            if {k: v for k, v in previous.items() if k != "recorded_at"} != {
                k: v for k, v in value.items() if k != "recorded_at"
            }:
                raise ValueError("An owner decision receipt is append-only and cannot be replaced")
            value = previous
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            verify_locks()
            atomic_create(path, json_text(value), mode=0o644)
        # Administrative provenance, not a human action; only this new receipt is committed.
        try:
            if blob(repo, anchor, receipt_path(profile)) == path.read_text():
                return value
        except ValueError:
            pass
        verify_locks()
        _git(repo, "add", "--", receipt_path(profile))
        _git(
            repo,
            "commit",
            "--only",
            "-m",
            f"owner-decision relay: {decision}",
            "--",
            receipt_path(profile),
        )
        return value


def _authority(repo: Path) -> tuple[str, bool]:
    if os.environ.get("ARCHON_HORIZON_SESSION"):
        from homalg.workspaces import _control_root, _native_owner

        owner = _native_owner(repo)
        control, _ = _control_root(repo)
        path = _safe_file(
            control, f".archon-horizon/runs/{owner['run']}/sessions/{owner['session']}/meta.json"
        )
        return json.loads(path.read_text())["start_sha"], True
    ledger = (repo / ".archon-horizon/vcs/workspace.git").is_dir()
    return _git(repo, "rev-parse", "HEAD", ledger=ledger).strip(), ledger


def validate_resolution(
    repo: Path,
    source: str,
    *,
    anchor: str | None = None,
    ledger: bool = True,
    document: dict[str, Any] | None = None,
    evidence: bool = False,
) -> dict[str, Any] | None:
    """Check a replay against an independently supplied start/base, never a claimed authority."""
    metadata = parse_header(source).metadata
    if metadata.get("dispute", {}).get("resolution", {}).get("kind") != KIND:
        return None
    if anchor is None:
        anchor, ledger = _authority(repo)
    receipt = validate_snapshot(
        source,
        document or read_document(repo, metadata["doc"]),
        trusted=lambda path: blob(repo, anchor, path, ledger=ledger),
        current=lambda path: _safe_file(repo, path).read_text(),
        schemas=SchemaStore(repo / "schema"),
    )
    if evidence and receipt:
        _check_sources(repo, receipt)
    return receipt


def validate_snapshot(
    source: str,
    document: dict[str, Any],
    *,
    trusted: Callable[[str], str | None],
    current: Callable[[str], str | None],
    schemas: SchemaStore | None = None,
) -> dict[str, Any] | None:
    """Pure snapshot check shared by actual engine START and PR BASE boundaries."""
    node = parse_header(source).metadata
    dispute = node.get("dispute", {})
    resolution = dispute.get("resolution", {})
    if resolution.get("kind") != KIND:
        return None
    policy_text = trusted(POLICY)
    if policy_text is None or current(POLICY) != policy_text:
        raise ValueError("Replay profile absent or changed from the trusted start/base")
    profile = _profile(policy_text, resolution.get("decision_id", ""))
    relative = receipt_path(profile)
    receipt_text = trusted(relative)
    if receipt_text is None or current(relative) != receipt_text:
        raise ValueError("Owner decision receipt absent or changed from the trusted start/base")
    receipt = json.loads(receipt_text)
    if schemas:
        errors = schemas.validate(receipt, "owner-decision.schema.json")
        if errors:
            raise ValueError(errors[0].message)
    original = receipt["original_dispute"]
    expected = {**original, "status": "resolved", "resolution": resolution}
    if (
        receipt.get("kind") != "recorded-owner-instruction-attestation"
        or receipt.get("authority") != "operator-attestation-of-preexisting-owner-direction"
        or receipt["decision_id"] != profile["id"]
        or node["id"] != profile["node_id"]
        or receipt["node_id"] != node["id"]
        or receipt["profile_sha256"] != digest(profile)
        or receipt["owner"] != profile["owner"]
        or receipt["instruction"] != profile["instruction"]
        or receipt["evidence"] != profile["evidence"]
        or receipt.get("artifacts", []) != profile.get("artifacts", [])
        or resolution.get("receipt_sha256") != hashlib.sha256(receipt_text.encode()).hexdigest()
        or resolution.get("via") != "erratum"
        or resolution.get("receipt") != relative
        or not resolution.get("session")
        or not resolution.get("by")
        or dispute != expected
        or original.get("status") != "open"
        or any(field in original for field in ("confirmed_by", "confirmed_on", "resolution"))
        or node.get("dispute_history", []) != receipt["original_history"]
    ):
        raise ValueError(
            "Owner decision replay identity, provenance or original history is invalid"
        )
    binding = digest(source_binding(source, document, original))
    if binding != receipt["binding_sha256"] or binding != profile["binding_sha256"]:
        raise ValueError("Owner decision is stale: source, correction, PDF or dispute changed")
    return receipt


def replay_history_error(before: dict[str, Any], after: dict[str, Any]) -> bool:
    """A replay may enter history only by preserving the prior current record on reopening."""
    previous = before.get("dispute", {})
    old, new = before.get("dispute_history", []), after.get("dispute_history", [])
    if new[: len(old)] != old:
        return any(item.get("resolution", {}).get("kind") == KIND for item in [*old, *new])
    added = [item for item in new[len(old) :] if item.get("resolution", {}).get("kind") == KIND]
    if not added:
        return False
    return not (
        added == [previous]
        and previous.get("resolution", {}).get("kind") == KIND
        and previous.get("status") == "resolved"
        and after.get("dispute", {}).get("status") == "open"
        and new == old + [previous]
    )


def authorized_transition(
    before: str,
    after: str,
    document: dict[str, Any],
    *,
    trusted: Callable[[str], str | None],
    current: Callable[[str], str | None],
    schemas: SchemaStore | None = None,
) -> bool:
    """Exempt only the exact receipt-authorized dispute transition from human-field checks."""
    from homalg.scope import human_fields_changed

    old, new = parse_header(before).metadata, parse_header(after).metadata
    receipt = validate_snapshot(after, document, trusted=trusted, current=current, schemas=schemas)
    if not receipt or old.get("dispute") != receipt["original_dispute"]:
        return False
    old_lock = old.get("fidelity", {}).get("reviewed")
    new_lock = new.get("fidelity", {}).get("reviewed")
    if any(lock and lock.get("kind") != "agent" for lock in (old_lock, new_lock)):
        return False
    restored = copy.deepcopy(new)
    restored["dispute"] = old["dispute"]
    return not human_fields_changed(old, restored)


def replay(repo: Path, node_id: str, *, decision: str, by: str, session: str) -> dict[str, Any]:
    """Apply only the already-recorded owner direction; never grant a fidelity lock."""
    from homalg.disputes import _docstring_marker
    from homalg.engine import task
    from homalg.workspaces import _integration_lock, _native_owner

    repo = repo.resolve()
    if not by.strip() or not session.strip():
        raise ValueError("Actual replay operator and session are required")
    if os.environ.get("HOMALG_SESSION_MAIN_ROOT"):
        raise ValueError("Draft workers cannot replay owner decisions")
    native = _native_owner(repo) if os.environ.get("ARCHON_HORIZON_SESSION") else None
    if native:
        if session != native["session"]:
            raise ValueError("Replay session must be the actual native session identity")
        record = task(repo, native["task"])
        relative = f"HomAlg/{node_id.replace('.', '/', 1)}.lean"
        if relative not in record.get("write_set", {}).get("files", []):
            raise ValueError("Owner decision replay exceeds the native task's exact node scope")
    with _integration_lock(repo, native_owner=native) as verify_locks:
        anchor, ledger = _authority(repo)
        profile = _profile(blob(repo, anchor, POLICY, ledger=ledger), decision)
        if profile["node_id"] != node_id:
            raise ValueError("Owner decision does not authorize this node")
        receipt_text = blob(repo, anchor, receipt_path(profile), ledger=ledger)
        receipt = json.loads(receipt_text)
        path = node_path(repo, node_id)
        original_source = path.read_text()
        source = original_source
        metadata = header_mapping(source)
        if metadata.get("dispute", {}).get("resolution", {}).get("kind") == KIND:
            validate_resolution(repo, source, anchor=anchor, ledger=ledger, evidence=True)
            if metadata["dispute"]["resolution"]["decision_id"] != decision:
                raise ValueError("A conflicting owner decision is already applied")
            return metadata["dispute"]
        if metadata.get("dispute") != receipt["original_dispute"]:
            raise ValueError("Original dispute changed before replay")
        reviewed = metadata.get("fidelity", {}).get("reviewed")
        if reviewed and reviewed.get("kind") != "agent":
            raise ValueError("Owner decision replay cannot replace a human fidelity lock")
        metadata["dispute"]["status"] = "resolved"
        metadata["dispute"]["resolution"] = {
            "kind": KIND,
            "via": "erratum",
            "by": by,
            "session": session,
            "on": datetime.now(UTC).date().isoformat(),
            "decision_id": decision,
            "receipt": receipt_path(profile),
            "receipt_sha256": hashlib.sha256(receipt_text.encode()).hexdigest(),
            "note": (
                "Actual agent replay of an attested prior owner direction; "
                "no human confirmation or independent review implied."
            ),
        }
        # A source/header change needs ordinary fresh compilation and review.
        metadata["fidelity"].pop("reviewed", None)
        if metadata.get("decls"):
            source = _docstring_marker(source, metadata["decls"][0], None)
        source = replace_header(source, metadata, SchemaStore(repo / "schema"))
        validate_resolution(repo, source, anchor=anchor, ledger=ledger, evidence=True)
        if path.read_text() != original_source:
            raise ValueError("Node changed while replay was being prepared")
        verify_locks()
        atomic_write(path, source)
        return copy.deepcopy(metadata["dispute"])
