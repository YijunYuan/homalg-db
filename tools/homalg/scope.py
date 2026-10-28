"""Session interval write-scope checks, including protected human evidence."""

import re
import subprocess
from pathlib import Path
from typing import Any

from homalg.classify import append_only, document_keys
from homalg.engine import task
from homalg.headers import parse_header
from homalg.schemas import SchemaStore, load_yaml


def ledger(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Read the engine audit repository, never the user's branch history."""
    result = subprocess.run(
        [
            "git",
            "--git-dir",
            str(repo / ".archon-horizon/vcs/workspace.git"),
            "--work-tree",
            str(repo),
            *args,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError(f"Cannot inspect session ledger: {result.stderr.strip()}")
    return result


def human_fields_changed(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    document: bool = False,
    allow_agent_reviews: bool = False,
) -> bool:
    """Detect approvals or dispute resolutions that an agent session cannot author."""
    from homalg.review_policy import foundation_confirmed, valid_agent_review

    policy = {"schema_version": 1, "allow_independent_agent_reviews": allow_agent_reviews}

    if document:
        old_early, new_early = before.get("early_review"), after.get("early_review")
        if old_early != new_early:
            if old_early and old_early.get("kind") != "agent":
                return True
            if new_early and not (allow_agent_reviews and valid_agent_review(new_early)):
                return True
            if old_early and not allow_agent_reviews:
                return True
        old = {entry["notion"]: entry for entry in before.get("foundations", [])}
        new = {entry["notion"]: entry for entry in after.get("foundations", [])}
        for notion, entry in old.items():
            if (
                entry.get("confirmed_by")
                or (entry.get("status") == "confirmed" and not entry.get("confirmation"))
            ) and new.get(notion) != entry:
                return True
        for notion, entry in new.items():
            previous = old.get(notion, {})
            if entry.get("confirmed_by") != previous.get("confirmed_by"):
                return True
            if entry.get("status") == "confirmed" and entry != previous:
                if not (allow_agent_reviews and foundation_confirmed(entry, policy=policy)):
                    return True
            if entry.get("confirmation") != previous.get("confirmation"):
                if not allow_agent_reviews:
                    return True
                if entry.get("confirmation") and not foundation_confirmed(entry, policy=policy):
                    return True
        return False
    previous = before.get("dispute")
    current = after.get("dispute")
    old_history = before.get("dispute_history", [])
    new_history = after.get("dispute_history", [])
    reopening = (
        previous
        and previous.get("status") == "resolved"
        and current
        and current.get("status") == "open"
        and new_history == old_history + [previous]
    )
    if not reopening and old_history != new_history:
        return True
    if reopening or previous is None:
        if current and (
            current.get("status") != "open"
            or any(key in current for key in ("confirmed_by", "confirmed_on", "resolution"))
        ):
            return True
    elif previous:
        if current is None or any(
            previous.get(key) != current.get(key)
            for key in ("status", "confirmed_by", "confirmed_on", "resolution")
        ):
            return True
    old_lock = before.get("fidelity", {}).get("reviewed")
    new_lock = after.get("fidelity", {}).get("reviewed")
    return bool(
        old_lock != new_lock
        and (
            (old_lock and old_lock.get("kind") == "human")
            or (new_lock and new_lock.get("kind") == "human")
        )
    )


def new_node_allowed(
    path: str, metadata: dict[str, Any], record: dict[str, Any], scopes: set[str]
) -> bool:
    """Allow only stage-specific new leaves, with fixed parent/chapter boundaries."""
    info = record["metadata"]["homalg"]
    key, stage = info["doc"], info["stage"]
    if not path.startswith(f"HomAlg/{key}/") or metadata["doc"] != key:
        return False
    local = metadata["id"].split(".", 1)[1]
    if stage == "INV":
        chapter = str(info.get("chapter", ""))
        section = info.get("section")
        return (
            metadata["source"].get("chapter", "") == chapter
            and (section is None or metadata["source"].get("section") == section)
            and not metadata["decls"]
        )
    if stage == "DAG" and local.startswith("Cited_"):
        return "cited" in metadata and not metadata["decls"]
    if stage in {"DAG", "STMT", "PROOF"} and local.startswith(("Aux_", "Bridge_")):
        parent = metadata.get("aux", {}).get("parent", "")
        parent_path = "HomAlg/" + parent.replace(".", "/", 1) + ".lean"
        parent_local = parent.split(".", 1)[-1]
        return parent_path in scopes and local.startswith(
            (f"Aux_{parent_local}_", f"Bridge_{parent_local}_")
        )
    return False


def changed_paths(repo: Path, since: str, until: str) -> list[str]:
    """Compare immutable commits without allowing git-option injection."""
    for ref in (since, until):
        if not re.fullmatch(r"[0-9a-f]{40,64}", ref):
            raise ValueError("Session bounds must be full hexadecimal ledger commit ids")
        ledger(repo, "cat-file", "-e", ref + "^{commit}")
    return sorted(
        set(ledger(repo, "diff", "--name-only", "-z", since, until, "--").stdout.split("\0")) - {""}
    )


def check_scope(repo: Path, task_id: str, since: str, until: str) -> list[str]:
    """Return forbidden paths; the CLI emits the protocol's exit code four on violations."""
    record = task(repo, task_id)
    key = record["metadata"]["homalg"]["doc"]
    scopes = set(record.get("write_set", {}).get("files", record.get("scope", {}).get("files", [])))
    if any("*" in path or "?" in path or ".." in Path(path).parts for path in scopes):
        raise ValueError("HomAlg tasks must have explicit, repository-relative file scopes")
    schemas = SchemaStore(repo / "schema")
    from homalg.review_policy import agent_reviews_allowed

    policy_file = "horizon/review-policy.yaml"
    policy_blob = ledger(repo, "show", f"{since}:{policy_file}", check=False)
    policy = load_yaml(policy_blob.stdout) if policy_blob.returncode == 0 else {}
    allow_agent_reviews = agent_reviews_allowed(policy=policy)
    violations = []
    for path in changed_paths(repo, since, until):
        old_result = ledger(repo, "show", f"{since}:{path}", check=False)
        new_result = ledger(repo, "show", f"{until}:{path}", check=False)
        old_text = old_result.stdout if old_result.returncode == 0 else None
        new_text = new_result.stdout if new_result.returncode == 0 else None
        allowed = path in scopes
        if path in {"HomAlg.lean", f"HomAlg/{key}.lean", f"literature/{key}/nodes.json"}:
            allowed = True
        if path.startswith(("blueprint/", "hgraph/", ".archon-horizon/")):
            allowed = True
        if path == f"literature/{key}/hollow-allow.yaml":
            allowed = True
        try:
            if path in {
                "taxonomy/tags.yaml",
                "taxonomy/concepts.yaml",
                f"taxonomy/relations/{key}.yaml",
                f"literature/{key}/retired.yaml",
            }:
                field = "relations" if "/relations/" in path else Path(path).stem
                old = (
                    load_yaml(old_text)
                    if old_text is not None
                    else {"schema_version": 1, field: []}
                )
                new = load_yaml(new_text) if new_text is not None else {}
                allowed = append_only(old, new, field)
                if field == "relations":
                    allowed &= all(
                        item.get("review", {}).get("status") == "unreviewed"
                        for item in new.get(field, [])
                    )
            elif path == f"literature/{key}/document.yaml":
                old = load_yaml(old_text) if old_text else {}
                new = load_yaml(new_text) if new_text else {}
                allowed &= not human_fields_changed(
                    old, new, document=True, allow_agent_reviews=allow_agent_reviews
                )
            elif re.fullmatch(r"HomAlg/[^/]+/[^/]+\.lean", path):
                old = parse_header(old_text).metadata if old_text is not None else {}
                new = parse_header(new_text).metadata if new_text is not None else {}
                if new and schemas.validate(new, "node-header.strict.schema.json"):
                    allowed = False
                elif old_text is None and new:
                    allowed |= new_node_allowed(path, new, record, scopes)
                allowed &= not human_fields_changed(old, new)
        except (ValueError, TypeError, KeyError):
            allowed = False
        # Reuse the same document-path projection as PR classification/touch-scope.
        foreign = document_keys([path], include_fixtures=True) - {key}
        if foreign or not allowed or path == policy_file:
            violations.append(path)
    return sorted(set(violations))
