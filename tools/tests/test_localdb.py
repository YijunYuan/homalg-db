"""SQLite/API and static JSON contracts use the same real compiled fixture snapshot."""

import copy
import json
import sqlite3
from pathlib import Path

import pytest

from homalg.index import assemble_index
from homalg.localdb import Database, build_artifacts_db, build_db
from homalg.schemas import SchemaStore, load_yaml
from homalg.sitedata import build_site_data, schema_for_file


@pytest.fixture
def artifacts(repo: Path) -> dict:
    keys = ("Fixture2000", "Fixture2001")
    docs = [
        {
            "document": load_yaml((repo / f"literature/{key}/document.yaml").read_text()),
            "claim": {"state": "unclaimed"},
        }
        for key in keys
    ]
    nodes = [
        node
        for key in keys
        for node in json.loads((repo / f"literature/{key}/nodes.json").read_text())["nodes"]
    ]
    raw = json.loads((Path(__file__).parent / "golden/fixture-export.json").read_text())
    taxonomy = {
        name: load_yaml((repo / f"taxonomy/{name}.yaml").read_text())[name]
        for name in ("tags", "concepts")
    }
    index = assemble_index(
        docs,
        nodes,
        [raw],
        taxonomy,
        [],
        [],
        commit="fixture",
        repo_url="https://github.com/example/homalg-db",
        lean={"toolchain": raw["toolchain"], "mathlib_rev": raw["mathlib_rev"]},
    )
    sources = {node["id"]: (repo / node["derived"]["file"]["path"]).read_text() for node in nodes}
    artifacts = build_site_data(index, sources)
    artifacts["evolution/chain-complex.json"] = {
        "concept": "chain-complex",
        "current_bundle_sha256": "a" * 64,
        "summaries": [],
    }
    return artifacts


@pytest.fixture
def database(repo: Path, artifacts: dict) -> Database:
    path = repo / "build/homalg.sqlite"
    result = build_artifacts_db(artifacts, path)
    assert result["nodes"] == 17 and result["documents"] == 2
    return Database(path)


def test_all_database_payloads_equal_static_artifacts(database: Database, artifacts: dict) -> None:
    for path, value in artifacts.items():
        assert database.resource(path) == value, path
    for entry in artifacts["manifest.json"]["documents"]:
        key = entry["doc_key"]
        assert database.document(key) == artifacts[entry["files"]["document"]]
    for path, value in artifacts.items():
        if path.startswith("nodes/"):
            assert database.node(value["summary"]["id"]) == value


def test_search_identifier_filters_facets_and_fuzzy(database: Database) -> None:
    result = database.search({"q": "Fixture2000.Thm_1"})
    assert [record["id"] for record in result["records"]] == ["Fixture2000.Thm_1"]
    assert database.search({"q": "Thm_1"})["total"] == 2
    assert database.search({"q": "degree", "sort": "id"})["total"] > 1
    assert database.search({"q": "degre", "doc": "Fixture2000"})["total"] > 1
    assert database.search({"q": "degrre", "doc": "Fixture2000"})["total"] > 1
    assert database.search({"q": "xegree", "doc": "Fixture2000"})["total"] > 1
    assert database.search({"year": "2001", "aux": "no"})["total"] == 2
    assert database.search({"kind": "lemma", "mathlib": "no"})["total"] >= 1
    result = database.search(
        {"author": "HomAlgDB fixture authors", "tags": "chain-complex", "sort": "year-desc"}
    )
    assert result["records"][0]["year"] == 2001
    assert result["facets"]["doc"]["Fixture2001"] == 2
    assert result["page_size"] == 30 and result["page"] == 1
    assert database.search({"page": 2})["records"] == []


def test_dependency_queries_traverse_both_documents(database: Database) -> None:
    edges, truncated = database.neighbors("Fixture2001.Thm_1", "up", 3)
    assert not truncated
    assert any(edge["to"] == "Fixture2000.Lem_2" for edge in edges)
    down, _ = database.neighbors("Fixture2000.Def_1", "down", 3)
    assert any(edge["from"] == "Fixture2001.Thm_1" for edge in down)
    result = database.search({"deps": "Fixture2001.Thm_1", "dir": "up", "depth": 3})
    ids = {record["id"] for record in result["records"]}
    assert "Fixture2000.Lem_2" in ids and "Fixture2001.Thm_1" not in ids


@pytest.mark.parametrize(
    "query",
    [
        {"q": '" OR * --'},
        {"doc": "Fixture2000') OR 1=1 --"},
        {"author": "' UNION SELECT * FROM nodes --"},
    ],
)
def test_search_escapes_fts_and_sql_syntax(database: Database, query: dict) -> None:
    assert database.search(query)["total"] == 0
    assert database.search({})["total"] == 17


@pytest.mark.parametrize(
    "query",
    [
        {"unknown": "value"},
        {"page": "bad"},
        {"page": 0},
        {"depth": 4},
        {"year": "2001-1999"},
        {"year": "today"},
        {"aux": "maybe"},
        {"dir": "sideways"},
        {"deps": "../etc/passwd"},
        {"sort": "sql()"},
    ],
)
def test_invalid_url_parameters_are_rejected(database: Database, query: dict) -> None:
    with pytest.raises(ValueError):
        database.search(query)


def test_atomic_database_rebuild_retains_previous_snapshot(
    database: Database, artifacts: dict
) -> None:
    before = database.path.read_bytes()
    broken = copy.deepcopy(artifacts)
    first = broken["manifest.json"]["documents"][0]
    broken[first["files"]["search_shard"]].append(broken[first["files"]["search_shard"]][0])
    with pytest.raises(sqlite3.IntegrityError):
        build_artifacts_db(broken, database.path)
    assert database.path.read_bytes() == before
    build_artifacts_db(artifacts, database.path)
    assert database.path.read_bytes() == before


def test_build_db_from_index_and_static_directory(repo: Path, artifacts: dict) -> None:
    source = repo / "build/index.json"
    source.parent.mkdir()
    source.write_text(json.dumps(artifacts["index.json"]))
    built = build_db(repo)
    assert Database(Path(built["file"])).search({})["total"] == 17
    data = repo / "public/data"
    for path, value in artifacts.items():
        target = data / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value))
    build_db(repo, data=data)
    assert Database(Path(built["file"])).resource("manifest.json") == artifacts["manifest.json"]


def test_chapter_projection_keeps_external_dependency_stubs(repo: Path, artifacts: dict) -> None:
    entry = artifacts["manifest.json"]["documents"][0]
    bundle = artifacts[entry["files"]["document"]]
    chosen = "Fixture2000.Thm_1"
    bundle["chapters"].append({"chapter": "2", "sections": [], "node_ids": [chosen]})
    bundle["chapters"][0]["node_ids"].remove(chosen)
    next(node for node in bundle["nodes"] if node["id"] == chosen)["chapter"] = "2"
    next(node for node in artifacts[entry["files"]["search_shard"]] if node["id"] == chosen)[
        "chapter"
    ] = "2"
    target = repo / "chapter.sqlite"
    build_artifacts_db(artifacts, target)
    result = Database(target).document("Fixture2000", "2")
    assert [node["id"] for node in result["nodes"]] == [chosen]
    assert {node["id"] for node in result["external_nodes"]} == {
        "Fixture2000.Def_1",
        "Fixture2000.Lem_2",
    }
    assert not SchemaStore(repo / "schema").validate(result, "site/document-bundle.schema.json")
    with pytest.raises(KeyError):
        Database(target).document("Fixture2000", "missing")


def test_http_endpoints_and_cache_headers(database: Database, artifacts: dict, repo: Path) -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from homalg.localserve import create_app

    static = repo / "dist"
    static.mkdir()
    (static / "index.html").write_text("<html>Static frontend</html>")
    client = TestClient(create_app(static, database.path))
    manifest = client.get("/api/manifest")
    assert manifest.json() == artifacts["manifest.json"]
    assert (
        client.get("/api/manifest", headers={"If-None-Match": manifest.headers["etag"]}).status_code
        == 304
    )
    routes = {
        "/api/taxonomy": "taxonomy.json",
        "/api/global-graph": "global-graph.json",
        "/api/health": "health.json",
    }
    routes["/api/evolution/chain-complex"] = "evolution/chain-complex.json"
    for entry in artifacts["manifest.json"]["documents"]:
        routes[f"/api/documents/{entry['doc_key']}"] = entry["files"]["document"]
    for shard in artifacts["manifest.json"]["global_dag_files"]:
        routes[f"/api/global-dag?from={shard['from']}&to={shard['to']}"] = shard["file"]
    for path in artifacts:
        if path.startswith("nodes/"):
            routes[f"/api/{path.removesuffix('.json')}"] = path
    schemas = SchemaStore(repo / "schema")
    for route, path in routes.items():
        response = client.get(route)
        assert response.status_code == 200, route
        assert response.json() == artifacts[path], route
        if schema := schema_for_file(path):
            assert not schemas.validate(response.json(), schema)
        assert client.get(f"/data/{path}").json() == artifacts[path]
    response = client.get(
        "/api/nodes/Fixture2001/Thm_1/neighbors?dir=up&depth=3",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.json() == database.neighbors("Fixture2001.Thm_1", "up", 3)[0]
    assert response.headers["x-homalg-truncated"] == "false"
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert client.get("/api/search?q=Thm_1").json() == database.search({"q": "Thm_1"})
    assert client.get("/api/search?q=a&q=b").status_code == 400
    assert client.get("/api/evolution/missing-concept").status_code == 404
    assert client.get("/api/nodes/Fixture2000/Missing").status_code == 404
    assert client.get("/api/nodes/Fixture2000/Thm_1/neighbors?depth=4").status_code == 422
    assert client.get("/data/../../lean-toolchain").status_code == 404
    assert "Static frontend" in client.get("/").text
    static_only = TestClient(create_app(static))
    assert static_only.get("/api/manifest").status_code == 404
    assert static_only.get("/").status_code == 200


def test_minisearch_and_sqlite_share_fixture_query_contract(
    database: Database, artifacts: dict
) -> None:
    """Run the real browser search implementation, including its shared tokenizer/options."""
    import subprocess

    site = Path(__file__).resolve().parents[2] / "site"
    if not (site / "node_modules/minisearch/package.json").exists():
        pytest.skip("npm ci in site is required for browser/API contract tests")
    queries = [
        {"sort": "id"},
        {"q": "Fixture2000.Thm_1", "sort": "id"},
        {"q": "Thm_1", "sort": "id"},
        {"q": "degree", "sort": "id"},
        {"q": "degre", "sort": "id"},
        {"year": "2000-2001", "kind": "theorem", "sort": "id"},
        {"doc": "Fixture2001", "sort": "id"},
        {"aux": "yes", "mathlib": "no", "sort": "id"},
        {"tags": "chain-complex", "fidelity": "faithful", "sort": "id"},
        {"author": "HomAlgDB fixture authors", "page": 2, "sort": "id"},
    ]
    records = [
        record
        for path, value in artifacts.items()
        if path.startswith("search/")
        for record in value
    ]
    script = """
import {createIndex, runSearch} from './src/data/search/engine.ts';
let input = ''; for await (const piece of process.stdin) input += piece;
const {records,queries} = JSON.parse(input);
const index = await createIndex(records);
process.stdout.write(JSON.stringify(queries.map(query => runSearch(index,records,query))));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=site,
        input=json.dumps({"records": records, "queries": queries}),
        text=True,
        capture_output=True,
        check=True,
    )
    expected = json.loads(result.stdout)
    for query, static in zip(queries, expected, strict=True):
        assert database.search(query) == static, query


@pytest.mark.parametrize(
    "layout",
    [
        None,
        {
            "view": "aux-collapsed",
            "options_hash": "a" * 16,
            "nodes": {"Fixture2000.Thm_1": {"x": 100, "y": 200}},
        },
    ],
)
def test_chapters_preserve_optional_prerender_layouts(repo: Path, artifacts: dict, layout) -> None:
    entry = artifacts["manifest.json"]["documents"][0]
    artifacts[entry["files"]["document"]]["layout"] = layout
    path = repo / "layout.sqlite"
    build_artifacts_db(artifacts, path)
    assert Database(path).document("Fixture2000", "1")["layout"] == layout


def test_large_document_overview_avoids_node_payload(database: Database) -> None:
    overview = database.document("Fixture2000", "")
    assert overview["chapters"] and overview["nodes"] == []
    assert overview["edges"] == [] and overview["external_nodes"] == []
