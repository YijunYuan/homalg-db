"""Generate the static site's versioned contracts and content-addressed document shards."""

import copy
import hashlib
import html
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from homalg.io import atomic_write, json_text
from homalg.relations import merged_ids
from homalg.schemas import SchemaStore
from homalg.status import status_counts


def digest(value: Any) -> str:
    """Hash reproducible JSON, excluding presentation data at the call site."""
    return hashlib.sha256(json_text(value).encode()).hexdigest()[:16]


def plain_text(markdown: str, limit: int) -> str:
    """Produce a short search/display excerpt, preserving words and mathematical content."""
    value = re.sub(r"<[^>]*>", " ", markdown)
    value = re.sub(r"!?\[([^]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"[`*_#$]", "", value)
    return " ".join(html.unescape(value).split())[:limit]


def node_summary(
    node: dict[str, Any], tags: dict[str, str], concepts: dict[str, str]
) -> dict[str, Any]:
    """Build the lightweight graph record without carrying full prose or Lean source."""
    authored, derived, global_ = node["authored"], node["derived"], node["global"]
    diff = derived["deps_diff"]
    mathlib = authored.get("mathlib", {})
    result = {
        "id": node["id"],
        "local_id": node["id"].split(".", 1)[1],
        "doc": authored["doc"],
        "kind": authored["kind"],
        "label": authored["source"]["label"],
        "pages": authored["source"]["pages"],
        "headline": global_["headline"],
        "status": global_["status"],
        "local_status": derived["local_status"],
        "fidelity_status": authored["fidelity"]["status"],
        "reviewed": bool(authored["fidelity"].get("reviewed")),
        "reopened": global_["reopened"],
        "is_aux": "aux" in authored,
        "has_mathlib": mathlib.get("relation", "none") != "none",
        "disputed": authored.get("dispute", {}).get("status") == "open",
        "needs_repair": "repair" in authored,
        "deps_mismatch": bool(
            diff["verified_not_declared"] or any(diff["declared_not_verified"].values())
        ),
        "tags": sorted({tags[key] for key in authored["tags"]}),
        "concepts_defines": sorted(
            {concepts[key] for key in authored.get("concepts", {}).get("defines", [])}
        ),
        "concepts_uses": sorted(
            {concepts[key] for key in authored.get("concepts", {}).get("uses", [])}
        ),
        "statement_first_line": plain_text(authored["statement_md"].split("\n", 1)[0], 160),
        "decl_names": authored["decls"],
        "rank": global_["rank"],
    }
    for key in ("chapter", "section"):
        if key in authored["source"]:
            result[key] = authored["source"][key]
    if "title" in authored:
        result["title"] = authored["title"]
    if "aux" in authored:
        result.update(aux_kind=authored["aux"]["kind"], aux_parent=authored["aux"]["parent"])
    if mathlib:
        result["mathlib_relation"] = mathlib["relation"]
    return result


def node_ref(summary: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical cross-document reference shape."""
    return {key: summary[key] for key in ("id", "label", "headline", "status", "doc")}


def search_record(node: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    """Build full-text search material without duplicate author objects."""
    authored, global_ = node["authored"], node["global"]
    return {
        **{
            key: summary[key]
            for key in (
                "id",
                "doc",
                "local_id",
                "kind",
                "headline",
                "status",
                "has_mathlib",
                "is_aux",
                "label",
                "tags",
                "decl_names",
            )
        },
        "doc_title": global_["doc_title"],
        "title": authored.get("title", ""),
        "fidelity": summary["fidelity_status"],
        "chapter": summary.get("chapter", ""),
        "concepts": sorted(set(summary["concepts_defines"] + summary["concepts_uses"])),
        "year": global_["doc_year"],
        "authors": global_["doc_authors"],
        "statement_text": plain_text(authored["statement_md"], 300),
        "description_text": plain_text(authored.get("description_md", ""), 300),
    }


def global_views(index: dict[str, Any], summaries: dict[str, dict[str, Any]]) -> tuple[dict, dict]:
    """Precompute stable document/concept coordinates and decade-sharded node graphs."""
    docs = sorted(
        (record["document"] for record in index["documents"]),
        key=lambda doc: (doc["year"], doc["doc_key"]),
    )
    nodes = {node["id"]: node for node in index["nodes"]}
    nodes_by_doc: dict[str, list[dict]] = defaultdict(list)
    summaries_by_doc: dict[str, list[dict]] = defaultdict(list)
    for node in index["nodes"]:
        nodes_by_doc[node["authored"]["doc"]].append(node)
        summaries_by_doc[node["authored"]["doc"]].append(summaries[node["id"]])
    doc_records = {doc["doc_key"]: doc for doc in docs}
    edition_roots = {}
    for doc in docs:
        root = doc["doc_key"]
        seen = set()
        while doc_records.get(root, {}).get("previous_edition"):
            if root in seen:
                raise ValueError(f"Previous edition cycle: {doc['doc_key']}")
            seen.add(root)
            root = doc_records[root]["previous_edition"]
        edition_roots[doc["doc_key"]] = root
    lane_numbers = {
        root: position for position, root in enumerate(dict.fromkeys(edition_roots.values()))
    }
    doc_position = {key: lane_numbers[root] for key, root in edition_roots.items()}
    coordinates = {}
    for position, node in enumerate(index["nodes"]):
        global_ = node["global"]
        coordinates[node["id"]] = {
            "x": global_["doc_year"] * 120
            + doc_position[node["authored"]["doc"]] * 12
            + position % 5,
            "y": global_["rank"] * 120 + position % 7 * 8,
        }
    graph = {
        "documents": [
            {
                "doc_key": doc["doc_key"],
                "year": doc["year"],
                "x": doc["year"] * 120,
                "y": doc_position[doc["doc_key"]] * 100,
                "counts": status_counts(nodes_by_doc[doc["doc_key"]])["node_counts"],
            }
            for doc in docs
        ],
        "document_edges": index["document_graph"],
        "concepts": [],
    }
    for concept in index["concepts"]:
        if concept.get("merged_into"):
            continue
        lanes = []
        related_nodes = set()
        for doc in docs:
            local = summaries_by_doc[doc["doc_key"]]
            defined = [summary for summary in local if concept["id"] in summary["concepts_defines"]]
            used = [summary for summary in local if concept["id"] in summary["concepts_uses"]]
            related_nodes.update(summary["id"] for summary in defined + used)
            if defined or used:
                lanes.append(
                    {
                        "doc": doc["doc_key"],
                        "year": doc["year"],
                        "uses_count": len(used),
                        "defines": [
                            node_ref(summary) | coordinates[summary["id"]] for summary in defined
                        ],
                    }
                )
        graph["concepts"].append(
            {
                "id": concept["id"],
                "lanes": lanes,
                "arcs": [
                    {
                        "type": relation["type"],
                        "source": relation["source"],
                        "target": relation["target"],
                        "review_status": relation["review"]["status"],
                    }
                    for relation in index["relations"]
                    if relation["review"]["status"] != "rejected"
                    and {relation["source"], relation["target"]} <= related_nodes
                ],
            }
        )
    shards: dict[str, dict] = {}
    for node in index["nodes"]:
        year = node["global"]["doc_year"]
        start = (year // 10) * 10
        shard = shards.setdefault(
            f"{start}-{start + 9}", {"range": [start, start + 9], "nodes": [], "edges": []}
        )
        summary = summaries[node["id"]]
        shard["nodes"].append(
            {key: summary[key] for key in ("id", "doc", "kind", "headline", "status")}
            | {"year": year}
            | coordinates[node["id"]]
        )
    edges = [
        {"from": edge["from"], "to": edge["to"], "verified": edge["verified"]}
        for edge in index["edges"]
        if edge["verified"]
    ]
    edges.extend(
        {
            "from": relation["source"],
            "to": relation["target"],
            "verified": False,
            "relation": relation["type"],
            "review_status": relation["review"]["status"],
        }
        for relation in index["relations"]
        if relation["review"]["status"] != "rejected"
    )
    for edge in edges:
        if edge["from"] not in nodes or edge["to"] not in nodes:
            continue
        if any(
            endpoint.split(".", 1)[1].startswith("Aux_") for endpoint in (edge["from"], edge["to"])
        ):
            edge["via_aux"] = True
        year = nodes[edge["from"]]["global"]["doc_year"]
        start = year // 10 * 10
        shards[f"{start}-{start + 9}"]["edges"].append(edge)
    return graph, shards


def build_site_data(
    index: dict[str, Any], source_text: dict[str, str], *, pages_base: str = "/"
) -> dict[str, Any]:
    """Pure contract generation; callers supply node source text explicitly."""
    tag_ids, concept_ids = merged_ids(index["tags"]), merged_ids(index["concepts"])
    summaries = {node["id"]: node_summary(node, tag_ids, concept_ids) for node in index["nodes"]}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for node in index["nodes"]:
        grouped[node["authored"]["doc"]].append(node)
    edges_by_doc: dict[str, list[dict]] = defaultdict(list)
    edges_by_node: dict[str, list[dict]] = defaultdict(list)
    relations_by_node: dict[str, list[dict]] = defaultdict(list)
    for edge in index["edges"]:
        edges_by_doc[edge["from"].split(".", 1)[0]].append(edge)
        edges_by_node[edge["from"]].append(edge)
    for relation in index["relations"]:
        relations_by_node[relation["source"]].append(relation)
        if relation["target"] != relation["source"]:
            relations_by_node[relation["target"]].append(relation)
    result: dict[str, Any] = {"index.json": index}
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "generator": index["generator"],
        "commit": index["generator"]["commit"],
        "repo_url": index["repo_url"],
        "pages_base": pages_base,
        "lean": index["lean"],
        "documents": [],
        "tags_count": len(index["tags"]),
        "concepts_count": len(index["concepts"]),
        "relations_count": len(index["relations"]),
        "index_file": "index.json",
        "global_graph_file": "global-graph.json",
        "global_dag_files": [],
        "prerender": {"shiki": False, "search_index": False, "layout": False},
        "budgets_ok": True,
        "health": {
            "summaries_stale": 0,
            "llm_relations_unreviewed": 0,
            "deps_mismatch": 0,
            "needs_repair": 0,
            "disputed": 0,
            "markdown_findings": 0,
        },
    }
    searches = []
    per_doc = {}
    for record in sorted(index["documents"], key=lambda row: row["document"]["doc_key"]):
        doc = record["document"]
        key = doc["doc_key"]
        local = grouped[key]
        local_ids = {node["id"] for node in local}
        edges = edges_by_doc[key]
        external = sorted({edge["to"] for edge in edges} - local_ids)
        chapters = [
            {
                "chapter": chapter["chapter"],
                "sections": chapter.get("sections", []),
                "node_ids": [
                    node["id"]
                    for node in local
                    if node["authored"]["source"].get("chapter", "") == chapter["chapter"]
                ],
                **({"title": chapter["title"]} if "title" in chapter else {}),
            }
            for chapter in doc.get("structure", [])
        ]
        known_chapters = {chapter["chapter"] for chapter in chapters}
        for chapter in sorted(
            {node["authored"]["source"].get("chapter", "") for node in local} - known_chapters
        ):
            chapters.append(
                {
                    "chapter": chapter,
                    "sections": [],
                    "node_ids": [
                        node["id"]
                        for node in local
                        if node["authored"]["source"].get("chapter", "") == chapter
                    ],
                }
            )
        graph_fields = {
            "chapters": chapters,
            "nodes": [summaries[node["id"]] for node in local],
            "edges": edges,
            "external_nodes": [node_ref(summaries[node_id]) for node_id in external],
        }
        graph_hash = digest(graph_fields)
        document_file = f"documents/{key}.{graph_hash}.json"
        result[document_file] = {
            "schema_version": 1,
            "document": {field: value for field, value in doc.items() if field != "bibtex"},
            **graph_fields,
        }
        search = [search_record(node, summaries[node["id"]]) for node in local]
        searches.append(json_text(search))
        search_file = f"search/{key}.{digest(search)}.json"
        result[search_file] = search
        manifest["documents"].append(
            {
                **{
                    field: doc[field]
                    for field in ("doc_key", "title", "year", "authors", "type", "language")
                },
                **status_counts(local),
                "claim": record["claim"],
                "graph_hash": graph_hash,
                "files": {"document": document_file, "search_shard": search_file},
            }
        )
        counts = {"markdown_findings": 0, "deps_mismatch": 0, "needs_repair": 0, "disputed": 0}
        for node in local:
            summary = summaries[node["id"]]
            for field in ("deps_mismatch", "needs_repair", "disputed"):
                counts[field] += int(summary[field])
                manifest["health"][field] += int(summary[field])
            dependencies = {"statement": [], "proof": []}
            for edge in edges_by_node[node["id"]]:
                dependencies[edge["kind"]].append(node_ref(summaries[edge["to"]]))
            blob = node["global"]["blob_url"]
            result[f"nodes/{key}/{summary['local_id']}.json"] = {
                "summary": summary,
                "authored": node["authored"],
                "derived": node["derived"],
                "global": node["global"],
                "dependencies": dependencies,
                "dependents": [
                    node_ref(summaries[node_id]) for node_id in node["global"]["dependents"]
                ],
                "relations": relations_by_node[node["id"]],
                "lean": {"source_text": source_text[node["id"]]},
                "links": {
                    "github_blob": blob,
                    "github_blame": blob.replace("/blob/", "/blame/", 1),
                },
            }
        per_doc[key] = counts
    if index.get("retired"):
        manifest["retired"] = copy.deepcopy(index["retired"])
    manifest["search_hash"] = hashlib.sha256("".join(searches).encode()).hexdigest()[:16]
    manifest["health"]["llm_relations_unreviewed"] = sum(
        relation["provenance"]["by"] == "llm" and relation["review"]["status"] == "unreviewed"
        for relation in index["relations"]
    )
    result["taxonomy.json"] = {key: index[key] for key in ("tags", "concepts", "relations")}
    result["global-graph.json"], shards = global_views(index, summaries)
    for name, shard in sorted(shards.items()):
        path = f"global-dag/{name}.json"
        result[path] = shard
        manifest["global_dag_files"].append(
            {"from": shard["range"][0], "to": shard["range"][1], "file": path}
        )
    for evolution in index["evolution"]:
        concept = next(entry for entry in index["concepts"] if entry["id"] == evolution["concept"])
        current = concept.get("current_bundle_sha256")
        if current is None:
            from homalg.evolution.bundle import build_bundle

            current = build_bundle(index, concept["id"], include_prompt=False)["bundle_sha256"]
        summaries_ = [
            summary | {"stale": summary["provenance"].get("bundle_sha256") != current}
            for summary in evolution["summaries"]
        ]
        manifest["health"]["summaries_stale"] += sum(summary["stale"] for summary in summaries_)
        result[f"evolution/{concept['id']}.json"] = {
            "concept": concept["id"],
            "current_bundle_sha256": current,
            "summaries": summaries_,
        }
    result["health.json"] = {"markdown_findings": [], "per_doc": per_doc}
    result["manifest.json"] = manifest
    return result


def schema_for_file(path: str) -> str | None:
    """Choose a contract for every Python-produced data artifact."""
    if path == "index.json":
        return "index.schema.json"
    if path.startswith(("search-index.", "search-index/")):
        return None
    mapping = {
        "documents": "document-bundle",
        "nodes": "node-record",
        "search": "search",
        "global-dag": "global-dag",
        "evolution": "evolution",
    }
    stem = mapping.get(path.split("/", 1)[0], Path(path).stem)
    return f"site/{stem}.schema.json"


def check_budgets(
    repo: Path, directory: Path, *, distribution: bool = False
) -> list[dict[str, Any]]:
    """Measure actual bytes after prerender, including any restored documentation."""
    budgets = json.loads((repo / "schema/budgets.json").read_text())
    failures = []
    files = [path for path in directory.rglob("*") if path.is_file()]
    total = sum(path.stat().st_size for path in files)
    key = "site_bytes" if distribution else "data_bytes"
    if total > budgets[key]:
        failures.append({"file": str(directory), "bytes": total, "limit": budgets[key]})
    if distribution:
        return failures
    for path in files:
        relative = path.relative_to(directory).as_posix()
        budget = {"manifest.json": "manifest_bytes", "health.json": "health_bytes"}.get(relative)
        for prefix, candidate in (
            ("documents/", "document_bundle_bytes"),
            ("search/", "search_shard_bytes"),
            ("global-dag/", "global_dag_shard_bytes"),
        ):
            if relative.startswith(prefix):
                budget = candidate
        if budget and path.stat().st_size > budgets[budget]:
            failures.append(
                {"file": relative, "bytes": path.stat().st_size, "limit": budgets[budget]}
            )
    return failures


def manifest_artifacts(manifest: dict[str, Any]) -> set[str]:
    """Only explicitly named generated artifacts qualify for publication cleanup."""
    values = [manifest.get(key) for key in ("index_file", "global_graph_file", "search_index_file")]
    for document in manifest.get("documents", []):
        values.extend(document.get("files", {}).values())
    values.extend(item.get("file") for item in manifest.get("global_dag_files", []))
    return {value for value in values if isinstance(value, str)}


def collect_obsolete_artifacts(output: Path, previous: dict, current: dict) -> list[str]:
    """Remove old manifest-owned shards only; never traverse links or unknown files."""
    root = output.resolve()
    pattern = re.compile(
        r"(?:documents|search)/[A-Z][A-Za-z]*[0-9]{4}[A-Za-z0-9]*\.[a-f0-9]{16}\.json"
        r"|search-index\.[a-f0-9]{16}\.json"
        r"|search-index/[A-Z][A-Za-z]*[0-9]{4}[A-Za-z0-9]*\.[a-f0-9]{16}\.[a-f0-9]{16}\.json"
        r"|global-dag/[0-9]+-[0-9]+\.json"
    )
    removed = []
    for relative in sorted(manifest_artifacts(previous) - manifest_artifacts(current)):
        if not pattern.fullmatch(relative):
            continue
        candidate = output / relative
        if candidate.is_symlink() or any(
            parent.is_symlink() for parent in candidate.parents if parent != output
        ):
            continue
        if not candidate.resolve().is_relative_to(root) or not candidate.is_file():
            continue
        candidate.unlink()
        removed.append(relative)
    return removed


def write_site_data(
    repo: Path,
    index: dict[str, Any],
    output: Path,
    *,
    prerender: bool = True,
    enforce_budgets: bool = False,
    pages_base: str = "/",
) -> dict[str, Any]:
    """Validate every generated contract and publish the manifest after its referenced shards."""
    schemas = SchemaStore(repo / "schema")
    errors = schemas.validate(index, "index.schema.json")
    if errors:
        raise ValueError(f"Invalid index: {errors[0].message}")
    sources = {}
    for node in index["nodes"]:
        doc, local = node["id"].split(".", 1)
        expected = f"HomAlg/{doc}/{local}.lean"
        if node["derived"]["file"]["path"] != expected:
            raise ValueError(f"Invalid source path for {node['id']}")
        sources[node["id"]] = (repo / expected).read_text()
    try:
        previous_manifest = json.loads((output / "manifest.json").read_text())
    except (OSError, ValueError):
        previous_manifest = {}
    artifacts = build_site_data(index, sources, pages_base=pages_base)
    for relative, value in artifacts.items():
        schema = schema_for_file(relative)
        errors = schemas.validate(value, schema) if schema else []
        if errors:
            raise ValueError(f"{relative}: {list(errors[0].path)}: {errors[0].message}")
    for relative, value in artifacts.items():
        if relative != "manifest.json":
            atomic_write(output / relative, json_text(value))
    atomic_write(output / "manifest.json", json_text(artifacts["manifest.json"]))
    if prerender:
        result = subprocess.run(
            ["node", str(repo / "site/scripts/prerender.mjs"), "--data", str(output.resolve())],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(f"Site prerender failed: {result.stderr or result.stdout}")
    manifest = json.loads((output / "manifest.json").read_text())
    # Prerender may enrich contracts; validate those outputs too.
    for relative in artifacts:
        schema = schema_for_file(relative)
        errors = (
            schemas.validate(json.loads((output / relative).read_text()), schema) if schema else []
        )
        if errors:
            raise ValueError(f"Prerendered {relative}: {errors[0].message}")
    collect_obsolete_artifacts(output, previous_manifest, manifest)
    failures = check_budgets(repo, output)
    manifest["budgets_ok"] = not failures
    atomic_write(output / "manifest.json", json_text(manifest))
    if enforce_budgets and failures:
        raise ValueError(f"Site data exceeds byte budgets: {failures}")
    return manifest
