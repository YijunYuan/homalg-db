"""Controlled-vocabulary discovery, merge resolution and explicit maintenance changes."""

import copy
from pathlib import Path
from typing import Any

import networkx as nx

from homalg.documents import dump_metadata, read_metadata
from homalg.io import atomic_write
from homalg.nodeio import header_mapping, replace_header
from homalg.relations import merged_ids
from homalg.repository import documents, node_paths
from homalg.schemas import SchemaStore, load_yaml


def edit_distance(left: str, right: str) -> int:
    """Compute Levenshtein distance for short controlled vocabulary labels."""
    previous = list(range(len(right) + 1))
    for index, char in enumerate(left, 1):
        current = [index]
        for position, other in enumerate(right, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[position] + 1,
                    previous[position - 1] + (char != other),
                )
            )
        previous = current
    return previous[-1]


def find(repo: Path, query: str) -> list[dict[str, Any]]:
    """Search ids, labels and aliases with case-insensitive substring and distance-two matching."""
    text = query.casefold().strip()
    if not text:
        raise ValueError("Taxonomy search needs a nonempty query")
    results = []
    for name in ("tags", "concepts"):
        entries = load_yaml((repo / "taxonomy" / f"{name}.yaml").read_text())[name]
        for entry in entries:
            fields = [str(entry.get(key, "")) for key in ("id", "label", "name", "description")]
            fields.extend(entry.get("aliases", []))
            matches = [
                value
                for value in fields
                if value
                and (text in value.casefold() or edit_distance(text, value.casefold()) <= 2)
            ]
            if matches:
                results.append({"collection": name, "entry": entry, "matched": matches})
    return sorted(results, key=lambda result: (result["collection"], result["entry"]["id"]))


def merged_node_updates(
    repo: Path, mappings: dict[str, dict[str, str]], selected: tuple[str, ...] = ()
) -> dict[Path, str]:
    """Prepare only tag/concept header edits, leaving human approvals and Lean code intact."""
    schemas = SchemaStore(repo / "schema")
    updates = {}
    for path in node_paths(repo, documents(repo, selected)):
        source = path.read_text()
        metadata = header_mapping(source)
        old = copy.deepcopy(metadata)
        metadata["tags"] = sorted({mappings["tags"].get(key, key) for key in metadata["tags"]})
        for kind, values in metadata.get("concepts", {}).items():
            metadata["concepts"][kind] = sorted(
                {mappings["concepts"].get(key, key) for key in values}
            )
        if metadata != old:
            updates[path] = replace_header(source, metadata, schemas)
    return updates


def apply_merges(repo: Path, selected: tuple[str, ...] = ()) -> list[str]:
    """Bring node vocabulary references up to date without editing registry entries."""
    mappings = {
        name: merged_ids(load_yaml((repo / "taxonomy" / f"{name}.yaml").read_text())[name])
        for name in ("tags", "concepts")
    }
    updates = merged_node_updates(repo, mappings, selected)
    for path, text in updates.items():
        atomic_write(path, text)
    return [path.relative_to(repo).as_posix() for path in updates]


def merge(repo: Path, source: str, target: str, *, rename: bool = False) -> list[str]:
    """Retain retired vocabulary ids and rewrite references in a maintenance PR."""
    if source == target:
        raise ValueError("A vocabulary id cannot be merged into itself")
    schemas = SchemaStore(repo / "schema")
    registries = {}
    matched = False
    for name in ("tags", "concepts"):
        path = repo / "taxonomy" / f"{name}.yaml"
        registry = read_metadata(path, f"{name}.schema.json", schemas)
        table = {entry["id"]: entry for entry in registry[name]}
        if source in table:
            matched = True
            if table[source].get("merged_into"):
                raise ValueError(f"{source} is already merged; use its surviving id")
            if target not in table:
                if not rename:
                    raise ValueError(f"Unknown target in {name}: {target}")
                table[target] = copy.deepcopy(table[source])
                table[target]["id"] = target
                registry[name].append(table[target])
            survivor = table[target]
            if survivor.get("merged_into"):
                raise ValueError(f"Merge target {target} is itself retired")
            if name == "concepts":
                survivor["aliases"] = sorted(
                    set(
                        survivor.get("aliases", [])
                        + table[source].get("aliases", [])
                        + [source, table[source]["name"]]
                    )
                )
            table[source]["merged_into"] = target
            for entry in registry[name]:
                if entry["id"] == source:
                    continue
                if name == "tags" and entry.get("parent") == source:
                    entry["parent"] = (
                        target if entry["id"] != target else table[source].get("parent")
                    )
                elif name == "concepts" and "parents" in entry:
                    entry["parents"] = sorted(
                        {target if key == source else key for key in entry["parents"]}
                        - {entry["id"]}
                    )
        errors = schemas.validate(registry, f"{name}.schema.json")
        if errors:
            raise ValueError(errors[0].message)
        registries[name] = registry
    if not matched:
        raise ValueError(f"Unknown vocabulary id: {source}")
    mappings = {name: merged_ids(registry[name]) for name, registry in registries.items()}
    for name, registry in registries.items():
        graph = nx.DiGraph()
        for entry in registry[name]:
            if entry.get("merged_into"):
                continue
            graph.add_node(entry["id"])
            parents = (
                [entry["parent"]]
                if name == "tags" and entry.get("parent")
                else entry.get("parents", [])
            )
            for parent in parents:
                graph.add_edge(entry["id"], mappings[name].get(parent, parent))
            if name == "concepts" and entry.get("related_tags"):
                entry["related_tags"] = sorted(
                    {mappings["tags"].get(tag, tag) for tag in entry["related_tags"]}
                )
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError(f"Merge would create a {name} parent cycle")
    updates = merged_node_updates(repo, mappings)
    for name, registry in registries.items():
        updates[repo / "taxonomy" / f"{name}.yaml"] = dump_metadata(registry)
    for path, text in updates.items():
        atomic_write(path, text)
    return [path.relative_to(repo).as_posix() for path in updates]
