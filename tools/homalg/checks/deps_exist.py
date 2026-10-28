"""Reject references to missing node files."""

from homalg.checks.context import Context, Finding


def check(ctx: Context) -> list[Finding]:
    """Resolve dependencies against the entire checkout, including other documents."""
    findings = []
    for path, header in ctx.valid_headers.items():
        for targets in header.metadata.get("deps", {}).values():
            for target in targets:
                doc, local = target.split(".")
                if not (ctx.repo / "HomAlg" / doc / f"{local}.lean").is_file():
                    findings.append(
                        Finding(
                            "deps-exist",
                            "error",
                            path,
                            f"Missing dependency {target}",
                            header.yaml_line,
                        )
                    )
    return findings
