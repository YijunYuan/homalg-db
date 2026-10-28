"""Pull-request policy checks against current main, live reviews and pending claims."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from homalg.checks.context import Finding
from homalg.claims import claim_view, instant, load_status_history
from homalg.classify import (
    append_only,
    approval_reasons,
    document_keys,
    owner_approved,
)
from homalg.collaboration import (
    Client,
    active_claim_count,
    changed_paths,
    classify_repository,
    main_claim,
    pending_claim_count,
    policy_for,
)
from homalg.schemas import SchemaStore, load_yaml


def pr_findings(
    repo: Path,
    *,
    base: str,
    author: str,
    labels: list[str] | tuple[str, ...] = (),
    created_at: str | None = None,
    number: int | None = None,
    head: str = "HEAD",
    now: str | datetime | None = None,
    owner: str | None = None,
    owner_only: bool = False,
    client: Client | None = None,
) -> list[Finding]:
    """Evaluate collaboration policy; owner approval runs only when explicitly requested."""
    client = client or Client(repo)
    current = instant(now or datetime.now(UTC))
    owner = owner or os.getenv("HOMALG_OWNER", "")
    schemas = SchemaStore(repo / "schema")
    merge_base = client.git("merge-base", base, head).strip()
    files = [path for path in changed_paths(client, merge_base, head) if path]
    classification = classify_repository(client, merge_base, list(labels), head)
    findings: list[Finding] = []

    def error(rule: str, path: str, message: str, severity: str = "error") -> None:
        findings.append(Finding(rule, severity, path, message))

    def before(path: str) -> str | None:
        return client.blob(merge_base, path)

    def after(path: str) -> str | None:
        return client.blob(head, path)

    def yaml_at(path: str, old: bool = False) -> dict[str, Any]:
        text = before(path) if old else after(path)
        if text is None:
            return {}
        value = load_yaml(text)
        if not isinstance(value, dict):
            raise ValueError(f"Expected metadata mapping: {path}")
        return value

    from homalg.review_policy import foundation_confirmed

    review_policy = yaml_at("horizon/review-policy.yaml", old=True)

    if owner_only:
        reasons = approval_reasons(
            files,
            before,
            after,
            labels=labels,
            classification=classification,
            review_policy=review_policy,
        )
        if not reasons:
            return []
        if not owner:
            error("owner-approval", "", "HOMALG_OWNER is required for sensitive changes")
            return findings
        if owner.lower() == author.lower():
            return []
        if number is None:
            error("owner-approval", "", "PR number is required to verify owner approval")
            return findings
        repository = json.loads(client.gh("repo", "view", "--json", "nameWithOwner"))[
            "nameWithOwner"
        ]
        reviews = client.api(f"repos/{repository}/pulls/{number}/reviews")
        head_sha = client.git("rev-parse", head).strip()
        if not owner_approved(owner, author, head_sha, reviews):
            error(
                "owner-approval",
                "",
                f"Owner approval on {head_sha} is required: {', '.join(reasons)}",
            )
        return findings

    if number is not None:
        repository = json.loads(client.gh("repo", "view", "--json", "nameWithOwner"))[
            "nameWithOwner"
        ]
        request = client.api(f"repos/{repository}/pulls/{number}")
        if request.get("head", {}).get("repo", {}).get("full_name") != request.get("base", {}).get(
            "repo", {}
        ).get("full_name"):
            error(
                "collaborator-only",
                "",
                "Fork PRs are not supported; contributors need collaborator access",
            )
        if request.get("head", {}).get("ref", "").startswith("status/"):
            error("touch-scope", "", "status branches are not merged")
    else:
        repository = ""

    maintenance = "taxonomy-maintenance" in labels
    for path, field in (("taxonomy/tags.yaml", "tags"), ("taxonomy/concepts.yaml", "concepts")):
        if (
            path in files
            and not maintenance
            and not append_only(yaml_at(path, True), yaml_at(path), field)
        ):
            error(
                "taxonomy-append-only",
                path,
                "Existing vocabulary entries may not be removed or modified",
            )
    for path in files:
        if re.fullmatch(r"taxonomy/relations/[^_][^/]*\.yaml", path) and not maintenance:
            if not append_only(yaml_at(path, True), yaml_at(path), "relations"):
                error(
                    "relation-append-only",
                    path,
                    "Existing relation records may not be removed or modified",
                )
    if classification["kind"] == "multi-doc" and "multi-doc" not in labels and not maintenance:
        error("touch-scope", "", "Changes to multiple documents require the multi-doc label")
    key = classification["doc"]
    if classification["kind"] == "formalization" and "mathlib-bump" not in labels:
        permitted = {
            "HomAlg.lean",
            f"HomAlg/{key}.lean",
            "taxonomy/tags.yaml",
            "taxonomy/concepts.yaml",
            f"taxonomy/relations/{key}.yaml",
        }
        metadata = {
            "document.yaml",
            "claim.yaml",
            "nodes.json",
            "inventory.yaml",
            "notes.md",
            "retired.yaml",
            "hollow-allow.yaml",
        }
        for path in files:
            valid = path in permitted or path.startswith(f"HomAlg/{key}/")
            if path.startswith(f"literature/{key}/"):
                relative = path.removeprefix(f"literature/{key}/")
                valid = relative in metadata or relative.startswith(("reviews/", "run-log/"))
            if "regen" in labels and (
                re.fullmatch(r"literature/[^/]+/nodes\.json", path)
                or re.fullmatch(r"HomAlg/[^/]+\.lean", path)
            ):
                valid = True
            if not valid:
                error("touch-scope", path, f"Path is outside document {key}'s submission scope")
    for doc in document_keys(files):
        path = f"literature/{doc}/document.yaml"
        metadata = yaml_at(path)
        for entry in metadata.get("foundations", []):
            if not foundation_confirmed(entry, policy=review_policy) or not entry.get("evidence"):
                error(
                    "foundations-confirmed",
                    path,
                    "Foundations require source evidence and an authorized current confirmation",
                )

    if classification["kind"] not in {"claim", "formalization"} or key is None:
        return findings
    policy = policy_for(repo, schemas)
    present = client.fetch(key)
    old = main_claim(client, key, schemas)
    history = load_status_history(repo, key, schemas=schemas) if present else []
    view = claim_view(old, history, current, policy=policy, schemas=schemas)
    path = f"literature/{key}/claim.yaml"
    new = yaml_at(path)
    schema_errors = schemas.validate(new, "claim.schema.json")
    if schema_errors or new.get("doc_key") != key:
        error(
            "claim-schema", path, "Claim must satisfy its schema and match the containing document"
        )
        return findings
    old_entry = old["claims"][0] if old["claims"] else None
    new_entry = new["claims"][0] if new["claims"] else None
    is_owner = bool(owner) and owner.lower() == author.lower()
    if classification["kind"] == "claim":
        if set(files) != {path}:
            error("claim-files-only", path, "Claim PR must change only its claim.yaml")
        if new_entry and new_entry["holder"].lower() != author.lower():
            error("claim-author", path, "A claim may only be added or modified by its holder")
        if (
            old_entry
            and old_entry != new_entry
            and view["state"] == "active"
            and old_entry["holder"].lower() != author.lower()
            and not is_owner
        ):
            error("claim-author", path, "Another contributor's active claim cannot be replaced")
        renewal = (
            old_entry
            and new_entry
            and old_entry["holder"] == new_entry["holder"]
            and old_entry["claimed_at"] == new_entry["claimed_at"]
        )
        if new_entry:
            started, expiry = instant(new_entry["claimed_at"]), instant(new_entry["expires_at"])
            if (
                not renewal
                and not current - timedelta(hours=policy["claimed_at_window_hours"])
                <= started
                <= current
            ):
                error("claim-window", path, "New claim timestamp is outside the allowed window")
            if expiry <= current or expiry - current > timedelta(days=policy["claim_ttl_days"]):
                error("claim-window", path, "Claim expiry is outside the permitted duration")
        if created_at is None or current - instant(created_at) > timedelta(
            days=policy["claim_pr_max_age_days"]
        ):
            error("claim-window", path, "Claim PR age is missing or exceeds the maximum")
        if new_entry:
            if not repository:
                repository = json.loads(client.gh("repo", "view", "--json", "nameWithOwner"))[
                    "nameWithOwner"
                ]
            active = active_claim_count(client, author, key, current, schemas, policy)
            pending = pending_claim_count(client, repository, author, key, exclude_pr=number)
            if active + pending + 1 > policy["max_active_claims_per_holder"]:
                error("claim-limit", path, "Active plus pending claims exceed the per-holder limit")
    else:
        if view["state"] != "active" or view.get("holder", "").lower() != author.lower():
            error("claim-owner", path, "PR author is not the active claim holder", "warning")
        if path in files and old != new:
            if (
                view["state"] != "active"
                or not old_entry
                or old_entry["holder"].lower() != author.lower()
            ):
                error("claim-sync", path, "Expired claims cannot be renewed by a formalization PR")
            elif new_entry:
                fixed = set(old_entry) | set(new_entry)
                fixed -= {"expires_at", "pr", "scope"}
                if any(old_entry.get(field) != new_entry.get(field) for field in fixed):
                    error(
                        "claim-sync", path, "Formalization may only update expires_at, pr and scope"
                    )
                expiry = instant(new_entry["expires_at"])
                if expiry <= current or expiry - current > timedelta(days=policy["claim_ttl_days"]):
                    error("claim-sync", path, "Renewal exceeds the allowed claim duration")
    return findings
