"""CLI for isolated, source-ledger-based draft workers."""

from pathlib import Path

import click


def register_commands(cli: click.Group) -> None:
    """Expose draft authoring without registering or completing native tasks."""
    from homalg import workspaces
    from homalg.cli import common_options, report

    @cli.group("workspaces")
    @common_options
    def group(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Create isolated draft workers and integrate checked, owned node files."""

    @group.command("create")
    @common_options
    @click.argument("worker_id")
    @click.option(
        "--author", required=True, help="Actual author/session identity (recorded, not attested)."
    )
    @click.option("--file", "files", multiple=True)
    @click.option(
        "--task", "task_id", help="Bind ownership to a real registered task's file scope."
    )
    @click.option("--dependency", "dependencies", multiple=True)
    @click.option("--native", is_flag=True, help="Owned by this live native Horizon task/session.")
    @click.option(
        "--copy-cache", is_flag=True, help="Copy independent Lake cache files; no hardlinks."
    )
    def create(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        worker_id: str,
        **options: object,
    ) -> None:
        """Reserve explicit Lean node paths from the current clean source ledger."""
        data = workspaces.create(repo, worker_id, **options)
        ctx.exit(report("workspaces create", [], data, machine=machine, strict=strict))

    @group.command("status")
    @common_options
    @click.argument("worker_id", required=False)
    def status(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, worker_id: str | None
    ) -> None:
        """Show ownership, changed files and whether compile evidence is current."""
        data = workspaces.status(repo, worker_id)
        ctx.exit(report("workspaces status", [], data, machine=machine, strict=strict))

    @group.command("check")
    @common_options
    @click.argument("worker_id")
    @click.option("--by", required=True)
    @click.option("--timeout", default=1800, type=click.IntRange(min=1))
    def check(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        worker_id: str,
        by: str,
        timeout: int,
    ) -> None:
        """Compile owned modules with the pinned Horizon in the worker's own workspace."""
        data = workspaces.check(repo, worker_id, by=by, timeout=timeout)
        ctx.exit(
            report(
                "workspaces check",
                [],
                data,
                machine=machine,
                strict=strict,
                exit_code=0 if data["ok"] else 3,
            )
        )

    @group.command("promote")
    @common_options
    @click.argument("worker_id")
    @click.option("--by", required=True)
    @click.option("--native", is_flag=True, help="Collect within the worker's live parent session.")
    def promote(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        worker_id: str,
        by: str,
        native: bool,
    ) -> None:
        """At an idle locked boundary, integrate checked files into the source ledger only."""
        data = workspaces.promote(repo, worker_id, by=by, native=native)
        ctx.exit(report("workspaces promote", [], data, machine=machine, strict=strict))

    @group.command("collect")
    @common_options
    @click.argument("worker_id")
    @click.option("--by", required=True)
    def collect(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, worker_id: str, by: str
    ) -> None:
        """Stage a native candidate; canonical compilation and review remain required."""
        data = workspaces.collect(repo, worker_id, by=by)
        ctx.exit(report("workspaces collect", [], data, machine=machine, strict=strict))

    @group.command("exec", context_settings={"ignore_unknown_options": True})
    @common_options
    @click.argument("worker_id")
    @click.argument("command", nargs=-1, type=click.UNPROCESSED)
    def execute(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        worker_id: str,
        command: tuple[str, ...],
    ) -> None:
        """Run a worker command after -- with canonical session/Git routing removed."""
        ctx.exit(workspaces.execute(repo, worker_id, command))

    @group.command("retire")
    @common_options
    @click.argument("worker_id")
    @click.option("--by", required=True)
    @click.option("--reason", required=True)
    def retire(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        worker_id: str,
        by: str,
        reason: str,
    ) -> None:
        """Release a stale draft's ownership, retaining its checkout and all evidence."""
        data = workspaces.retire(repo, worker_id, by=by, reason=reason)
        ctx.exit(report("workspaces retire", [], data, machine=machine, strict=strict))
