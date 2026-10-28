"""CLI registration for compiled export, global indexing and static data generation."""

import json
from pathlib import Path

import click

from homalg.io import atomic_write, json_text


def register_commands(cli: click.Group) -> None:
    """Attach pipeline commands after the common CLI helpers have been initialized."""
    from homalg.cli import common_options, report

    @cli.command("export-lean")
    @common_options
    @click.option(
        "--doc", help="Export one document and preserve cross-document dependency identities."
    )
    @click.option("--all", "all_docs", is_flag=True, help="Export every registered document.")
    @click.option(
        "--out", type=click.Path(path_type=Path, dir_okay=False), help="Raw export destination."
    )
    def export_command(ctx, repo, machine, strict, doc, all_docs, out) -> None:
        """Build all selected modules, export JSON, and merge local derived records."""
        from homalg.leanexport import export_lean

        if doc and all_docs:
            raise click.UsageError("Choose --doc or --all, not both")
        result = export_lean(repo, doc=doc, out=(repo / out) if out else None)
        ctx.exit(
            report(
                "export-lean",
                [],
                {
                    "modules": len(result["modules"]),
                    "declarations": sum(len(module["decls"]) for module in result["modules"]),
                },
                machine=machine,
                strict=strict,
            )
        )

    @cli.command("index")
    @common_options
    @click.option(
        "--docs", default="", help="Comma-separated document subset (include dependency documents)."
    )
    @click.option("--commit", help="Revision for links, overriding CI/Git discovery.")
    @click.option("--repo-url", help="Repository HTTPS URL.")
    @click.option(
        "--offline", is_flag=True, help="Skip live GitHub PR lookup; PR links are omitted."
    )
    @click.option("--now", help="RFC 3339 evaluation time for deterministic claim status.")
    @click.option(
        "--out", type=click.Path(path_type=Path, dir_okay=False), default=Path("build/index.json")
    )
    def index_command(
        ctx, repo, machine, strict, docs, commit, repo_url, now, out, offline
    ) -> None:
        """Join fresh exports and metadata into the global dependency database."""
        from homalg.claims import instant
        from homalg.index import index_repository

        selected = tuple(key.strip() for key in docs.split(",") if key.strip())
        result = index_repository(
            repo,
            selected,
            commit=commit,
            repo_url=repo_url,
            now=instant(now) if now else None,
            offline=offline,
        )
        target = repo / out
        atomic_write(target, json_text(result))
        ctx.exit(
            report(
                "index",
                [],
                {"file": str(target), "nodes": len(result["nodes"]), "edges": len(result["edges"])},
                machine=machine,
                strict=strict,
            )
        )

    @cli.command("site-data")
    @common_options
    @click.option(
        "--from",
        "source",
        type=click.Path(path_type=Path, dir_okay=False),
        default=Path("build/index.json"),
    )
    @click.option(
        "--out", type=click.Path(path_type=Path, file_okay=False), default=Path("site/public/data")
    )
    @click.option("--pages-base", default="/", help="Static site's base URL path.")
    @click.option(
        "--no-prerender",
        is_flag=True,
        help="Skip Shiki, MiniSearch, ELK and Markdown preprocessing.",
    )
    @click.option(
        "--check-budgets",
        "budgets",
        is_flag=True,
        help="Fail if actual output exceeds byte budgets.",
    )
    @click.option(
        "--dist",
        type=click.Path(path_type=Path, file_okay=False),
        help="Only check an existing built site.",
    )
    def site_command(
        ctx, repo, machine, strict, source, out, pages_base, no_prerender, budgets, dist
    ) -> None:
        """Generate schema-checked static data and optional pre-rendered assets."""
        from homalg.checks.context import Finding
        from homalg.sitedata import check_budgets, write_site_data

        if dist is not None:
            failures = check_budgets(repo, repo / dist, distribution=True)
            findings = [
                Finding(
                    "site-budget",
                    "error",
                    failure["file"],
                    f"{failure['bytes']} bytes exceeds {failure['limit']}",
                )
                for failure in failures
            ]
            ctx.exit(
                report(
                    "site-data",
                    findings,
                    {"directory": str(repo / dist)},
                    machine=machine,
                    strict=strict,
                )
            )
        index = json.loads((repo / source).read_text())
        manifest = write_site_data(
            repo,
            index,
            repo / out,
            prerender=not no_prerender,
            enforce_budgets=budgets,
            pages_base=pages_base,
        )
        ctx.exit(
            report(
                "site-data",
                [],
                {
                    "directory": str(repo / out),
                    "documents": len(manifest["documents"]),
                    "prerender": manifest["prerender"],
                    "budgets_ok": manifest["budgets_ok"],
                },
                machine=machine,
                strict=strict,
            )
        )
