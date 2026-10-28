"""The deps-acyclic validation rule."""

from homalg.checks.context import Context, Finding
from homalg.checks.text_rules import graph_check


def check(ctx: Context) -> list[Finding]:
    """Validate shared graph or vocabulary facts."""
    return graph_check(ctx, documents=False)
