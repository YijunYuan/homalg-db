"""Validate authored-only node metadata against the strict schema."""

from homalg.checks.context import Context, Finding


def check(ctx: Context) -> list[Finding]:
    """Reject derived or malformed fields with a YAML quoting hint."""
    findings = []
    for path, header in ctx.headers.items():
        for error in ctx.schemas.validate(header.metadata, "node-header.strict.schema.json"):
            hint = (
                "; quote the value"
                if error.validator == "type" and (error.validator_value == "string")
                else ""
            )
            location = ".".join(str(part) for part in error.absolute_path)
            findings.append(
                Finding(
                    "schema-header",
                    "error",
                    path,
                    f"{location or 'header'}: {error.message}{hint}",
                    header.yaml_line,
                )
            )
    return findings
