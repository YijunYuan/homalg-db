"""Private literature and visual transcription command registration."""

from pathlib import Path
from typing import Any

import click


def register_commands(cli: click.Group) -> None:
    """Expose implemented private source operations through the shared CLI report."""
    from homalg import literature, transcription
    from homalg.cli import common_options, report

    def done(
        ctx: click.Context, name: str, data: dict[str, Any], machine: bool, strict: bool
    ) -> None:
        ctx.exit(report(name, [], data, machine=machine, strict=strict))

    @cli.group("literature")
    @common_options
    def literature_group(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Manage the private source checkout without exposing its content publicly."""

    @literature_group.command("sync")
    @common_options
    def sync(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Clone or fast-forward the configured private literature repository."""
        done(ctx, "literature sync", {"path": str(literature.checkout(repo))}, machine, strict)

    @literature_group.command("add")
    @common_options
    @click.argument("key")
    @click.option(
        "--pdf", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False)
    )
    def add(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, key: str, pdf: Path
    ) -> None:
        """Copy a registered PDF after verifying its SHA-256."""
        done(
            ctx,
            "literature add",
            {"path": str(literature.add_pdf(repo, key, pdf))},
            machine,
            strict,
        )

    @cli.command("ingest-pdf")
    @common_options
    @click.argument("key")
    @click.option("--pages", help="PDF indices such as 1-5 or 2,4-6.")
    def ingest(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, key: str, pages: str | None
    ) -> None:
        """Render verified PDF pages at 200 dpi; extracted text is navigation-only."""
        done(ctx, "ingest-pdf", literature.ingest_pdf(repo, key, pages=pages), machine, strict)

    @cli.group("transcription")
    @common_options
    def transcription_group(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Land visual transcriptions, review exact page bytes and resolve disputes."""

    @transcription_group.command("status")
    @common_options
    @click.argument("key")
    def status(ctx: click.Context, repo: Path, machine: bool, strict: bool, key: str) -> None:
        """Report page states and reopen pages changed after satisfactory review."""
        done(ctx, "transcription status", transcription.status(repo, key), machine, strict)

    @transcription_group.command("land")
    @common_options
    @click.argument("key")
    @click.option("--pages", required=True)
    @click.option("--session", required=True)
    @click.option("--engine")
    @click.option("--model")
    def land(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, key: str, **options: Any
    ) -> None:
        """Register at most five delivered page files with provenance and byte hashes."""
        done(ctx, "transcription land", transcription.land(repo, key, **options), machine, strict)

    @transcription_group.command("review")
    @common_options
    @click.argument("key")
    @click.option("--pages", required=True)
    @click.option(
        "--status",
        "verdict",
        required=True,
        type=click.Choice(sorted(transcription.REVIEW_STATUSES)),
    )
    @click.option("--by", required=True)
    @click.option("--finding", "findings", multiple=True)
    def review(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, key: str, **options: Any
    ) -> None:
        """Record an independent review of the current landed page bytes."""
        done(
            ctx, "transcription review", transcription.review(repo, key, **options), machine, strict
        )

    @transcription_group.command("resolve")
    @common_options
    @click.argument("key")
    @click.option("--page", required=True, type=click.IntRange(1, 9999))
    @click.option(
        "--status",
        "verdict",
        required=True,
        type=click.Choice(sorted(transcription.REVIEW_STATUSES)),
    )
    @click.option("--by", required=True)
    @click.option("--note", required=True)
    def resolve(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        key: str,
        page: int,
        **options: Any,
    ) -> None:
        """Require an interactive human to adjudicate a disputed page."""
        done(
            ctx,
            "transcription resolve",
            transcription.review(repo, key, pages=str(page), human=True, **options),
            machine,
            strict,
        )
