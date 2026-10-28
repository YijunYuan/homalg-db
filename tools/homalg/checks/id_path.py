"""Enforce the node id/path invariant I-1."""

from pathlib import PurePosixPath

from homalg.checks.context import Context, Finding


def check(ctx: Context) -> list[Finding]:
    """Check the id and document against the flat source path."""
    findings = []
    for path, header in ctx.headers.items():
        source = PurePosixPath(path)
        expected = f"{source.parent.name}.{source.stem}"
        if header.metadata.get("id") != expected or (
            header.metadata.get("doc") != source.parent.name
        ):
            findings.append(
                Finding(
                    "id-path",
                    "error",
                    path,
                    f"Expected id {expected} and doc {source.parent.name}",
                    header.line,
                )
            )
    return findings
