"""CLI registration for authored nodes, review guards and vocabulary maintenance."""

from pathlib import Path
from typing import Any

import click

from homalg.io import atomic_write


def integers(value: str | None) -> list[int] | None:
    """Parse the CLI's comma-separated printed-page list."""
    return [int(part.strip()) for part in value.split(",") if part.strip()] if value else None


def register_commands(cli: click.Group) -> None:
    """Register implemented authoring helpers after the shared reporting framework exists."""
    from homalg.cli import common_options, report

    def done(
        ctx: click.Context, command: str, data: dict[str, Any], machine: bool, strict: bool
    ) -> None:
        ctx.exit(report(command, [], data, machine=machine, strict=strict))

    @cli.command("migrate")
    @common_options
    @click.option("--to", "target", required=True, type=click.IntRange(min=1))
    @click.option("--dry-run", is_flag=True)
    def migrate_command(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, target: int, dry_run: bool
    ) -> None:
        """Run registered forward migrations; unsupported schema versions are rejected."""
        from homalg.migrations import migrate

        done(ctx, "migrate", migrate(repo, target, dry_run=dry_run), machine, strict)

    @cli.command("new-node")
    @common_options
    @click.argument("node_id")
    @click.option("--kind", required=True)
    @click.option("--label")
    @click.option("--pages")
    @click.option("--tags", required=True)
    @click.option("--chapter")
    @click.option("--section")
    @click.option("--title")
    @click.option("--parent")
    @click.option("--aux-kind", type=click.Choice(["lemma", "technical", "bridge"]))
    @click.option("--reason")
    @click.option("--cited-kind", type=click.Choice(["document", "work", "folklore"]))
    @click.option("--cited-ref")
    @click.option("--cited-doc")
    @click.option("--cited-locator")
    @click.option("--used-at")
    def new_node_command(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        node_id: str,
        tags: str,
        pages: str | None,
        used_at: str | None,
        **options: Any,
    ) -> None:
        """Create a planned, schema-valid node without overwriting an existing id."""
        from homalg.checks.context import Finding
        from homalg.scaffold import new_node

        try:
            path = new_node(
                repo,
                node_id,
                tags=tags.split(","),
                pages=integers(pages),
                used_at=integers(used_at),
                **options,
            )
        except (ValueError, FileExistsError) as exc:
            ctx.exit(
                report(
                    "new-node",
                    [Finding("new-node", "error", "", str(exc))],
                    {},
                    machine=machine,
                    strict=strict,
                )
            )
        done(ctx, "new-node", {"file": str(path)}, machine, strict)

    @cli.command("new-doc")
    @common_options
    @click.argument("key")
    @click.option(
        "--pdf", type=click.Path(path_type=Path, exists=True, dir_okay=False), required=True
    )
    @click.option("--title")
    @click.option("--author", "authors", multiple=True, help="Author family name, repeatable.")
    def new_doc_command(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        key: str,
        pdf: Path,
        title: str | None,
        authors: tuple[str, ...],
    ) -> None:
        """Prepare public PDF metadata and open a document registration PR."""
        from homalg.collaboration import register_document
        from homalg.scaffold import new_document_files

        files = new_document_files(repo, key, pdf, title=title, authors=list(authors) or None)
        done(ctx, "new-doc", register_document(repo, key, files=files), machine, strict)

    @cli.group("foundations")
    @common_options
    def foundations_group(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Draft suggestions, inspect evidence and confirm entries one at a time."""

    @foundations_group.command("draft")
    @common_options
    @click.argument("key")
    def foundation_draft(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, key: str
    ) -> None:
        """Populate an empty foundation boundary with unapproved suggestions."""
        from homalg.foundations import draft

        done(ctx, "foundations draft", {"foundations": draft(repo, key)}, machine, strict)

    @foundations_group.command("list")
    @common_options
    @click.argument("key")
    def foundation_list(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, key: str
    ) -> None:
        """Show source evidence and confirmation state for every entry."""
        from homalg.documents import read_document

        done(
            ctx,
            "foundations list",
            {"foundations": read_document(repo, key).get("foundations", [])},
            machine,
            strict,
        )

    @foundations_group.command("confirm")
    @common_options
    @click.argument("key")
    @click.argument("index", type=int)
    @click.option("--by", required=True)
    def foundation_confirm(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, key: str, index: int, by: str
    ) -> None:
        """Human-only: confirm one proposed, evidenced foundation entry (one-based index)."""
        from homalg.foundations import confirm

        done(
            ctx, "foundations confirm", {"entry": confirm(repo, key, index, by=by)}, machine, strict
        )

    @foundations_group.command("review")
    @common_options
    @click.argument("key")
    @click.argument("index", type=int)
    @click.option("--by", required=True)
    @click.option("--session", required=True)
    @click.option("--author-session", required=True)
    @click.option("--report", "review_report", type=click.Path(path_type=Path))
    @click.option("--note", default="")
    def foundation_review(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        key: str,
        index: int,
        by: str,
        session: str,
        author_session: str,
        review_report: Path | None,
        note: str,
    ) -> None:
        """Independently review one foundation under the explicit repository policy."""
        from homalg.foundations import review

        entry = review(
            repo,
            key,
            index,
            by=by,
            session=session,
            author_session=author_session,
            report=review_report,
            note=note,
        )
        done(ctx, "foundations review", {"entry": entry}, machine, strict)

    @cli.group("dispute")
    @common_options
    def dispute_group(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Raise source problems and preserve their explicit human resolution history."""

    @dispute_group.command("open")
    @common_options
    @click.argument("node_id")
    @click.option("--kind", type=click.Choice(["statement", "proof"]), required=True)
    @click.option("--reason", required=True)
    @click.option("--by")
    def dispute_open(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        node_id: str,
        kind: str,
        reason: str,
        by: str | None,
    ) -> None:
        """Record a dispute, its docstring marker and a local human inbox item."""
        from homalg.disputes import open_dispute

        done(
            ctx,
            "dispute open",
            {"dispute": open_dispute(repo, node_id, kind=kind, reason=reason, by=by)},
            machine,
            strict,
        )

    @dispute_group.command("confirm")
    @common_options
    @click.argument("node_id")
    @click.option("--by", required=True)
    def dispute_confirm(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, node_id: str, by: str
    ) -> None:
        """Human-only: confirm a raised dispute as a source error."""
        from homalg.disputes import confirm_dispute

        done(
            ctx,
            "dispute confirm",
            {"dispute": confirm_dispute(repo, node_id, by=by)},
            machine,
            strict,
        )

    @dispute_group.command("resolve")
    @common_options
    @click.argument("node_id")
    @click.option(
        "--via", type=click.Choice(["erratum", "proof-route", "withdrawn"]), required=True
    )
    @click.option("--by", required=True)
    @click.option("--note", required=True)
    def dispute_resolve(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        node_id: str,
        via: str,
        by: str,
        note: str,
    ) -> None:
        """Human-only: resolve a dispute through an explicitly justified route."""
        from homalg.disputes import resolve_dispute

        done(
            ctx,
            "dispute resolve",
            {"dispute": resolve_dispute(repo, node_id, via=via, by=by, note=note)},
            machine,
            strict,
        )

    @cli.command("review-fidelity")
    @common_options
    @click.argument("node_id", required=False)
    @click.option("--by")
    @click.option("--session")
    @click.option("--author-session")
    @click.option("--human", is_flag=True)
    @click.option("--note", default="")
    @click.option("--unlock", "unlock_id")
    @click.option("--reason", default="")
    @click.option("--relock-all", is_flag=True)
    def review_command(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        node_id: str | None,
        by: str | None,
        session: str | None,
        author_session: str | None,
        human: bool,
        note: str,
        unlock_id: str | None,
        reason: str,
        relock_all: bool,
    ) -> None:
        """Lock satisfactorily reviewed statements, or explicitly unlock/refresh existing locks."""
        from homalg import review

        if sum(bool(value) for value in (node_id, unlock_id, relock_all)) != 1:
            raise click.UsageError("Choose NODE_ID, --unlock NODE_ID or --relock-all")
        if relock_all:
            result = review.relock_all(repo, reason=reason)
        elif not by:
            raise click.UsageError("--by is required for a statement review or unlock")
        elif unlock_id:
            review.unlock_fidelity(repo, unlock_id, by=by, reason=reason)
            result = {"unlocked": unlock_id}
        else:
            result = {
                "lock": review.review_fidelity(
                    repo,
                    node_id,
                    by=by,
                    session=session,
                    author_session=author_session,
                    human=human,
                    note=note,
                )
            }
        done(ctx, "review-fidelity", result, machine, strict)

    @cli.group("taxonomy")
    @common_options
    def taxonomy_group(ctx: click.Context, repo: Path, machine: bool, strict: bool) -> None:
        """Find existing vocabulary before appending, and maintain explicit alias chains."""

    @taxonomy_group.command("find")
    @common_options
    @click.argument("query")
    def taxonomy_find(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, query: str
    ) -> None:
        """Search tag/concept ids, labels, descriptions and aliases."""
        from homalg.taxonomy import find

        done(ctx, "taxonomy find", {"matches": find(repo, query)}, machine, strict)

    def merge_command(name: str) -> None:
        @taxonomy_group.command(name)
        @common_options
        @click.argument("source")
        @click.argument("target")
        def command(
            ctx: click.Context, repo: Path, machine: bool, strict: bool, source: str, target: str
        ) -> None:
            """Maintain vocabulary aliases and rewrite node references in a maintenance PR."""
            from homalg.taxonomy import merge

            done(
                ctx,
                f"taxonomy {name}",
                {"files": merge(repo, source, target, rename=name == "rename")},
                machine,
                strict,
            )

    merge_command("merge")
    merge_command("rename")

    @taxonomy_group.command("apply-merges")
    @common_options
    @click.option("--doc", "selected", multiple=True)
    def taxonomy_apply(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, selected: tuple[str, ...]
    ) -> None:
        """Normalize retired vocabulary references after syncing registry updates."""
        from homalg.taxonomy import apply_merges

        done(ctx, "taxonomy apply-merges", {"files": apply_merges(repo, selected)}, machine, strict)

    @cli.command("status")
    @common_options
    @click.option("--doc", "selected", multiple=True)
    @click.option("--fast", is_flag=True)
    def status_command(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        selected: tuple[str, ...],
        fast: bool,
    ) -> None:
        """Report headline/detail counts; mark approximate values explicitly."""
        from homalg.maintenance import status_preview

        done(ctx, "status", status_preview(repo, selected, fast=fast), machine, strict)

    @cli.command("fix-deps")
    @common_options
    @click.argument("key")
    @click.option("--out", type=click.Path(path_type=Path, file_okay=False))
    def fix_command(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, key: str, out: Path | None
    ) -> None:
        """Add verified dependencies; --out writes a mirror for review."""
        from homalg.maintenance import fix_deps

        if out is None:
            click.confirm(
                f"Write verified dependencies to {key}'s authored node headers?", abort=True
            )
        done(
            ctx,
            "fix-deps",
            {"files": fix_deps(repo, key, output=(repo / out) if out else None)},
            machine,
            strict,
        )

    @cli.command("unused-imports")
    @common_options
    @click.option("--doc", "selected", multiple=True)
    def unused_command(
        ctx: click.Context, repo: Path, machine: bool, strict: bool, selected: tuple[str, ...]
    ) -> None:
        """Report unused node/Mathlib imports while retaining declared proof-route imports."""
        from homalg.maintenance import unused_imports

        done(ctx, "unused-imports", {"unused": unused_imports(repo, selected)}, machine, strict)

    @cli.command("prune-check")
    @common_options
    @click.argument("node_id")
    @click.option("--apply", is_flag=True)
    @click.option("--moved-to")
    @click.option("--by")
    @click.option("--reason", default="No remaining users")
    def prune_command(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        node_id: str,
        apply: bool,
        moved_to: str | None,
        by: str | None,
        reason: str,
    ) -> None:
        """Check unused auxiliary/cited nodes; deletion retains a tombstone."""
        from homalg.maintenance import prune_check

        done(
            ctx,
            "prune-check",
            prune_check(repo, node_id, apply=apply, moved_to=moved_to, by=by, reason=reason),
            machine,
            strict,
        )

    @cli.command("review-summary")
    @common_options
    @click.option("--doc", required=True)
    @click.option(
        "--base", help="Git comparison revision; defaults to GITHUB_BASE_SHA or origin/main."
    )
    @click.option("--out", type=click.Path(path_type=Path, dir_okay=False))
    def summary_command(
        ctx: click.Context,
        repo: Path,
        machine: bool,
        strict: bool,
        doc: str,
        out: Path | None,
        base: str | None,
    ) -> None:
        """Generate a Markdown review summary without posting it anywhere."""
        from homalg.maintenance import review_summary

        summary = review_summary(repo, doc, base=base)
        if out:
            atomic_write(repo / out, summary)
        elif not machine:
            click.echo(summary)
        done(
            ctx,
            "review-summary",
            {"file": str(repo / out)} if out else {"markdown": summary} if machine else {},
            machine,
            strict,
        )
