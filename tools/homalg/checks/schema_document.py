"""Validate document schemas and their path/year invariants."""

import re

from homalg.checks.context import Context, Finding


def check(ctx: Context) -> list[Finding]:
    """Check R6.1 and the DocKey publication year."""
    findings = []
    for key, doc in ctx.docs.items():
        path = f"literature/{key}/document.yaml"
        for error in ctx.schemas.validate(doc, "document.schema.json"):
            findings.append(Finding("schema-document", "error", path, error.message))
        year = re.search(r"[0-9]{4}", key)
        if doc.get("doc_key") != key or (year and doc.get("year") != int(year.group())):
            findings.append(
                Finding(
                    "schema-document",
                    "error",
                    path,
                    "Document key/year must agree with the containing directory",
                )
            )
    return findings
