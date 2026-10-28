"""Join document-local metadata and raw Lean exports into the global database."""

import copy
import hashlib
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import networkx as nx

from homalg import __version__
from homalg.relations import load_relations, merged_ids
from homalg.repository import documents
from homalg.retired import load_retired, retirement_map
from homalg.schemas import SchemaStore, load_yaml
from homalg.status import compute_status, facets, status_counts


def git_value(repo: Path, *args: str) -> str | None:
    """Return a successful Git query without exposing diagnostics as data."""
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def revision(repo: Path) -> str:
    """Use CI's exact SHA or a locally qualified dirty revision."""
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    commit = git_value(repo, "rev-parse", "HEAD") or "uncommitted"
    return commit + ("-dirty" if git_value(repo, "status", "--porcelain") else "")


def repository_url(repo: Path) -> str:
    """Normalize the origin into an HTTPS URL, with a non-routable local fallback."""
    if os.environ.get("GITHUB_REPOSITORY"):
        return "https://github.com/" + os.environ["GITHUB_REPOSITORY"]
    remote = git_value(repo, "remote", "get-url", "origin") or ""
    if remote.startswith("git@") and ":" in remote:
        host, path = remote[4:].split(":", 1)
        remote = f"https://{host}/{path}"
    elif remote.startswith("ssh://git@"):
        remote = "https://" + remote.removeprefix("ssh://git@")
    return (
        remote.removesuffix(".git")
        if remote.startswith(("https://", "http://"))
        else ("https://localhost.invalid/homalg-db")
    )


def latest_formalization_prs(repo: Path, keys: list[str], url: str) -> dict[str, int]:
    """Read current PR links from GitHub, matching complete document branch prefixes."""
    from homalg.collaboration import Client

    match = re.fullmatch(r"https://github\.com/([\w.-]+/[\w.-]+)", url)
    if not match:
        return {}
    records = Client(repo).api(
        f"repos/{match[1]}/pulls?state=all&sort=created&direction=desc&per_page=100"
    )
    latest: dict[str, tuple[str, int]] = {}
    selected = set(keys)
    for record in records:
        branch = record.get("head", {}).get("ref", "")
        identifier = re.fullmatch(r"formalize/([A-Z][A-Za-z]*[0-9]{4}[A-Za-z0-9]*)-.+", branch)
        number, created = record.get("number"), record.get("created_at")
        if (
            identifier
            and identifier[1] in selected
            and type(number) is int
            and isinstance(created, str)
        ):
            latest[identifier[1]] = max(latest.get(identifier[1], ("", 0)), (created, number))
    return {key: number for key, (_, number) in latest.items()}


def dependency_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One edge per pair, preferring the verified classification over the declared kind."""
    output = []
    for node in sorted(nodes, key=lambda item: item["id"]):
        derived = node["derived"]
        declared = derived["declared_deps"]
        verified = derived["verified_deps"]
        declared_all = set(declared["statement"]) | set(declared["proof"])
        verified_all = set(verified["statement"]) | set(verified["proof"])
        for target in sorted(declared_all | verified_all):
            evidence = verified if target in verified_all else declared
            output.append(
                {
                    "from": node["id"],
                    "to": target,
                    "kind": "statement" if target in evidence["statement"] else "proof",
                    "declared": target in declared_all,
                    "verified": target in verified_all,
                }
            )
    return output


def declaration_records(exports: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Combine module exports, rejecting conflicting observations of a declaration."""
    result = {}
    for export in exports:
        for module in export["modules"]:
            for declaration in module["decls"]:
                name = declaration["name"]
                if name in result and result[name] != declaration:
                    raise ValueError(f"Conflicting raw exports for {name}; regenerate all exports")
                result[name] = declaration
    return result


def assemble_index(
    document_records: list[dict[str, Any]],
    node_records: list[dict[str, Any]],
    exports: list[dict[str, Any]],
    taxonomy: dict[str, Any],
    relations: list[dict[str, Any]],
    evolution: list[dict[str, Any]],
    *,
    commit: str,
    repo_url: str,
    lean: dict[str, str],
    reopened: set[str] | None = None,
    retired: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Pure global join, cycle detection, closure, statuses and document projection."""
    nodes = copy.deepcopy(sorted(node_records, key=lambda node: node["id"]))
    by_id = {node["id"]: node for node in nodes}
    if len(by_id) != len(nodes):
        raise ValueError("Duplicate node id in index inputs")
    tombstones = retirement_map(retired or [])
    if set(tombstones) & by_id.keys():
        raise ValueError("A retired node id is still present in the live index")
    docs = {record["document"]["doc_key"]: record["document"] for record in document_records}
    if len(docs) != len(document_records):
        raise ValueError("Duplicate document id in index inputs")
    if any(node.get("derived") is None for node in nodes):
        raise ValueError("Missing local Lean-derived data; run homalg export-lean before indexing")
    exported = declaration_records(exports)
    edges = dependency_edges(nodes)
    graph = nx.DiGraph()
    graph.add_nodes_from(by_id)
    for edge in edges:
        if edge["to"] not in by_id:
            raise ValueError(
                f"Missing dependency {edge['to']} of {edge['from']}; include its document"
            )
        graph.add_edge(edge["from"], edge["to"])
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError(f"deps-acyclic: {nx.find_cycle(graph)}")
    doc_graph = nx.DiGraph()
    doc_graph.add_nodes_from(docs)
    for edge in edges:
        source_doc, target_doc = (by_id[edge[key]]["authored"]["doc"] for key in ("from", "to"))
        if source_doc != target_doc:
            doc_graph.add_edge(source_doc, target_doc)
    if not nx.is_directed_acyclic_graph(doc_graph):
        raise ValueError(f"doc-acyclic: {nx.find_cycle(doc_graph)}")
    ranks: dict[str, int] = {}
    for node_id in reversed(list(nx.topological_sort(graph))):
        key = by_id[node_id]["authored"]["doc"]
        ranks[node_id] = max(
            (
                ranks[dependency] + 1
                for dependency in graph.successors(node_id)
                if by_id[dependency]["authored"]["doc"] == key
            ),
            default=0,
        )
    for node in nodes:
        authored, derived = node["authored"], node["derived"]
        doc = docs[authored["doc"]]
        declarations = authored["decls"]
        missing = set(declarations) - exported.keys()
        if missing:
            raise ValueError(f"Missing raw export for {', '.join(sorted(missing))}")
        decl_axioms = {
            name: {
                "axioms": exported[name]["axioms"],
                "transitive_sorry": exported[name]["transitive_sorry"],
            }
            for name in declarations
        }
        blocked = sorted(
            key
            for key in nx.descendants(graph, node["id"])
            if by_id[key]["derived"]["local_status"] == "stated"
        )
        is_reopened = node["id"] in (reopened or set())
        lock = authored["fidelity"].get("reviewed", {})
        if lock:
            locked = lock.get("decl_hashes", {})
            for declaration in derived["decl_info"]:
                old = locked.get(declaration["name"], {})
                is_reopened |= any(
                    old.get(key) != declaration[key] for key in ("type_hash", "meaning_hash")
                )
            is_reopened |= set(locked) != set(declarations)
        status, headline = compute_status(
            authored, derived, decl_axioms, blocked, reopened=is_reopened
        )
        line = min((declaration.get("line", 1) for declaration in derived["decl_info"]), default=1)
        node["global"] = {
            "status": status,
            "headline": headline,
            "decl_axioms": decl_axioms,
            "dependents": sorted(graph.predecessors(node["id"])),
            "closure": {"blocked_by": blocked},
            "doc_title": doc["title"],
            "doc_year": doc["year"],
            "doc_authors": [author["family"] for author in doc["authors"]],
            "rank": ranks[node["id"]],
            "commit": commit,
            "reopened": is_reopened,
            "blob_url": f"{repo_url.rstrip('/')}/blob/{quote(commit, safe='')}/"
            f"{quote(derived['file']['path'], safe='/')}#L{line}",
        }
        chapter = next(
            (
                entry
                for entry in doc.get("structure", [])
                if entry["chapter"] == authored["source"].get("chapter")
            ),
            None,
        )
        if chapter and chapter.get("title"):
            node["global"]["chapter_title"] = chapter["title"]
    projection: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"imports": 0, "relations": {"accepted": 0, "unreviewed": 0}}
    )
    for node in nodes:
        if node["id"].split(".", 1)[1].startswith("Aux_"):
            continue
        for target in node["derived"]["imports"]["nodes"]:
            target_doc, local = target.split(".", 1)
            source_doc = node["authored"]["doc"]
            if target_doc != source_doc and not local.startswith("Aux_"):
                projection[source_doc, target_doc]["imports"] += 1
    for relation in relations:
        source_doc, target_doc = (relation[key].split(".", 1)[0] for key in ("source", "target"))
        review = relation["review"]["status"]
        if source_doc != target_doc and review != "rejected":
            projection[source_doc, target_doc]["relations"][review] += 1
    normalized_nodes = copy.deepcopy(nodes)
    tag_ids, concept_ids = merged_ids(taxonomy["tags"]), merged_ids(taxonomy["concepts"])
    for node in normalized_nodes:
        authored = node["authored"]
        authored["tags"] = sorted({tag_ids[key] for key in authored["tags"]})
        for kind, keys in authored.get("concepts", {}).items():
            authored["concepts"][kind] = sorted({concept_ids[key] for key in keys})
    result = {
        "schema_version": 1,
        "generator": {"name": "homalg", "version": __version__, "commit": commit},
        "lean": lean,
        "repo_url": repo_url,
        "documents": document_records,
        "nodes": nodes,
        "edges": edges,
        "document_graph": [
            {"from": source, "to": target, **value}
            for (source, target), value in sorted(projection.items())
        ],
        "tags": taxonomy["tags"],
        "concepts": copy.deepcopy(taxonomy["concepts"]),
        "relations": relations,
        "evolution": evolution,
        "stats": {"facets": facets(normalized_nodes), "counts": status_counts(nodes)},
    }
    if retired:
        result["retired"] = copy.deepcopy(sorted(retired, key=lambda item: item["id"]))
    from homalg.evolution.bundle import build_bundle

    for concept in result["concepts"]:
        concept["current_bundle_sha256"] = build_bundle(
            result, concept["id"], include_prompt=False
        )["bundle_sha256"]
    return result


def index_repository(
    repo: Path,
    selected: tuple[str, ...] = (),
    *,
    commit: str | None = None,
    repo_url: str | None = None,
    now: datetime | None = None,
    offline: bool = False,
) -> dict[str, Any]:
    """Read validated source files and fresh exports; do not rebuild Lean or write output."""
    from homalg.claims import claim_view, load_status_history

    schemas = SchemaStore(repo / "schema")
    keys = documents(repo, selected)
    origin_url = repository_url(repo)
    target_url = repo_url or origin_url
    prs = (
        latest_formalization_prs(repo, keys, target_url)
        if not offline
        and target_url == origin_url
        and git_value(repo, "remote", "get-url", "origin")
        else {}
    )
    now = now or datetime.now(UTC)
    policy = load_yaml((repo / "taxonomy/policy.yaml").read_text())
    records, nodes, exports = [], [], []
    lean = None
    for key in keys:
        directory = repo / "literature" / key
        doc = load_yaml((directory / "document.yaml").read_text())
        claim = load_yaml((directory / "claim.yaml").read_text())
        node_file = json.loads((directory / "nodes.json").read_text())
        for value, name in ((doc, "document"), (claim, "claim"), (node_file, "nodes-file")):
            errors = schemas.validate(value, f"{name}.schema.json")
            if errors:
                raise ValueError(f"{key}/{name}: {errors[0].message}")
        if lean is not None and lean != node_file["lean"]:
            raise ValueError("Mixed Lean versions in document nodes; regenerate all local exports")
        lean = node_file["lean"]
        records.append(
            {
                "document": doc,
                "claim": claim_view(
                    claim, load_status_history(repo, key), now, policy=policy, pr=prs.get(key)
                ),
            }
        )
        for node in node_file["nodes"]:
            derived = node["derived"]
            if derived is None:
                raise ValueError(f"{node['id']}: run homalg export-lean --doc {key}")
            expected_path = f"HomAlg/{key}/{node['id'].split('.', 1)[1]}.lean"
            if derived["file"]["path"] != expected_path:
                raise ValueError(f"{node['id']}: source path does not match its identity")
            source = repo / derived["file"]["path"]
            if hashlib.sha256(source.read_bytes()).hexdigest() != derived["file"]["sha256"]:
                raise ValueError(
                    f"{node['id']}: stale local export; run homalg export-lean --doc {key}"
                )
        nodes.extend(node_file["nodes"])
        raw_file = repo / "build" / f"lean-export-{key}.json"
        if not raw_file.exists():
            raw_file = repo / "build/lean-export.json"
        raw = json.loads(raw_file.read_text())
        errors = schemas.validate(raw, "lean-export.schema.json")
        if errors:
            raise ValueError(f"{raw_file}: {errors[0].message}")
        if raw["toolchain"] != lean["toolchain"] or raw["mathlib_rev"] != lean["mathlib_rev"]:
            raise ValueError(f"{raw_file}: toolchain mismatch; regenerate the raw export")
        # Retain only this document, so a newer per-document export can supersede a combined file.
        raw = dict(
            raw,
            modules=[
                module for module in raw["modules"] if module["module"].startswith(f"HomAlg.{key}.")
            ],
        )
        exports.append(raw)
    if lean is None:
        raise ValueError("No registered documents to index")
    taxonomy = {
        name: load_yaml((repo / "taxonomy" / f"{name}.yaml").read_text())[name]
        for name in ("tags", "concepts")
    }
    relations = load_relations(repo, nodes, schemas)
    if selected:
        relations = [
            relation
            for relation in relations
            if all(relation[endpoint].split(".", 1)[0] in keys for endpoint in ("source", "target"))
        ]
    evolution = [
        load_yaml(path.read_text()) for path in sorted((repo / "taxonomy/evolution").glob("*.yaml"))
    ]
    from homalg.evolution.reviews import validate_review

    for record in evolution:
        for summary in record["summaries"]:
            validate_review(summary, repo)
    from homalg.review import lock_changes

    reopened = set()
    for node in nodes:
        if not node["authored"]["fidelity"].get("reviewed"):
            continue
        declarations = {item["name"]: item for item in node["derived"]["decl_info"]}
        source = (repo / node["derived"]["file"]["path"]).read_text()
        if lock_changes(source, node["authored"], declarations):
            reopened.add(node["id"])
    result = assemble_index(
        records,
        nodes,
        exports,
        taxonomy,
        relations,
        evolution,
        commit=commit or revision(repo),
        repo_url=target_url,
        lean=lean,
        reopened=reopened,
        retired=load_retired(repo, schemas),
    )
    errors = schemas.validate(result, "index.schema.json")
    if errors:
        raise ValueError(f"Invalid index at {list(errors[0].path)}: {errors[0].message}")
    return result
