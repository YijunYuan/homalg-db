"""Claim expiry, ownership, round-trip metadata and takeover regression tests."""

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from homalg.claims import claim_state, claim_view, effective_expiry, instant, transition
from homalg.documents import dump_metadata, parse_metadata
from homalg.schemas import SchemaStore

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = SchemaStore(ROOT / "schema")


def test_released_claim_retains_queried_pr_link() -> None:
    """A release removes ownership, not the most recent formalization PR navigation link."""
    value = {"schema_version": 1, "doc_key": "Example2000", "claims": []}
    assert claim_view(value, [], "2026-01-01T00:00:00Z", pr=42) == {"state": "unclaimed", "pr": 42}


def claim(holder: str = "alice") -> dict:
    """Build a ten-day synthetic claim."""
    return {
        "schema_version": 1,
        "doc_key": "Example2000",
        "claims": [
            {
                "holder": holder,
                "claimed_at": "2026-01-01T00:00:00Z",
                "expires_at": "2026-01-11T00:00:00Z",
                "scope": {"chapters": [], "sections": []},
            }
        ],
    }


def status(at: str, holder: str = "alice") -> dict:
    """Produce an independently valid numeric publication."""
    counts = {
        key: 0
        for key in SCHEMAS.schemas["run-status.schema.json"]["properties"]["counts"]["required"]
    }
    for field in ("headline", "aux_headline", "cited_headline"):
        counts[field] = {
            key: 0 for key in ("in_progress", "statement_complete", "proof_complete", "error")
        }
    return {
        "schema_version": 1,
        "doc_key": "Example2000",
        "holder": holder,
        "generated_at": at,
        "scope_chapters": [],
        "counts": counts,
        "stages": {},
        "last_check": {"result": "none", "at": None},
        "open_for_human": 0,
    }


def test_activity_extends_past_nominal_expiry_in_timestamp_order() -> None:
    """Commit order must not affect an unbroken chain of valid activity."""
    history = [status("2026-01-20T00:00:00Z"), status("2026-01-10T00:00:00Z")]
    assert effective_expiry(claim()["claims"][0], history, "2026-01-21T00:00:00Z") == instant(
        "2026-02-03T00:00:00Z"
    )
    assert claim_state(claim(), history, "2026-01-21T00:00:00Z") == "active"
    assert claim_state(claim(), history, "2026-02-03T00:00:00Z") == "expired"


def test_late_activity_cannot_resurrect_expired_claim() -> None:
    """A gap after expiry remains expired regardless of later publications."""
    history = [status("2026-01-12T00:00:00Z"), status("2026-01-20T00:00:00Z")]
    assert effective_expiry(claim()["claims"][0], history, "2026-01-21T00:00:00Z") == instant(
        "2026-01-11T00:00:00Z"
    )


@pytest.mark.parametrize(
    "publication",
    [
        status("2026-01-10T00:00:00Z", "bob"),
        status("2025-12-31T00:00:00Z"),
        status("2026-01-10T00:11:00Z"),
        {"holder": "alice", "generated_at": "2026-01-10T00:00:00Z"},
        status("2026-01-10T00:00:00Z") | {"doc_key": "Different2000"},
    ],
)
def test_invalid_activity_is_ignored(publication: dict) -> None:
    """A status branch cannot extend someone else's or another document's claim."""
    assert effective_expiry(
        claim()["claims"][0], [publication], "2026-01-10T00:00:00Z", doc_key="Example2000"
    ) == instant("2026-01-11T00:00:00Z")


def test_small_clock_skew_is_clamped_and_boundary_activity_is_allowed() -> None:
    """At most ten minutes of skew is accepted but cannot extend from a future time."""
    entry = status("2026-01-10T00:10:00Z")
    assert effective_expiry(claim()["claims"][0], [entry], "2026-01-10T00:00:00Z") == instant(
        "2026-01-24T00:00:00Z"
    )
    entry = status("2026-01-11T00:00:00Z")
    assert effective_expiry(claim()["claims"][0], [entry], "2026-01-11T00:00:00Z") == instant(
        "2026-01-25T00:00:00Z"
    )


def test_takeover_uses_activity_expiry_and_does_not_mutate_inputs() -> None:
    """The same effective expiry drives displayed state and takeover permission."""
    original = claim()
    history = [status("2026-01-10T00:00:00Z")]
    with pytest.raises(ValueError, match="actively claimed"):
        transition(original, "take", "bob", "2026-01-23T00:00:00Z", status_log=history)
    result = transition(original, "take", "bob", "2026-01-24T00:00:00Z", status_log=history)
    assert result["claims"][0]["holder"] == "bob"
    assert original == claim()


def test_renew_only_changes_expiry_and_release_checks_owner() -> None:
    """Renewals preserve claim identity, notes, scopes and arbitrary YAML comments."""
    old = claim()
    result = transition(old, "renew", "alice", "2026-01-10T00:00:00Z", days=30)
    expected = deepcopy(old)
    expected["claims"][0]["expires_at"] = "2026-02-09T00:00:00Z"
    assert result == expected
    with pytest.raises(ValueError, match="holder"):
        transition(old, "renew", "bob", "2026-01-10T00:00:00Z")
    with pytest.raises(ValueError, match="holder"):
        transition(old, "release", "bob", "2026-01-10T00:00:00Z")
    assert transition(old, "release", "alice", "2026-01-10T00:00:00Z")["claims"] == []


def test_claim_limit_counts_pending_requests_and_renewals() -> None:
    """Concurrent requests count toward the same limit as already active claims."""
    empty = claim() | {"claims": []}
    with pytest.raises(ValueError, match="limit"):
        transition(
            empty,
            "take",
            "alice",
            "2026-01-10T00:00:00Z",
            active_other_claims=1,
            pending_other_claims=1,
        )
    assert transition(claim(), "renew", "alice", "2026-01-10T00:00:00Z", active_other_claims=1)
    with pytest.raises(ValueError, match="duration"):
        transition(empty, "take", "alice", "2026-01-10T00:00:00Z", days=91)


def test_view_conforms_to_contract_and_omits_expired_run() -> None:
    """The index shape uses the exact shared state and exposes only current activity."""
    data = claim_view(claim(), [status("2026-01-10T00:00:00Z")], "2026-01-20T00:00:00Z", pr=12)
    assert data["state"] == "active" and data["pr"] == 12 and data["run"]
    assert data["effective_expires_at"] == "2026-01-24T00:00:00Z"
    assert "run" not in claim_view(claim(), [], "2026-01-20T00:00:00Z")
    assert claim_view(claim() | {"claims": []}, [], datetime.now(UTC)) == {"state": "unclaimed"}


def test_roundtrip_preserves_comments_and_quotes() -> None:
    """Editing a timestamp must retain contributor notes and avoid YAML date coercion."""
    source = (
        '# contributor note\nschema_version: 1\ndoc_key: "Example2000" # identity\nclaims: []\n'
    )
    data = parse_metadata(source)
    data["note"] = "2026-01-01"
    rendered = dump_metadata(data)
    assert "# contributor note" in rendered and "# identity" in rendered
    assert 'note: "2026-01-01"' in rendered
    assert parse_metadata(rendered)["note"] == "2026-01-01"
