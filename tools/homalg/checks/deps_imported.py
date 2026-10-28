"""Require direct imports for the document's declared proof route."""

from homalg.checks.context import Context, Finding
from homalg.headers import imports_of


def check(ctx: Context) -> list[Finding]:
    """Planned nodes have no Lean imports and are explicitly exempt."""
    findings = []
    for path, header in ctx.valid_headers.items():
        if not header.metadata.get("decls"):
            continue
        imports = set(imports_of(ctx.sources[path]))
        for targets in header.metadata.get("deps", {}).values():
            for target in targets:
                if f"HomAlg.{target}" not in imports:
                    findings.append(
                        Finding(
                            "deps-imported",
                            "error",
                            path,
                            f"Directly import HomAlg.{target}",
                            header.yaml_line,
                        )
                    )
    return findings
