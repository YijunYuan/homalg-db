"""Offline M6 contracts: semantic evidence, hallucinations, reviews and spending gates."""

import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from homalg.evolution.bundle import build_bundle, summary_status
from homalg.evolution.importer import EvolutionError, import_output, review
from homalg.evolution.runner import input_upper_bound, output_schema, run
from homalg.io import json_text
from homalg.relations import relation_id
from homalg.schemas import SchemaStore, load_yaml

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2001, 1, 2, tzinfo=UTC)


@pytest.fixture
def index():
    value = json.loads((ROOT / "tools/tests/fixtures/good/index.json").read_text())
    second = copy.deepcopy(value["nodes"][0])
    second["id"] = second["authored"]["id"] = "Fixture2001.Def_1"
    second["authored"]["doc"] = "Fixture2001"
    second["authored"]["source"]["label"] = "Definition 1"
    second["authored"]["statement_md"] = "A pointed complex is a complex with a point."
    second["authored"]["concepts"] = {"defines": ["chain-complex"], "uses": []}
    value["nodes"].append(second)
    doc = copy.deepcopy(value["documents"][0])
    doc["document"].update(doc_key="Fixture2001", year=2001)
    value["documents"].append(doc)
    return value


def output(bundle):
    nodes = bundle["nodes"]
    return {
        "concept": bundle["concept"]["id"],
        "narrative_md": f"Compare `{nodes[0]['id']}` and `{nodes[1]['id']}`.",
        "stages": [
            {
                "period": str(node["year"]),
                "doc": node["doc"],
                "nodes": [node["id"]],
                "change": "A synthetic construction.",
            }
            for node in nodes
        ],
        "proposed_relations": [
            {
                "type": "specializes",
                "source": nodes[0]["id"],
                "target": nodes[1]["id"],
                "evidence": "Synthetic comparison.",
                "confidence": 0.7,
            }
        ],
        "proposed_aliases": ["toy complex"],
        "open_questions": ["Does the construction extend?"],
    }


def test_bundle_semantic_hash_only_changes_with_evidence(index):
    first = build_bundle(index, "chain-complex")
    second_index = copy.deepcopy(index)
    second_index["generator"]["commit"] = "another-commit"
    second_index["concepts"][0]["current_bundle_sha256"] = "e" * 64
    second_index["evolution"] = [{"concept": "chain-complex", "summaries": [{"version": 1}]}]
    second = build_bundle(second_index, "chain-complex")
    assert first["bundle_sha256"] == second["bundle_sha256"]
    assert first["prompt"] != second["prompt"]
    assert (ROOT / "schema/evolution-output.schema.json").read_text().rstrip() in first["prompt"]
    second_index["nodes"][0]["authored"]["statement_md"] += " New hypothesis."
    assert build_bundle(second_index, "chain-complex")["bundle_sha256"] != first["bundle_sha256"]
    assert [doc["year"] for doc in first["documents"]] == [2000, 2001]


def test_bundle_resolves_merges_and_excludes_unreviewed(index):
    index["concepts"].append({"id": "old-complex", "name": "Old", "merged_into": "chain-complex"})
    index["nodes"][0]["authored"]["concepts"]["uses"] = ["old-complex"]
    for kind, status in [
        ("generalizes", "accepted"),
        ("equivalent_to", "rejected"),
        ("same_as", "unreviewed"),
    ]:
        source, target = [item["id"] for item in index["nodes"]]
        index["relations"].append(
            {
                "id": relation_id(source, kind, target),
                "source": source,
                "target": target,
                "type": kind,
                "review": {"status": status},
            }
        )
    bundle = build_bundle(index, "old-complex")
    assert bundle["concept"]["id"] == "chain-complex"
    assert len(bundle["nodes"]) == 2
    assert {relation["review"]["status"] for relation in bundle["relations"]} == {
        "accepted",
        "rejected",
    }


def test_import_versions_canonical_relations_and_protected_reviews(repo, index):
    bundle = build_bundle(index, "chain-complex", repo=repo)
    result = import_output(repo, output(bundle), bundle, model="offline-fixture", now=NOW)
    path = repo / "taxonomy/evolution/chain-complex.yaml"
    summaries = load_yaml(path.read_text())
    assert summaries["summaries"][0]["review"] == {"status": "unreviewed"}
    relations_path = repo / "taxonomy/relations/llm-2001-01-02.yaml"
    relation = load_yaml(relations_path.read_text())["relations"][0]
    assert relation["type"] == "generalizes" and relation["source"] == "Fixture2001.Def_1"
    assert relation["review"] == {"status": "unreviewed"}
    second = import_output(repo, output(bundle), bundle, model="offline-fixture", now=NOW)
    assert second["version"] == 2 and second["relations_added"] == []
    assert second["relations_skipped"] == result["relations_added"]
    before = relations_path.read_bytes()
    review(repo, status="rejected", by="fixture-reviewer", relation=relation["id"], now=NOW)
    assert relations_path.read_bytes() == before
    registry = load_yaml((repo / "taxonomy/relations/_reviews.yaml").read_text())
    assert registry["reviews"][relation["id"]]["status"] == "rejected"
    review(
        repo, status="accepted", by="fixture-reviewer", concept="chain-complex", version=2, now=NOW
    )
    assert load_yaml(path.read_text())["summaries"][1]["review"]["status"] == "accepted"


@pytest.mark.parametrize(
    "mutation", ["schema", "stage-node", "stage-doc", "narrative", "relation", "hash", "concept"]
)
def test_import_rejects_invalid_output_without_writes(repo, index, mutation):
    bundle = build_bundle(index, "chain-complex", repo=repo)
    value = output(bundle)
    if mutation == "schema":
        value["extra"] = True
    if mutation == "stage-node":
        value["stages"][0]["nodes"] = ["Unknown2099.Thm_1"]
    if mutation == "stage-doc":
        value["stages"][0]["doc"] = "Fixture2001"
    if mutation == "narrative":
        value["narrative_md"] += " Invented `Unknown2099.Thm_1`."
    if mutation == "relation":
        value["proposed_relations"][0]["target"] = "Unknown2099.Thm_1"
    if mutation == "hash":
        bundle["nodes"][0]["statement_md"] += "tampered"
    if mutation == "concept":
        value["concept"] = "unknown-concept"
    before = {path: path.read_bytes() for path in (repo / "taxonomy").rglob("*.yaml")}
    with pytest.raises(EvolutionError):
        import_output(repo, value, bundle, model="offline-fixture", now=NOW)
    assert {path: path.read_bytes() for path in (repo / "taxonomy").rglob("*.yaml")} == before


def test_import_rolls_back_first_file_if_second_write_fails(repo, index, monkeypatch):
    import homalg.evolution.importer as module

    original = module.atomic_write
    calls = []

    def failing(path, text):
        calls.append(path)
        if len(calls) == 2:
            raise OSError("synthetic write failure")
        original(path, text)

    monkeypatch.setattr(module, "atomic_write", failing)
    bundle = build_bundle(index, "chain-complex", repo=repo)
    with pytest.raises(OSError, match="synthetic"):
        import_output(repo, output(bundle), bundle, model="offline-fixture", now=NOW)
    assert not (repo / "taxonomy/evolution/chain-complex.yaml").exists()
    assert not (repo / "taxonomy/relations/llm-2001-01-02.yaml").exists()


def test_staleness_uses_current_inputs_and_latest_version(index):
    bundle = build_bundle(index, "chain-complex")
    assert summary_status(index)[0]["summary"] == "none"
    index["evolution"] = [
        {
            "concept": "chain-complex",
            "summaries": [
                {
                    "version": 1,
                    "provenance": {
                        "bundle_sha256": bundle["bundle_sha256"],
                        "bundle_commit": "fixture",
                    },
                }
            ],
        }
    ]
    assert summary_status(index)[0]["summary"] == "current"
    index["nodes"][0]["authored"]["statement_md"] += " New input."
    assert summary_status(index)[0]["summary"] == "stale"


def fake_provider(bundle, *, prices=None):
    calls = []

    def complete(prompt, schema, model, max_tokens):
        calls.append({"model": model, "max_tokens": max_tokens})
        return json.dumps(output(bundle)), {"input_tokens": 100, "output_tokens": 50}

    return SimpleNamespace(
        DEFAULT_MODEL="fixture-model",
        PRICES=prices if prices is not None else {"fixture-model": (2, 10)},
        complete=complete,
        calls=calls,
    )


def test_runner_refuses_missing_prices_and_over_budget_before_call(repo, index, monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    bundle = build_bundle(index, "chain-complex", repo=repo)
    adapter = fake_provider(bundle, prices={})
    with pytest.raises(EvolutionError, match="Unknown prices"):
        run(repo, index, ["chain-complex"], max_cost=1, provider=adapter)
    assert not adapter.calls
    adapter = fake_provider(bundle)
    result = run(repo, index, ["chain-complex"], max_cost="0.000001", provider=adapter)
    assert result["budget_stopped"] and not adapter.calls
    assert not (repo / "taxonomy/evolution/chain-complex.yaml").exists()


def test_runner_cumulative_cap_and_usage_provenance(repo, index, monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    bundle = build_bundle(index, "chain-complex", repo=repo)
    adapter = fake_provider(bundle)
    upper = input_upper_bound(bundle["prompt"], output_schema(repo))
    bound = (upper * 2 + 8192 * 10) / 1_000_000
    result = run(
        repo,
        index,
        ["chain-complex", "chain-complex"],
        max_cost=bound * 1.1,
        provider=adapter,
        provider_name="fixture",
    )
    assert len(adapter.calls) == 1 and result["budget_stopped"]
    summary = load_yaml((repo / "taxonomy/evolution/chain-complex.yaml").read_text())["summaries"][
        0
    ]
    assert summary["provenance"]["usage"] == {"input_tokens": 100, "output_tokens": 50}
    assert summary["provenance"]["cost_usd"] == pytest.approx(0.0007)
    assert summary["provenance"]["max_cost_usd"] == pytest.approx(bound * 1.1)
    assert summary["provenance"]["provider"] == "fixture"


def test_runner_cli_configuration_precedence_and_explicit_prices(
    repo, index, tmp_path, monkeypatch
):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    config = tmp_path / "evolution.toml"
    config.write_text('provider = "personal"\nmodel = "personal-model"\n')
    bundle = build_bundle(index, "chain-complex", repo=repo)
    adapter = fake_provider(bundle)
    result = run(
        repo,
        index,
        ["chain-complex"],
        max_cost=1,
        provider=adapter,
        provider_name="explicit",
        model="explicit-model",
        config_path=config,
        price_in=2,
        price_out=10,
    )
    assert result["provider"] == "explicit" and adapter.calls[0]["model"] == "explicit-model"
    monkeypatch.setenv("CI", "true")
    with pytest.raises(EvolutionError, match="disabled in CI"):
        run(repo, index, ["chain-complex"], max_cost=1, provider=adapter)
    assert len(adapter.calls) == 1


def test_index_projection_hash_is_optional_only_in_generated_schema(repo, index):
    value = index["concepts"][0]
    value["current_bundle_sha256"] = "0" * 64
    store = SchemaStore(repo / "schema")
    assert not store.validate(index, "index.schema.json")
    assert store.validate({"schema_version": 1, "concepts": [value]}, "concepts.schema.json")


def test_cli_offline_bundle_import_status_and_error_exit(repo, index):
    import click

    from homalg.cli_evolution import register_commands

    @click.group()
    def cli():
        pass

    register_commands(cli)
    index_path = repo / "offline-index.json"
    index_path.write_text(json_text(index))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "evolution",
            "bundle",
            "chain-complex",
            "--repo",
            str(repo),
            "--index",
            str(index_path),
            "--out",
            "bundle.json",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    bundle = json.loads((repo / "bundle.json").read_text())
    value = output(bundle)
    value["stages"][0]["nodes"] = ["Unknown2099.Thm_1"]
    (repo / "output.json").write_text(json.dumps(value))
    result = runner.invoke(
        cli,
        [
            "evolution",
            "import",
            "output.json",
            "--repo",
            str(repo),
            "--bundle",
            "bundle.json",
            "--model",
            "fixture",
            "--json",
        ],
    )
    assert result.exit_code == 1 and "Unknown2099.Thm_1" in result.output


def test_openai_request_is_bounded_and_nullable_schema_is_normalized(repo, monkeypatch):
    import sys

    from homalg.evolution.providers.openai import complete

    calls = {}

    def create(**kwargs):
        calls.update(kwargs)
        return SimpleNamespace(
            status="completed",
            output_text='{"concept":"chain-complex","proposed_aliases":null}',
            usage=SimpleNamespace(input_tokens=11, output_tokens=17),
        )

    def client(**kwargs):
        assert kwargs["max_retries"] == 0 and kwargs["base_url"] == "https://api.openai.com/v1"
        return SimpleNamespace(responses=SimpleNamespace(create=create))

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=client))
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-not-a-real-key")
    text, usage = complete("Return JSON.", output_schema(repo), "gpt-6.1-sol", 256)
    assert json.loads(text) == {"concept": "chain-complex"}
    assert usage == {"input_tokens": 11, "output_tokens": 17}
    assert calls["max_output_tokens"] == 256 and calls["store"] is False
    assert calls["service_tier"] == "default" and "tools" not in calls
    schema = calls["text"]["format"]["schema"]
    assert set(schema["required"]) == set(schema["properties"])
    assert {"type": "null"} in schema["properties"]["proposed_aliases"]["anyOf"]


def test_runner_unknown_price_override_and_bad_usage_fail_closed(repo, index, monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    bundle = build_bundle(index, "chain-complex", repo=repo)
    adapter = fake_provider(bundle, prices={})
    with pytest.raises(EvolutionError, match="both"):
        run(repo, index, ["chain-complex"], max_cost=1, provider=adapter, price_in=2)
    assert not adapter.calls
    adapter.complete = lambda *args: (
        json.dumps(output(bundle)),
        {"input_tokens": 1, "output_tokens": 999999},
    )
    with pytest.raises(EvolutionError, match="exceeded"):
        run(repo, index, ["chain-complex"], max_cost=1, provider=adapter, price_in=2, price_out=10)
    assert not (repo / "taxonomy/evolution/chain-complex.yaml").exists()


def test_previous_editions_share_a_document_lane_and_cycles_fail(index):
    from homalg.sitedata import build_site_data

    index["generator"]["commit"] = "fixture"
    index["documents"][1]["document"]["previous_edition"] = "Fixture2000"
    # Keep the synthetic second node's denormalized fields consistent with its document.
    index["nodes"][1]["global"]["doc_year"] = 2001
    sources = {node["id"]: "" for node in index["nodes"]}
    data = build_site_data(index, sources)
    graph = data["global-graph.json"]
    assert len(graph["documents"]) == 2
    assert graph["documents"][0]["y"] == graph["documents"][1]["y"]
    index["documents"][0]["document"]["previous_edition"] = "Fixture2001"
    with pytest.raises(ValueError, match="cycle"):
        build_site_data(index, sources)
