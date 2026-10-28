"""CLI registration for immutable local databases and static/API serving."""

from pathlib import Path

import click


def register_commands(cli: click.Group) -> None:
    """Expose build-db and serve through the project's normal machine reporting."""
    from homalg.cli import common_options, report

    @cli.command("build-db")
    @common_options
    @click.option(
        "--out",
        type=click.Path(path_type=Path, dir_okay=False),
        default=Path("build/homalg.sqlite"),
    )
    @click.option(
        "--from",
        "source",
        type=click.Path(path_type=Path, dir_okay=False),
        default=Path("build/index.json"),
    )
    @click.option(
        "--data",
        type=click.Path(path_type=Path, file_okay=False),
        help="Preserve a prerendered static data snapshot instead of reading index.json.",
    )
    def build_command(ctx, repo, machine, strict, out, source, data) -> None:
        """Atomically create a SQLite/FTS5 snapshot from generated public data."""
        from homalg.localdb import build_db

        result = build_db(
            repo, repo / out, source=repo / source, data=repo / data if data else None
        )
        ctx.exit(report("build-db", [], result, machine=machine, strict=strict))

    @cli.command("serve")
    @common_options
    @click.option(
        "--static", "static_dir", required=True, type=click.Path(path_type=Path, file_okay=False)
    )
    @click.option("--db", type=click.Path(path_type=Path, dir_okay=False))
    @click.option("--host", default="127.0.0.1", help="Listening interface; loopback by default.")
    @click.option("--port", default=8787, type=click.IntRange(1, 65535))
    def serve_command(ctx, repo, machine, strict, static_dir, db, host, port) -> None:
        """Host the built frontend, optionally with the local database API."""
        from homalg.localserve import serve

        if machine:
            raise click.UsageError("A long-running server does not support --json")
        serve(repo / static_dir, repo / db if db else None, host=host, port=port)
