"""Avoid the shared hand-maintained registry prohibited by R3.4."""

from homalg.checks.context import Context, Finding


def check(ctx: Context) -> list[Finding]:
    """The document metadata remains the single source of truth."""
    return (
        [Finding("registry-none", "error", "REGISTRY.md", "Do not maintain a shared registry")]
        if (ctx.repo / "REGISTRY.md").exists()
        else []
    )
