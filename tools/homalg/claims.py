"""Pure claim transitions and activity-based expiry shared by CLI, CI and indexing."""

from collections.abc import Iterable
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from homalg.schemas import SchemaStore

DEFAULT_POLICY = {
    "schema_version": 1,
    "claim_ttl_days": 90,
    "claim_activity_grace_days": 14,
    "max_active_claims_per_holder": 2,
    "claimed_at_window_hours": 24,
    "claim_pr_max_age_days": 7,
}


def instant(value: str | datetime) -> datetime:
    """Parse a timestamp with an explicit UTC offset and normalize it to UTC."""
    result = (
        datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    )
    if not isinstance(result, datetime) or result.tzinfo is None:
        raise ValueError("An explicit timezone is required")
    return result.astimezone(UTC)


def timestamp(value: datetime) -> str:
    """Write deterministic RFC 3339 UTC timestamps."""
    return instant(value).isoformat(timespec="seconds").replace("+00:00", "Z")


@lru_cache(maxsize=1)
def default_schemas() -> SchemaStore:
    """Load the checkout's schema graph once for standalone pure callers."""
    return SchemaStore(Path(__file__).resolve().parents[2] / "schema")


def valid_statuses(
    claim: dict[str, Any],
    status_log: Iterable[Any],
    now: str | datetime,
    *,
    schemas: SchemaStore | None = None,
    doc_key: str | None = None,
) -> list[tuple[datetime, dict[str, Any]]]:
    """Ignore invalid, foreign-holder, old and excessively future status records."""
    schemas = schemas or default_schemas()
    current = instant(now)
    start = instant(claim["claimed_at"])
    accepted = []
    for status in status_log:
        if schemas.validate(status, "run-status.schema.json"):
            continue
        if status["holder"].lower() != claim["holder"].lower():
            continue
        if doc_key is not None and status["doc_key"] != doc_key:
            continue
        generated = instant(status["generated_at"])
        if generated < start or generated > current + timedelta(minutes=10):
            continue
        accepted.append((min(generated, current), status))
    return sorted(accepted, key=lambda pair: pair[0])


def effective_expiry(
    claim: dict[str, Any],
    status_log: Iterable[Any],
    now: str | datetime,
    *,
    grace_days: int = 14,
    schemas: SchemaStore | None = None,
    doc_key: str | None = None,
) -> datetime:
    """Extend only an unbroken activity chain; a later publication cannot revive expiry."""
    if grace_days < 1:
        raise ValueError("Claim activity grace must be positive")
    expiry = instant(claim["expires_at"])
    if expiry <= instant(claim["claimed_at"]):
        raise ValueError("Claim expiry must follow its start")
    for generated, _ in valid_statuses(claim, status_log, now, schemas=schemas, doc_key=doc_key):
        if generated <= expiry:
            expiry = max(expiry, generated + timedelta(days=grace_days))
    return expiry


def claim_view(
    claim_file: dict[str, Any],
    status_log: Iterable[Any],
    now: str | datetime,
    *,
    policy: dict[str, Any] | None = None,
    schemas: SchemaStore | None = None,
    pr: int | None = None,
) -> dict[str, Any]:
    """Build the published ClaimView with exactly the same expiry used by takeover."""
    schemas = schemas or default_schemas()
    errors = schemas.validate(claim_file, "claim.schema.json")
    if errors:
        raise ValueError(errors[0].message)
    if not claim_file["claims"]:
        return {"state": "unclaimed"} | ({"pr": pr} if pr is not None else {})
    policy = policy or DEFAULT_POLICY
    claim = claim_file["claims"][0]
    history = list(status_log)
    expiry = effective_expiry(
        claim,
        history,
        now,
        grace_days=policy["claim_activity_grace_days"],
        schemas=schemas,
        doc_key=claim_file["doc_key"],
    )
    state = "active" if expiry > instant(now) else "expired"
    result = {key: deepcopy(claim[key]) for key in ("holder", "claimed_at", "expires_at", "scope")}
    result.update(state=state, effective_expires_at=timestamp(expiry))
    if pr is not None:
        result["pr"] = pr
    accepted = valid_statuses(claim, history, now, schemas=schemas, doc_key=claim_file["doc_key"])
    if state == "active" and accepted:
        result["run"] = deepcopy(accepted[-1][1])
    return result


def claim_state(
    claim_file: dict[str, Any],
    status_log: Iterable[Any],
    now: str | datetime,
    *,
    policy: dict[str, Any] | None = None,
    schemas: SchemaStore | None = None,
) -> str:
    """Return unclaimed, active or expired from the shared ClaimView computation."""
    return claim_view(claim_file, status_log, now, policy=policy, schemas=schemas)["state"]


def transition(
    claim_file: dict[str, Any],
    action: str,
    holder: str,
    now: str | datetime,
    *,
    status_log: Iterable[Any] = (),
    policy: dict[str, Any] | None = None,
    days: int | None = None,
    chapters: list[str] | None = None,
    sections: list[str] | None = None,
    note: str = "",
    agent: str | None = None,
    active_other_claims: int = 0,
    pending_other_claims: int = 0,
    owner: bool = False,
    schemas: SchemaStore | None = None,
) -> dict[str, Any]:
    """Apply take/renew/release without mutating inputs; enforce ownership and limits."""
    schemas = schemas or default_schemas()
    policy = policy or DEFAULT_POLICY
    current = instant(now)
    errors = schemas.validate(policy, "policy.schema.json")
    if errors:
        raise ValueError(errors[0].message)
    view = claim_view(claim_file, status_log, current, policy=policy, schemas=schemas)
    previous = claim_file["claims"][0] if claim_file["claims"] else None
    own = previous is not None and previous["holder"].lower() == holder.lower()
    ttl = policy["claim_ttl_days"] if days is None else days
    if action not in {"take", "renew", "release"}:
        raise ValueError(f"Unknown claim action: {action}")
    if (
        not isinstance(ttl, int)
        or isinstance(ttl, bool)
        or not 1 <= ttl <= policy["claim_ttl_days"]
    ):
        raise ValueError(f"Claim duration must be between 1 and {policy['claim_ttl_days']} days")
    if action == "take" and view["state"] == "active":
        raise ValueError(f"Document is actively claimed by {view['holder']}")
    if action == "renew" and not own:
        raise ValueError("Only the claim holder may renew it")
    if action == "release" and previous and not own and not owner and view["state"] == "active":
        raise ValueError("Only the active holder or owner may release this claim")
    if action != "release" and (
        active_other_claims + pending_other_claims + 1 > policy["max_active_claims_per_holder"]
    ):
        raise ValueError("Active and pending claims exceed the per-holder limit")
    result = deepcopy(claim_file)
    if action == "release":
        result["claims"] = []
    elif action == "renew":
        result["claims"][0]["expires_at"] = timestamp(current + timedelta(days=ttl))
    else:
        entry = {
            "holder": holder,
            "claimed_at": timestamp(current),
            "expires_at": timestamp(current + timedelta(days=ttl)),
            "scope": {"chapters": chapters or [], "sections": sections or [], "note": note},
        }
        if agent:
            entry["agent"] = agent
        result["claims"] = [entry]
    errors = schemas.validate(result, "claim.schema.json")
    if errors:
        raise ValueError(errors[0].message)
    return result


def load_status_history(
    repo: Path, key: str, *, schemas: SchemaStore | None = None
) -> list[dict[str, Any]]:
    """Read valid status publications from an already-fetched remote branch, without network I/O."""
    import json
    import subprocess

    from homalg.repository import DOC_KEY

    if not DOC_KEY.fullmatch(key):
        raise ValueError(f"Invalid document key: {key}")
    ref = f"refs/remotes/origin/status/{key}"
    present = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", ref],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if present.returncode == 1:
        return []
    if present.returncode:
        raise ValueError(f"Cannot inspect status branch: {present.stderr.strip()}")
    commits = subprocess.run(
        ["git", "log", "--format=%H", ref, "--", "status.json"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    schemas = schemas or SchemaStore(repo / "schema")
    records = []
    for commit in commits:
        result = subprocess.run(
            ["git", "show", f"{commit}:status.json"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            continue
        try:
            value = json.loads(result.stdout)
        except ValueError:
            continue
        if not schemas.validate(value, "run-status.schema.json") and value["doc_key"] == key:
            records.append(value)
    return sorted(records, key=lambda status: instant(status["generated_at"]))
