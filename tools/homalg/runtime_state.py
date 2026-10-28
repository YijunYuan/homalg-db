"""Fresh document status projections shared by hooks, stages and remote numeric progress."""

import hashlib
import json
from pathlib import Path
from typing import Any

import networkx as nx

from homalg.extract import extract_document
from homalg.headers import parse_header
from homalg.io import atomic_write, json_text
from homalg.leanexport import export_lean
from homalg.leantext import sorry_count
from homalg.repository import documents, node_paths
from homalg.review import lock_changes
from homalg.roots import generate_roots
from homalg.schemas import SchemaStore
from homalg.status import compute_status, status_counts


def fresh(repo: Path, key: str) -> bool:
    """Require a raw export and a byte-current derived record for every current node."""
    path = repo / "literature" / key / "nodes.json"
    raw = repo / "build" / f"lean-export-{key}.json"
    if not path.exists() or not raw.exists():
        return False
    try:
        nodes = json.loads(path.read_text())["nodes"]
        paths = node_paths(repo, [key])
        if {node["id"] for node in nodes} != {f"{key}.{path.stem}" for path in paths}:
            return False
        for node in nodes:
            source = repo / "HomAlg" / key / (node["id"].split(".", 1)[1] + ".lean")
            if (
                not node["derived"]
                or node["derived"]["file"]["sha256"]
                != hashlib.sha256(source.read_bytes()).hexdigest()
                or source.stat().st_mtime_ns > raw.stat().st_mtime_ns
            ):
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def refresh(repo: Path, key: str) -> None:
    """Refresh stale local facts through the exporter's shared workspace lock."""
    if fresh(repo, key):
        return
    for relative, text in generate_roots(repo, (key,)).items():
        atomic_write(repo / relative, text)
    atomic_write(
        repo / "literature" / key / "nodes.json",
        json_text(extract_document(repo, key, SchemaStore(repo / "schema"))),
    )
    export_lean(repo, doc=key)


def document_state(repo: Path, key: str) -> dict[str, Any]:
    """Compute the same status function as indexing, degrading individual stale nodes explicitly."""
    all_nodes: dict[str, dict[str, Any]] = {}
    raw: dict[str, dict[str, Any]] = {}
    for path in sorted(
        (repo / "build").glob("lean-export*.json"), key=lambda path: path.stat().st_mtime_ns
    ):
        data = json.loads(path.read_text())
        for module in data.get("modules", []):
            for declaration in module["decls"]:
                raw[declaration["name"]] = declaration
    for doc in documents(repo):
        path = repo / "literature" / doc / "nodes.json"
        existing = (
            {node["id"]: node for node in json.loads(path.read_text())["nodes"]}
            if path.exists()
            else {}
        )
        for source_path in node_paths(repo, [doc]):
            text = source_path.read_text()
            authored = parse_header(text).metadata
            derived = existing.get(authored["id"], {}).get("derived")
            current = bool(
                derived
                and derived["file"]["sha256"]
                == hashlib.sha256(source_path.read_bytes()).hexdigest()
            )
            if not current:
                derived = {
                    "local_status": "planned"
                    if not authored["decls"]
                    else "stated"
                    if sorry_count(text)
                    else "proved",
                    "verified_deps": {"statement": [], "proof": []},
                    "deps_diff": {"verified_not_declared": [], "declared_not_verified": []},
                }
            available = current and all(name in raw for name in authored["decls"])
            all_nodes[authored["id"]] = {
                "id": authored["id"],
                "authored": authored,
                "derived": derived,
                "source": text,
                "approx": not available,
            }
    graph = nx.DiGraph()
    graph.add_nodes_from(all_nodes)
    for node in all_nodes.values():
        for dependency in set(
            sum(node["authored"]["deps"].values(), [])
            + sum(node["derived"]["verified_deps"].values(), [])
        ):
            graph.add_edge(node["id"], dependency)
    selected = []
    for node in all_nodes.values():
        if node["authored"]["doc"] != key:
            continue
        authored, derived = node["authored"], node["derived"]
        blocked = sorted(
            dep
            for dep in nx.descendants(graph, node["id"])
            if dep not in all_nodes or all_nodes[dep]["derived"]["local_status"] == "stated"
        )
        declarations = {name: raw[name] for name in authored["decls"] if name in raw}
        reopened = node["approx"] or bool(lock_changes(node["source"], authored, declarations))
        axioms = {
            name: {
                "axioms": declaration["axioms"],
                "transitive_sorry": declaration["transitive_sorry"],
            }
            for name, declaration in declarations.items()
        }
        detail, headline = compute_status(authored, derived, axioms, blocked, reopened=reopened)
        node["global"] = {
            "status": detail,
            "headline": headline,
            "reopened": reopened,
            "closure": {"blocked_by": blocked},
        }
        selected.append(node)
    return {
        "doc_key": key,
        "nodes": selected,
        "counts": status_counts(selected),
        "approx": any(node["approx"] for node in selected),
    }


def overlay_nodes(state: dict[str, Any]) -> dict[str, Any]:
    """Expose only dashboard fields; source transcriptions stay in the private viewer."""
    output = {}
    for node in state["nodes"]:
        authored, derived, global_ = node["authored"], node["derived"], node["global"]
        dispute = authored.get("dispute", {})
        output[node["id"]] = {
            "headline": global_["headline"],
            "status": global_["status"],
            "local_status": derived["local_status"],
            "locked": bool(authored["fidelity"].get("reviewed")),
            "fidelity": authored["fidelity"]["status"],
            "fidelity_status": authored["fidelity"]["status"],
            "reviewed": bool(authored["fidelity"].get("reviewed")),
            "cited": "cited" in authored,
            "dispute_raised": dispute.get("status") == "open",
            "dispute_confirmed": dispute.get("status") == "open"
            and bool(dispute.get("confirmed_by")),
            "disputed": dispute.get("status") == "open",
            "reopened": global_["reopened"],
            "deps_mismatch": any(derived["deps_diff"].values()),
            "approx": node["approx"],
            "is_aux": "aux" in authored,
            "aux_kind": authored.get("aux", {}).get("kind"),
            "blocked_by": global_["closure"]["blocked_by"],
            "needs_repair": authored["fidelity"]["status"] == "deviates" or global_["reopened"],
        }
    return output
