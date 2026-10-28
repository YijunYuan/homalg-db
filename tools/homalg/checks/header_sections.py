"""Enforce the required Markdown sections and their canonical ordering."""

from homalg.checks.context import Context, Finding
from homalg.headers import SECTION_FIELDS, THEOREM_KINDS


def check(ctx: Context) -> list[Finding]:
    """Report missing prose as errors and unfinished scaffold prose as warnings."""
    findings = []
    for path, header in ctx.headers.items():
        required = ["Statement", "Description"]
        kind = header.metadata.get("kind")
        if isinstance(kind, str) and kind in THEOREM_KINDS:
            required.append("Proof")
        key = header.metadata.get("doc")
        doc = ctx.docs.get(key, {}) if isinstance(key, str) else {}
        if doc.get("language", "en") != "en":
            required.append("Statement (original)")
        for title in required:
            content = header.sections.get(title, "")
            if not content:
                findings.append(
                    Finding(
                        "header-sections",
                        "error",
                        path,
                        f"Missing or empty ## {title}",
                        header.line,
                    )
                )
            elif any(line.lstrip().startswith("TODO") for line in content.splitlines()):
                findings.append(
                    Finding(
                        "header-sections",
                        "warning",
                        path,
                        f"Unfinished ## {title}",
                        header.section_lines[title],
                    )
                )
        titles = list(header.sections)
        expected = [title for title in SECTION_FIELDS if title in titles]
        if titles != expected:
            findings.append(
                Finding(
                    "header-sections",
                    "error",
                    path,
                    "Use only the standard Markdown sections in canonical order",
                    header.line,
                )
            )
    return findings
