"""Command registration for offline evidence bundles and explicit local model runs."""

import json
from pathlib import Path

import click

from homalg.evolution.bundle import build_bundle, summary_status
from homalg.evolution.importer import EvolutionError, import_output, review
from homalg.evolution.runner import run
from homalg.io import atomic_write, json_text


def register_commands(cli: click.Group) -> None:
    from homalg.checks.context import Finding
    from homalg.cli import common_options, report

    def index_data(repo, source):
        if source:
            return json.loads((repo / source).read_text())
        from homalg.index import index_repository

        return index_repository(repo)

    def finish(ctx, name, operation, machine, strict):
        try:
            data = operation()
        except (EvolutionError, ValueError, OSError, RuntimeError) as exc:
            ctx.exit(
                report(
                    name,
                    [Finding("evolution", "error", "", str(exc))],
                    {},
                    machine=machine,
                    strict=strict,
                    exit_code=1,
                )
            )
        ctx.exit(
            report(
                name,
                [],
                data,
                machine=machine,
                strict=strict,
                exit_code=1 if data.get("budget_stopped") else 0,
            )
        )

    def selected(index, concept, all_concepts=False, stale=False):
        if sum((bool(concept), all_concepts, stale)) != 1:
            raise EvolutionError("Choose a concept, --all or --stale")
        if concept:
            return [concept]
        if stale:
            return [item["concept"] for item in summary_status(index) if item["summary"] == "stale"]
        return [item["id"] for item in index["concepts"] if not item.get("merged_into")]

    @cli.group("evolution")
    @common_options
    def evolution_group(ctx, repo, machine, strict):
        """Package, summarize and review the documented development of concepts."""

    @evolution_group.command("bundle")
    @common_options
    @click.argument("concept", required=False)
    @click.option("--all", "all_concepts", is_flag=True)
    @click.option("--stale", is_flag=True)
    @click.option("--index", "source", type=click.Path(path_type=Path, dir_okay=False))
    @click.option("--out", required=True, type=click.Path(path_type=Path))
    @click.option("--prompt-version", default=1, type=click.IntRange(min=1))
    def bundle_command(
        ctx, repo, machine, strict, concept, all_concepts, stale, source, out, prompt_version
    ):
        """Write a JSON evidence bundle, or one file per selected concept in a directory."""

        def perform():
            index = index_data(repo, source)
            concepts = selected(index, concept, all_concepts, stale)
            bundles = [
                build_bundle(index, key, prompt_version=prompt_version, repo=repo)
                for key in concepts
            ]
            files = []
            for bundle in bundles:
                target = repo / out
                if all_concepts or stale:
                    target = target / f"{bundle['concept']['id']}.bundle.json"
                atomic_write(target, json_text(bundle))
                files.append(str(target))
            return {"files": files, "count": len(files)}

        finish(ctx, "evolution bundle", perform, machine, strict)

    @evolution_group.command("status")
    @common_options
    @click.option("--index", "source", type=click.Path(path_type=Path, dir_okay=False))
    def status_command(ctx, repo, machine, strict, source):
        """Report none, current or stale for each concept's latest summary version."""
        finish(
            ctx,
            "evolution status",
            lambda: {"concepts": summary_status(index_data(repo, source))},
            machine,
            strict,
        )

    @evolution_group.command("import")
    @common_options
    @click.argument("output", type=click.Path(path_type=Path, dir_okay=False))
    @click.option("--bundle", required=True, type=click.Path(path_type=Path, dir_okay=False))
    @click.option("--model", required=True)
    @click.option("--by")
    @click.option("--prompt-version", type=click.IntRange(min=1))
    def import_command(ctx, repo, machine, strict, output, bundle, model, by, prompt_version):
        """Validate a model's JSON and append a wholly unreviewed summary version."""

        def perform():
            inputs = json.loads((repo / bundle).read_text())
            if prompt_version is not None and prompt_version != inputs["prompt_version"]:
                raise EvolutionError("Prompt version must match the evidence bundle")
            return import_output(
                repo, json.loads((repo / output).read_text()), inputs, model=model, by=by
            )

        finish(ctx, "evolution import", perform, machine, strict)

    @evolution_group.command("run")
    @common_options
    @click.argument("concept", required=False)
    @click.option("--stale", is_flag=True)
    @click.option("--index", "source", type=click.Path(path_type=Path, dir_okay=False))
    @click.option("--provider", "provider_name")
    @click.option("--model")
    @click.option(
        "--max-cost", required=True, help="Cumulative USD ceiling for this local invocation."
    )
    @click.option("--max-tokens", default=8192, type=click.IntRange(min=16))
    @click.option("--price-in", help="Explicit USD per million input tokens.")
    @click.option("--price-out", help="Explicit USD per million output tokens.")
    @click.option("--by")
    def run_command(ctx, repo, machine, strict, concept, stale, source, **options):
        """Explicitly call an installed provider under a mandatory cumulative cost limit."""

        def perform():
            index = index_data(repo, source)
            return run(repo, index, selected(index, concept, stale=stale), **options)

        finish(ctx, "evolution run", perform, machine, strict)

    @evolution_group.command("review")
    @common_options
    @click.argument("identifier")
    @click.argument("version", required=False, type=click.IntRange(min=1))
    @click.option("--summary", "summary_review", is_flag=True)
    @click.option("--accept", "accept", is_flag=True)
    @click.option("--reject", "reject", is_flag=True)
    @click.option("--by", required=True)
    @click.option("--note")
    @click.option("--session")
    @click.option("--author-session")
    @click.option("--report", "review_report", type=click.Path(path_type=Path, dir_okay=False))
    def review_command(
        ctx,
        repo,
        machine,
        strict,
        identifier,
        version,
        summary_review,
        accept,
        reject,
        by,
        note,
        session,
        author_session,
        review_report,
    ):
        """Write a review for a protected PR; this command does not approve or merge it."""

        def perform():
            if accept == reject:
                raise EvolutionError("Choose exactly one of --accept and --reject")
            if summary_review != (version is not None):
                raise EvolutionError("Summary review requires --summary CONCEPT VERSION")
            return review(
                repo,
                status="accepted" if accept else "rejected",
                by=by,
                note=note,
                session=session,
                author_session=author_session,
                report=review_report,
                concept=identifier if summary_review else None,
                version=version,
                relation=None if summary_review else identifier,
            )

        finish(ctx, "evolution review", perform, machine, strict)
