"""Entry points for session hooks, private backups, status and explicit human escalation."""

from pathlib import Path

import click


def register_commands(cli: click.Group) -> None:
    """Register lifecycle operations without importing Horizon implementation internals."""
    from homalg import lifecycle, publishing
    from homalg.cli import common_options, report
    from homalg.io import json_text

    @cli.command("after-session")
    @common_options
    @click.option("--task", "task_id", required=True)
    @click.option("--session", type=click.Path(path_type=Path), required=True)
    @click.option("--since", required=True)
    @click.option("--until", required=True)
    def after(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        task_id: str,
        session: Path,
        since: str,
        until: str,
    ) -> None:
        """Run the silent session hook; scope violations alone use stdout and exit four."""
        try:
            result = lifecycle.after_session(repo, task_id, session, since, until)
        except lifecycle.ScopeViolation as error:
            click.echo(json_text({"violations": error.paths}), nl=False)
            ctx.exit(4)
        ctx.exit(0 if result["ok"] else 1)

    @cli.command("publish-status")
    @common_options
    @click.argument("key")
    @click.option("--force", is_flag=True, help="Bypass the normal publication interval.")
    @click.option("--now", help="RFC 3339 evaluation time for reproducible tests.")
    def publish(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        key: str,
        force: bool,
        now: str | None,
    ) -> None:
        """Append current numeric evidence to the claimant's public status branch."""
        from homalg.claims import instant

        result = publishing.publish_status(
            repo, key, force=force, now=instant(now) if now else None
        )
        ctx.exit(report("publish-status", [], result, machine=machine, strict=strict))

    @cli.command("backup")
    @common_options
    @click.option("--force", is_flag=True)
    def backup(ctx: click.Context, repo: Path, machine: bool, strict: bool, force: bool) -> None:
        """Archive complete discussions and push work only to the private backup remote."""
        result = lifecycle.backup(repo, force=force)
        ctx.exit(report("backup", [], result, machine=machine, strict=strict))

    @cli.command("sync-main")
    @common_options
    def sync(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Merge current main into an idle contribution branch using ownership rules."""
        result = lifecycle.sync_main(repo)
        ctx.exit(report("sync-main", [], result, machine=machine, strict=strict))

    @cli.command("escalate")
    @common_options
    @click.argument("key")
    def escalate(ctx: click.Context, repo: Path, machine: bool, strict: bool, key: str) -> None:
        """Ask an idle human to approve each unresolved item before creating its issue."""
        result = lifecycle.escalate(repo, key)
        ctx.exit(report("escalate", [], result, machine=machine, strict=strict))
