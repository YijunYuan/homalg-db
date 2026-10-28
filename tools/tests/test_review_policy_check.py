"""Compiled validation independently enforces opted-in review provenance and freshness."""

from pathlib import Path

from homalg.checks.context import Context
from homalg.checks.review_policy import check
from homalg.review_policy import foundation_hash
from homalg.schemas import SchemaStore


def test_policy_validation_rejects_stale_and_unauthorized_foundations(repo: Path) -> None:
    """Writing a plausible confirmed status is insufficient without current approved evidence."""
    entry = {
        "notion": "Vector spaces",
        "mathlib": ["Module"],
        "justification": "Elementary background",
        "evidence": "Source page 1",
        "status": "confirmed",
    }
    entry["confirmation"] = {
        "kind": "agent",
        "status": "satisfactory",
        "by": "reviewer",
        "on": "2026-10-28",
        "session": "review-session",
        "author_session": "author-session",
        "content_sha256": foundation_hash(entry),
    }
    ctx = Context(repo=repo, schemas=SchemaStore(repo / "schema"))
    ctx.docs = {"Example2000": {"foundations": [entry]}}
    assert len(check(ctx)) == 1
    policy = repo / "horizon/review-policy.yaml"
    policy.parent.mkdir()
    policy.write_text("schema_version: 1\nallow_independent_agent_reviews: true\n")
    assert not check(ctx)
    entry["evidence"] = "Changed source claim"
    assert len(check(ctx)) == 1
    policy.write_text("schema_version: 1\nallow_independent_agent_reviews: 'yes'\n")
    findings = check(ctx)
    assert len(findings) == 1 and "Invalid review policy" in findings[0].message
