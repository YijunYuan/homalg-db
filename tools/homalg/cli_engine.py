"""CLI entry points for the local Horizon integration and explicit task scopes."""

from pathlib import Path
from typing import Any

import click


def register_commands(cli: click.Group) -> None:
    """Install engine commands using process/file contracts, without importing the fork."""
    from homalg import blueprint, engine, planning, scope, stages
    from homalg.checks.context import Finding
    from homalg.cli import common_options, report

    def done(
        ctx: click.Context, command: str, data: dict[str, Any], machine: bool, strict: bool
    ) -> None:
        ctx.exit(report(command, [], data, machine=machine, strict=strict))

    @cli.command("doctor")
    @common_options
    def doctor(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Check the pinned fork, ignored paths and shared Lake workspace boundary."""
        data = engine.doctor(repo)
        findings = [
            Finding("engine-setup", "error", "horizon-version.txt", message)
            for message in data["errors"]
        ]
        ctx.exit(report("doctor", findings, data, machine=machine, strict=strict))

    @cli.command("horizon-init")
    @common_options
    @click.option(
        "--engine", "engine_name", type=click.Choice(["claude-code", "codex"]), default="codex"
    )
    @click.option("--model")
    @click.option("--effort")
    @click.option("--transcriber-model")
    def initialize(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        engine_name: str,
        **options: Any,
    ) -> None:
        """Generate the local configuration and install the pinned fork's resources."""
        done(
            ctx,
            "horizon-init",
            engine.initialize(repo, engine=engine_name, **options),
            machine,
            strict,
        )

    @cli.command("build-active")
    @common_options
    def build(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Build active roots and orphan leaves using Horizon's shared build lock."""
        done(ctx, "build-active", engine.build_active(repo), machine, strict)

    @cli.command("private-snapshot")
    @common_options
    def snapshot(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Record a private-source baseline before a run round."""
        data = engine.private_snapshot(repo)
        done(
            ctx,
            "private-snapshot",
            {"available": data["available"], "files": len(data.get("hashes", {}))},
            machine,
            strict,
        )

    @cli.command("blueprint-tex")
    @common_options
    @click.option("--active", is_flag=True)
    @click.option("--doc", "selected", multiple=True)
    def blueprint_command(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        active: bool,
        selected: tuple[str, ...],
    ) -> None:
        """Generate leanblueprint and graph configuration from authored headers."""
        done(
            ctx,
            "blueprint-tex",
            {"files": blueprint.write(repo, selected, active=active)},
            machine,
            strict,
        )

    @cli.command("plan")
    @common_options
    @click.argument("key")
    @click.option("--chapters", default="")
    @click.option("--advance", is_flag=True)
    @click.option("--early-review-ok", is_flag=True)
    @click.option("--by")
    @click.option("--session")
    @click.option("--author-session")
    @click.option("--no-claim", is_flag=True)
    def plan(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        key: str,
        chapters: str,
        **options: Any,
    ) -> None:
        """Create newly eligible tasks; existing statuses and scopes remain intact."""
        data = planning.plan(
            repo, key, chapters=tuple(value for value in chapters.split(",") if value), **options
        )
        done(ctx, "plan", data, machine, strict)

    @cli.command("stage-check")
    @common_options
    @click.argument("task_id")
    def stage(ctx: click.Context, repo: Path, machine: bool, strict: bool, task_id: str) -> None:
        """Evaluate task completion from current source and compiled evidence."""
        data = stages.stage_check(repo, task_id)
        findings = [
            Finding("stage-check", "error", task_id, message) for message in data["failures"]
        ]
        ctx.exit(report("stage-check", findings, data, machine=machine, strict=strict))

    @cli.command("scope-check")
    @common_options
    @click.option("--task", "task_id", required=True)
    @click.option("--since", required=True)
    @click.option("--until", required=True)
    def scope_check(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        task_id: str,
        since: str,
        until: str,
    ) -> None:
        """Return forbidden paths as the engine's exit-four rollback protocol."""
        from homalg.io import json_text

        violations = scope.check_scope(repo, task_id, since, until)
        if violations:
            click.echo(json_text({"violations": violations}), nl=False)
            ctx.exit(4)
        done(ctx, "scope-check", {"violations": []}, machine, strict)
