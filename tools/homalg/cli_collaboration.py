"""CLI registration for claim, publication and PR policy commands."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click

from homalg.checks.context import Finding
from homalg.claims import instant
from homalg.collaboration import (
    Client,
    ExternalToolError,
    claim_operation,
    classify_repository,
    submit,
)
from homalg.pr_checks import pr_findings


def register_commands(cli: click.Group) -> None:
    """Register commands after the main CLI and its shared report functions exist."""
    from homalg.cli import common_options, report

    def execute(ctx: click.Context, name: str, machine: bool, strict: bool, call: Any) -> None:
        try:
            data = call()
            findings = []
            code = 0
        except ExternalToolError as exc:
            data = {}
            findings = [Finding("external-tool", "error", "", str(exc))]
            code = 3
        except ValueError as exc:
            data = {}
            findings = [Finding("collaboration", "error", "", str(exc))]
            code = 1
        ctx.exit(report(name, findings, data, machine=machine, strict=strict, exit_code=code))

    def claim_command(name: str, action: str) -> None:
        @cli.command(name)
        @common_options
        @click.argument("key")
        @click.option("--days", type=click.IntRange(min=1))
        @click.option("--chapters", default="", help="Comma-separated chapter ids.")
        @click.option("--note", default="")
        @click.option("--now", help="Evaluation timestamp; defaults to current UTC time.")
        @click.option(
            "--dry-run", is_flag=True, help="Read remote state and preview without publishing."
        )
        @click.option(
            "--no-wait", is_flag=True, help="Enable auto-merge and return without watching checks."
        )
        def command(
            ctx: click.Context,
            repo: Path,
            machine: bool,
            strict: bool,
            key: str,
            days: int | None,
            chapters: str,
            note: str,
            now: str | None,
            dry_run: bool,
            no_wait: bool,
        ) -> None:
            """Publish a claim transition based on current remote ownership and activity."""
            execute(
                ctx,
                name,
                machine,
                strict,
                lambda: claim_operation(
                    repo,
                    key,
                    action,
                    days=days,
                    chapters=[item for item in chapters.split(",") if item],
                    note=note,
                    now=instant(now) if now else datetime.now(UTC),
                    dry_run=dry_run,
                    watch=not no_wait,
                ),
            )

    claim_command("claim", "take")
    claim_command("renew", "renew")
    claim_command("release", "release")

    @cli.command("classify")
    @common_options
    @click.option("--pr-base", required=True)
    @click.option("--pr-author", required=True)
    @click.option("--pr-labels", default="")
    @click.option("--pr-head", default="HEAD")
    def classify(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        pr_base: str,
        pr_author: str,
        pr_labels: str,
        pr_head: str,
    ) -> None:
        """Classify changed paths using the ordered collaboration policy."""
        labels = [label for label in pr_labels.split(",") if label]
        execute(
            ctx,
            "classify",
            machine,
            strict,
            lambda: (
                classify_repository(
                    Client(repo),
                    pr_base,
                    labels,
                    pr_head,
                )
                | {"author": pr_author, "labels": labels}
            ),
        )

    @cli.command("pr-check")
    @common_options
    @click.option("--pr-base", required=True)
    @click.option("--pr-author", required=True)
    @click.option("--pr-labels", default="")
    @click.option("--pr-created-at")
    @click.option("--pr-number", type=int)
    @click.option("--pr-head", default="HEAD")
    @click.option("--now")
    @click.option("--owner-only", is_flag=True)
    def pr_check(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        pr_base: str,
        pr_author: str,
        pr_labels: str,
        pr_created_at: str | None,
        pr_number: int | None,
        pr_head: str,
        now: str | None,
        owner_only: bool,
    ) -> None:
        """Check PR ownership, claim races, append-only records and write scope."""
        try:
            findings = pr_findings(
                repo,
                base=pr_base,
                author=pr_author,
                labels=pr_labels.split(","),
                created_at=pr_created_at,
                number=pr_number,
                head=pr_head,
                now=now,
                owner_only=owner_only,
            )
            code = 0
        except ExternalToolError as exc:
            findings = [Finding("external-tool", "error", "", str(exc))]
            code = 3
        ctx.exit(report("pr-check", findings, {}, machine=machine, strict=strict, exit_code=code))

    @cli.command("submit")
    @common_options
    @click.argument("key")
    @click.option("--no-claim", is_flag=True, help="Allow a synthetic document without a claim.")
    @click.option("--release-claim", is_flag=True)
    def submit_command(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        key: str,
        no_claim: bool,
        release_claim: bool,
    ) -> None:
        """Validate and publish a document-scoped PR from an isolated worktree."""
        hooks = None
        if (repo / "config.yaml").exists():
            from homalg.lifecycle import LifecycleHooks

            hooks = LifecycleHooks()
        execute(
            ctx,
            "submit",
            machine,
            strict,
            lambda: submit(
                repo,
                key,
                no_claim=no_claim,
                release_claim=release_claim,
                hooks=hooks,
            ),
        )
