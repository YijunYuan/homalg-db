"""CLI for frozen author handoffs and read-only critical-path recommendations."""

import json
from pathlib import Path

import click


def register_commands(cli: click.Group) -> None:
    """Register explicit evidence steps without changing task lifecycle semantics."""
    from homalg import workflow
    from homalg.checks.context import Finding
    from homalg.cli import common_options, report

    @cli.group("workflow")
    @common_options
    def group(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Prepare stable reviews and recommend eligible work."""

    @group.command("prepare")
    @common_options
    @click.argument("task_id")
    @click.option("--author-session", required=True)
    @click.option("--out", required=True, type=click.Path(path_type=Path))
    @click.option("--node", "node_ids", multiple=True, help="Select nodes from one actual author.")
    def prepare(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, **options: object
    ) -> None:
        """Freshly compile and validate a scoped author delivery before independent review."""
        data = workflow.prepare(repo, **options)
        findings = [Finding(**item) for item in data["validation"]["findings"]]
        ctx.exit(
            report(
                "workflow prepare",
                findings,
                data,
                machine=machine,
                strict=strict,
                skipped=data["validation"]["skipped"],
            )
        )

    @group.command("prepare-batch")
    @common_options
    @click.argument("task_id")
    @click.option("--authors", required=True, type=click.Path(path_type=Path, exists=True))
    @click.option("--out", required=True, type=click.Path(path_type=Path))
    def prepare_batch(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        task_id: str,
        authors: Path,
        out: Path,
    ) -> None:
        """Share one fresh check across disjoint actual authors listed in a JSON array."""
        data = workflow.prepare_batch(
            repo, task_id, authors=json.loads(authors.read_text()), out=out
        )
        ctx.exit(
            report(
                "workflow prepare-batch",
                [Finding(**item) for item in data["validation"]["findings"]],
                data,
                machine=machine,
                strict=strict,
                skipped=data["validation"]["skipped"],
            )
        )

    @group.command("verify")
    @common_options
    @click.argument("handoff", type=click.Path(path_type=Path, exists=True))
    @click.option("--author-session", help="Select one actual author from a batch handoff.")
    def verify(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        handoff: Path,
        author_session: str | None,
    ) -> None:
        """Verify current author inputs; this is neither an approval nor a new compile."""
        data = workflow.verify(repo, handoff, author_session=author_session)
        ctx.exit(
            report(
                "workflow verify",
                [],
                {
                    "task": data["task"],
                    "current": True,
                    "approval": False,
                    "author_session": data["author_session"],
                    "node_ids": data["node_ids"],
                },
                machine=machine,
                strict=strict,
            )
        )

    @group.command("review-snapshot")
    @common_options
    @click.argument("handoff", type=click.Path(path_type=Path, exists=True))
    @click.option("--out", required=True, type=click.Path(path_type=Path))
    @click.option("--author-session", help="Select one actual author from a batch handoff.")
    @click.option(
        "--node", "node_ids", multiple=True, help="Select a subset for one reviewer batch."
    )
    def snapshot(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        handoff: Path,
        out: Path,
        node_ids: tuple[str, ...],
        author_session: str | None,
    ) -> None:
        """After real reports exist, freeze the final batch registration inputs."""
        data = workflow.review_snapshot(
            repo, handoff, out=out, node_ids=node_ids, author_session=author_session
        )
        ctx.exit(report("workflow review-snapshot", [], data, machine=machine, strict=strict))

    @group.command("review-snapshot-cohorts")
    @common_options
    @click.argument("handoff", type=click.Path(path_type=Path, exists=True))
    @click.option(
        "--cohorts", "manifest", required=True, type=click.Path(path_type=Path, exists=True)
    )
    @click.option("--out", required=True, type=click.Path(path_type=Path))
    def cohort_snapshot(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, **options: object
    ) -> None:
        """Freeze distinct actual author/reviewer cohorts without granting approval."""
        from homalg.review_cohorts import snapshot

        data = snapshot(repo, **options)
        ctx.exit(
            report("workflow review-snapshot-cohorts", [], data, machine=machine, strict=strict)
        )

    @group.command("next")
    @common_options
    @click.argument("key")
    @click.option("--proofs", type=click.Choice(["deferred", "included"]))
    def next_tasks(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        key: str,
        proofs: str | None,
    ) -> None:
        """Read-only ranking; no task creation, priority mutation or automatic dispatch."""
        data = workflow.next_tasks(repo, key, proofs=proofs)
        ctx.exit(report("workflow next", [], data, machine=machine, strict=strict))
