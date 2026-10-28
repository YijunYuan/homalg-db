"""Compare committed root modules with their deterministic generator."""

from homalg.checks.context import Context, Finding
from homalg.roots import generate_roots, stale_roots


def check(ctx: Context) -> list[Finding]:
    """A stale or missing root is an error even when no Lean build is available."""
    findings = []
    try:
        generated = generate_roots(ctx.repo, ctx.selected)
        stale = stale_roots(ctx.repo, ctx.selected)
    except ValueError as error:
        return [Finding("roots-fresh", "error", "HomAlg", str(error))]
    for relative, expected in generated.items():
        path = ctx.repo / relative
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            findings.append(
                Finding(
                    "roots-fresh",
                    "error",
                    relative,
                    "Generated imports are stale",
                    fix="homalg gen-roots",
                )
            )
    for relative in stale:
        findings.append(
            Finding(
                "roots-fresh",
                "error",
                relative,
                "Root has no registered node files",
                fix="homalg gen-roots",
            )
        )
    return findings
