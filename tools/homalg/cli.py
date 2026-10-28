"""Command-line entry points with stable machine reports and exit codes (R7.0)."""

from dataclasses import asdict
from functools import wraps
from pathlib import Path
from typing import Any

import click

from homalg import __version__
from homalg.checks.context import Finding
from homalg.extract import extract_document
from homalg.io import atomic_write, json_text
from homalg.leanexport import ExternalToolError
from homalg.repository import documents, find_repo
from homalg.roots import generate_roots, stale_roots
from homalg.schemas import SchemaStore
from homalg.validate import validate_repo


def report(
    command: str,
    findings: list[Finding],
    data: dict[str, Any],
    *,
    machine: bool,
    strict: bool = False,
    skipped: list[str] | None = None,
    exit_code: int = 0,
) -> int:
    """Emit the common envelope and return the exit status."""
    errors = sum(finding.severity == "error" for finding in findings)
    warnings = sum(finding.severity == "warning" for finding in findings)
    code = exit_code or (1 if errors or (strict and warnings) else 0)
    payload = {
        "command": command,
        "ok": code == 0,
        "findings": [
            {key: value for key, value in asdict(finding).items() if value is not None}
            for finding in findings
        ],
        "summary": {"errors": errors, "warnings": warnings, "skipped": skipped or []},
        "data": data,
    }
    if machine:
        click.echo(json_text(payload), nl=False)
    else:
        for finding in findings:
            where = f"{finding.file}:{finding.line}" if finding.line else finding.file
            click.echo(f"{where}: {finding.severity} [{finding.rule}] {finding.message}", err=True)
        click.echo(f"{command}: {errors} error(s), {warnings} warning(s)", err=True)
        if skipped:
            click.echo(
                f"Check coverage: {len(skipped)} checks skipped for this context; "
                "see docs/IMPLEMENTATION.md.",
                err=True,
            )
        if data:
            click.echo(json_text(data), nl=False)
    return code


class ReportingGroup(click.Group):
    """Render configuration/usage failures as JSON when requested."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """Remember output intent before parsing either parent or command options."""
        ctx.meta["machine"] = "--json" in args
        try:
            return super().parse_args(ctx, args)
        except click.ClickException as exc:
            ctx.exit(
                report(
                    "homalg",
                    [Finding("configuration", "error", "", str(exc))],
                    {},
                    machine=ctx.meta["machine"],
                    exit_code=2,
                )
            )

    def invoke(self, ctx: click.Context) -> Any:
        """Catch command-level failures without obscuring programming errors."""
        try:
            return super().invoke(ctx)
        except (click.exceptions.Exit, click.Abort):
            raise
        except ExternalToolError as exc:
            click.echo(exc.output, err=True)
            ctx.exit(
                report(
                    ctx.invoked_subcommand or "homalg",
                    [Finding(exc.rule, "error", "lakefile.toml", str(exc))],
                    {},
                    machine=ctx.meta.get("machine", False),
                    exit_code=3,
                )
            )
        except (click.ClickException, ValueError, OSError, RuntimeError) as exc:
            machine = ctx.meta.get("machine", False)
            command = ctx.invoked_subcommand or "homalg"
            code = (
                3
                if isinstance(exc, RuntimeError)
                or (isinstance(exc, FileNotFoundError) and exc.filename == "lake")
                else 2
            )
            findings = [Finding("configuration", "error", "", str(exc))]
            ctx.exit(report(command, findings, {}, machine=machine, exit_code=code))


def common_options(function: Any) -> Any:
    """Attach options shared by every implemented command."""

    @click.option(
        "--repo",
        type=click.Path(path_type=Path, file_okay=False),
        help="Checkout root; by default search upward from the working directory.",
    )
    @click.option("--json", "machine", is_flag=True, help="Write a machine-readable JSON report.")
    @click.option("--strict", is_flag=True, help="Fail on warnings as well as errors.")
    @click.pass_context
    @wraps(function)
    def wrapped(
        ctx: click.Context, repo: Path | None, machine: bool, strict: bool, **kwargs: Any
    ) -> Any:
        if isinstance(ctx.command, click.Group):
            if repo is not None:
                ctx.meta["repo"] = repo
            ctx.meta["machine"] = machine or ctx.meta.get("machine", False)
            ctx.meta["strict"] = strict or ctx.meta.get("strict", False)
            return function(ctx, repo, machine, strict, **kwargs)
        machine = machine or ctx.meta.get("machine", False)
        strict = strict or ctx.meta.get("strict", False)
        ctx.meta["machine"] = machine
        return function(ctx, find_repo(repo or ctx.meta.get("repo")), machine, strict, **kwargs)

    return wrapped


@click.group(cls=ReportingGroup)
@click.version_option(__version__)
def cli() -> None:
    """HomAlgDB: source-faithful Lean literature metadata.

    Parse source metadata, validate Lean evidence and generate the database and site.
    """


class ValidateCommand(click.Command):
    """Retain --file/--as ordering so each optional alias applies to its preceding file."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        ctx.meta["validation_args"] = list(args)
        return super().parse_args(ctx, args)


@cli.command("validate", cls=ValidateCommand)
@common_options
@click.option("--doc", "selected", multiple=True, help="Validate only this document (repeatable).")
@click.option("--fast", is_flag=True, help="Skip the Lean build.")
@click.option("--changed", is_flag=True)
@click.option("--file", "files", multiple=True, type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--as", "aliases", multiple=True, help="Logical repository path for the preceding file."
)
@click.option("--pr-base")
@click.option("--pr-author")
@click.option("--pr-labels", default="")
@click.option("--pr-created-at")
@click.option("--pr-number", type=int)
@click.option("--pr-head")
@click.option("--only", multiple=True, help="Rule ids; repeat or separate with commas.")
@click.option("--now")
@click.option("--no-build", is_flag=True)
@click.option("--export", type=click.Path(path_type=Path, exists=True, dir_okay=False))
def validate_command(
    ctx: click.Context,
    repo: Path,
    machine: bool,
    strict: bool,
    selected: tuple[str, ...],
    fast: bool,
    changed: bool,
    files: tuple[Path, ...],
    aliases: tuple[str, ...],
    pr_base: str | None,
    pr_author: str | None,
    pr_labels: str,
    pr_created_at: str | None,
    pr_number: int | None,
    pr_head: str | None,
    only: tuple[str, ...],
    now: str | None,
    no_build: bool,
    export: Path | None,
) -> None:
    """Check authored inputs, compiled facts, review evidence and available PR context."""
    sources: list[Path | tuple[Path, str]] = []
    arguments = iter(ctx.meta.get("validation_args", []))
    for argument in arguments:
        if argument == "--file" or argument.startswith("--file="):
            sources.append(Path(next(arguments) if argument == "--file" else argument[7:]))
        elif argument == "--as" or argument.startswith("--as="):
            alias = next(arguments) if argument == "--as" else argument[5:]
            if not sources or isinstance(sources[-1], tuple):
                raise click.UsageError("Each --as must follow a separate --file")
            sources[-1] = (sources[-1], alias)
    findings, skipped, data = validate_repo(
        repo,
        selected,
        fast=fast,
        changed=changed,
        files=tuple(sources),
        pr_base=pr_base,
        pr_author=pr_author,
        pr_labels=tuple(label for label in pr_labels.split(",") if label),
        pr_created_at=pr_created_at,
        pr_number=pr_number,
        pr_head=pr_head,
        now=now,
        only=tuple(rule for group in only for rule in group.split(",") if rule),
        no_build=no_build,
        export=export,
    )
    ctx.exit(
        report(
            "validate",
            findings,
            data,
            machine=machine,
            strict=strict,
            skipped=sorted(skipped),
        )
    )


@cli.command("extract")
@common_options
@click.option("--doc", "selected", multiple=True, help="Extract only this document (repeatable).")
def extract_command(
    ctx: click.Context, repo: Path, machine: bool, strict: bool, selected: tuple[str, ...]
) -> None:
    """Regenerate authored nodes.json records, retaining existing derived data."""
    schemas = SchemaStore(repo / "schema")
    # Parse every selected document before writing any file.
    results = {key: extract_document(repo, key, schemas) for key in documents(repo, selected)}
    paths = []
    for key, result in results.items():
        path = repo / "literature" / key / "nodes.json"
        atomic_write(path, json_text(result))
        paths.append(path.relative_to(repo).as_posix())
    ctx.exit(report("extract", [], {"files": paths}, machine=machine, strict=strict))


@cli.command("gen-roots")
@common_options
@click.option("--doc", "selected", multiple=True, help="Regenerate only this document root.")
@click.option(
    "--out",
    type=click.Path(path_type=Path, file_okay=False),
    help="Write to a mirrored directory instead of the checkout.",
)
def roots_command(
    ctx: click.Context,
    repo: Path,
    machine: bool,
    strict: bool,
    selected: tuple[str, ...],
    out: Path | None,
) -> None:
    """Generate the library root and document roots from the registered nodes."""
    roots = generate_roots(repo, selected)
    stale = stale_roots(repo, selected)
    destination = out or repo
    # All DocKey root modules are generated artifacts by contract R3.1.
    for relative in stale:
        (destination / relative).unlink(missing_ok=True)
    for relative, content in roots.items():
        atomic_write(destination / relative, content)
    ctx.exit(report("gen-roots", [], {"files": sorted(roots)}, machine=machine, strict=strict))


def main() -> None:
    """Installed console-script entry point."""
    cli()


from homalg.cli_authoring import register_commands as register_authoring  # noqa: E402
from homalg.cli_collaboration import register_commands as register_collaboration  # noqa: E402
from homalg.cli_engine import register_commands as register_engine  # noqa: E402
from homalg.cli_evolution import register_commands as register_evolution  # noqa: E402
from homalg.cli_lifecycle import register_commands as register_lifecycle  # noqa: E402
from homalg.cli_literature import register_commands as register_literature  # noqa: E402
from homalg.cli_pipeline import register_commands as register_pipeline  # noqa: E402
from homalg.cli_serve import register_commands as register_serve  # noqa: E402

register_pipeline(cli)
register_collaboration(cli)
register_authoring(cli)
register_literature(cli)
register_engine(cli)
register_evolution(cli)
register_lifecycle(cli)
register_serve(cli)
