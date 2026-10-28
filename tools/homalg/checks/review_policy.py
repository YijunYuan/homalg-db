"""Validate opted-in independent-review provenance and content freshness."""

from homalg.checks.context import Context, Finding
from homalg.review_policy import (
    agent_reviews_allowed,
    early_review_valid,
    foundation_confirmed,
    read_policy,
    valid_agent_review,
)


def check(ctx: Context) -> list[Finding]:
    """Require authorized, current agent evidence while retaining actual human provenance."""
    try:
        policy = read_policy(ctx.repo)
    except (OSError, ValueError) as error:
        return [Finding("review-policy", "error", "horizon/review-policy.yaml", str(error))]
    findings = []
    for key, document in ctx.docs.items():
        path = f"literature/{key}/document.yaml"
        for entry in document.get("foundations", []):
            if entry.get("confirmation") and not foundation_confirmed(entry, policy=policy):
                findings.append(
                    Finding(
                        "review-policy",
                        "error",
                        path,
                        f"Foundation {entry['notion']}: unauthorized or stale agent confirmation",
                    )
                )
        early = document.get("early_review")
        if early and not early_review_valid(early, policy=policy):
            findings.append(
                Finding("review-policy", "error", path, "Early-review provenance is invalid")
            )
    for path, header in ctx.valid_headers.items():
        authored = header.metadata
        review = authored["fidelity"].get("reviewed", {})
        document = ctx.all_docs.get(authored["doc"], {})
        first = (document.get("structure") or [{}])[0].get("chapter")
        first_definition = (
            document.get("type") != "synthetic"
            and first is not None
            and authored["source"].get("chapter") == first
            and authored["kind"] in {"definition", "construction", "notation", "axiom"}
            and "aux" not in authored
            and "cited" not in authored
        )
        if (
            first_definition
            and review.get("kind") == "agent"
            and not (agent_reviews_allowed(policy=policy) and valid_agent_review(review))
        ):
            findings.append(
                Finding(
                    "review-policy",
                    "error",
                    path,
                    "First-chapter definitions need authorized independent-agent or human review",
                )
            )
    return findings
