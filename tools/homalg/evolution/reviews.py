"""Independent evolution reviews bound to public reports and exact reviewed content."""

import hashlib
import re
from pathlib import Path
from typing import Any

from homalg.io import json_text
from homalg.review_policy import (
    agent_review_record,
    agent_reviews_allowed,
    require_report_provenance,
)


def subject_hash(subject: dict[str, Any]) -> str:
    """Exclude only the mutable verdict; changed assertions invalidate the review."""
    return hashlib.sha256(
        json_text({key: value for key, value in subject.items() if key != "review"}).encode()
    ).hexdigest()


def independent_review(
    repo: Path,
    subject: dict[str, Any],
    identifier: str,
    *,
    status: str,
    by: str,
    session: str,
    author_session: str,
    report: Path,
    note: str | None = None,
) -> dict[str, Any]:
    """Require distinct sessions, explicit source checking and content-bound evidence."""
    evidence = agent_review_record(
        repo, by=by, session=session, author_session=author_session, note=note or ""
    )
    path = (repo / report).resolve()
    relative = path.relative_to(repo.resolve())
    if any(
        part in {"build", ".private", ".homalg", ".archon-horizon", "references"}
        for part in relative.parts
    ):
        raise ValueError("Evolution review reports must be public authored evidence")
    text = path.read_text()
    require_report_provenance(text, session=session, author_session=author_session)
    expected = {
        "Subject": identifier,
        "Subject-sha256": subject_hash(subject),
        "Verdict": "satisfactory" if status == "accepted" else "unsatisfactory",
        "Assertions-checked": "yes",
    }
    if subject.get("provenance", {}).get("bundle_sha256"):
        expected["Bundle-sha256"] = subject["provenance"]["bundle_sha256"]
    for label, value in expected.items():
        lines = re.findall(rf"(?mi)^{re.escape(label)}:\s*([^\n]+)$", text)
        if lines != [value]:
            raise ValueError(f"Review report must contain exactly {label}: {value}")
    if not re.search(r"(?mi)^Source-evidence:\s*\S", text):
        raise ValueError("Review report must identify Source-evidence")
    return evidence | {
        "status": status,
        "report": relative.as_posix(),
        "report_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "subject_sha256": subject_hash(subject),
    }


def validate_review(subject: dict[str, Any], repo: Path | None = None) -> None:
    """Reject stale agent verdicts; do not silently promote or rewrite historical decisions."""
    record = subject.get("review", {})
    if record.get("kind") != "agent":
        return
    if repo is not None and not agent_reviews_allowed(repo):
        raise ValueError("Independent evolution review substitution is disabled")
    if not record.get("session") or record.get("session") == record.get("author_session"):
        raise ValueError("Evolution review sessions must be independent")
    if record.get("subject_sha256") != subject_hash(subject):
        raise ValueError("Evolution agent review is stale: reviewed assertions changed")
    if repo is not None:
        path = (repo / record["report"]).resolve()
        if not path.is_relative_to(repo.resolve()) or not path.is_file():
            raise ValueError("Evolution review report is missing or outside the repository")
        if hashlib.sha256(path.read_bytes()).hexdigest() != record.get("report_sha256"):
            raise ValueError("Evolution agent review report changed; review again")
