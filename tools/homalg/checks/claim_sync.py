"""The claim-sync validation rule."""

from homalg.checks.context import Context, Finding


def check(ctx: Context) -> list[Finding]:
    """Return diagnostics produced by the shared input or PR context loader."""
    return [item for item in [*ctx.preloaded, *ctx.pr_findings] if item.rule == "claim-sync"]
