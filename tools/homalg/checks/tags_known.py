"""The tags-known validation rule."""

from homalg.checks.context import Context, Finding
from homalg.checks.text_rules import vocabulary


def check(ctx: Context) -> list[Finding]:
    """Validate shared graph or vocabulary facts."""
    return vocabulary(ctx, concepts=False)
