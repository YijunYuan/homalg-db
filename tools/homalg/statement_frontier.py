"""Read-only, node-scoped prerequisites for opt-in native statement execution.

These checks authorize work, not acceptance. Chapter DAG work, independent
review, compiled validation and the outer session hook remain mandatory.
"""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import networkx as nx

from homalg.documents import read_document
from homalg.headers import imports_of, parse_header
from homalg.repository import node_paths
from homalg.review import review_blocks
from homalg.review_policy import early_review_valid, foundation_confirmed
from homalg.runtime_state import document_state
from homalg.schemas import load_yaml
from homalg.transcription import status as transcription_status

DEFINITIONS = {"definition", "construction", "notation", "axiom", "remark", "conjecture"}


def _complete_text(text: str) -> bool:
    return bool(text.strip()) and not re.search(r"(?im)^\s*TODO\b|\[illegible\]", text)


class StatementFrontier:
    """One immutable-input planning/check call; never reuse this across mutations."""

    def __init__(
        self,
        repo: Path,
        key: str,
        *,
        state_loader: Callable[[Path, str], dict[str, Any]] | None = None,
    ):
        self.repo, self.key = repo, key
        self._state_loader = state_loader or document_state
        self.document = read_document(repo, key)
        self.headers = {
            header.metadata["id"]: header
            for path in node_paths(repo, [key])
            for header in [parse_header(path.read_text())]
        }
        self.sources = {f"{key}.{path.stem}": path.read_text() for path in node_paths(repo, [key])}
        inventory_path = repo / "literature" / key / "inventory.yaml"
        self.inventory = load_yaml(inventory_path.read_text()) if inventory_path.exists() else {}
        self.pages = (
            {}
            if self.document["type"] == "synthetic"
            else transcription_status(repo, key, persist=False)["pages"]
        )
        self.states: dict[str, dict[str, Any]] = {}

    def state(self, identifier: str) -> dict[str, Any] | None:
        key = identifier.split(".", 1)[0]
        if key not in self.states:
            self.states[key] = {
                node["id"]: node for node in self._state_loader(self.repo, key)["nodes"]
            }
        return self.states[key].get(identifier)

    def accepted_interface(self, identifier: str) -> bool:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*\.[A-Za-z][A-Za-z0-9_]*", identifier):
            return False
        header = self.headers.get(identifier)
        if header is not None and not header.metadata.get("decls"):
            return False
        node = self.state(identifier)
        key, local = identifier.split(".", 1)
        path = self.repo / "literature" / key / "reviews" / f"{local}.md"
        reports = review_blocks(path.read_text()) if path.exists() else {}
        return bool(
            node
            and node["authored"].get("decls")
            and not node["approx"]
            and node["derived"].get("local_status") in {"stated", "proved"}
            and node["authored"].get("fidelity", {}).get("reviewed")
            and not node["global"]["reopened"]
            and node["global"]["headline"] != "error"
            and reports.get("source-fidelity", {}).get("status") == "satisfactory"
            and all(report["status"] == "satisfactory" for report in reports.values())
        )

    def settled_statement(self, identifier: str) -> bool:
        """Avoid reauthoring current accepted content; do not assert task completion.

        A confirmed source error is settled for its own statement task, while
        accepted_interface deliberately never permits it as a mathematical input.
        """
        header = self.headers.get(identifier)
        if header is not None and not header.metadata.get("decls"):
            return False
        node = self.state(identifier)
        if not (
            node
            and node["authored"].get("decls")
            and not node["approx"]
            and node["derived"].get("local_status") in {"stated", "proved"}
        ):
            return False
        if self.document["type"] != "synthetic":
            offset = self.document.get("pdf", {}).get("page_offset", 0)
            pages = node["authored"].get("source", {}).get("pages", [])
            if not pages or any(
                self.pages.get(f"{page + offset:04}", {}).get("status") != "reviewed"
                for page in pages
            ):
                return False
        if node["global"]["headline"] == "error":
            dispute = node["authored"].get("dispute", {})
            return dispute.get("status") == "open" and bool(dispute.get("confirmed_by"))
        return self.accepted_interface(identifier)

    def node_ids(self, chapters: set[str], explicit: tuple[str, ...] = ()) -> list[str]:
        if explicit:
            unknown = set(explicit) - set(self.headers)
            if unknown:
                raise ValueError("Unknown statement nodes: " + ", ".join(sorted(unknown)))
        selected = []
        for identifier, header in self.headers.items():
            node = header.metadata
            if explicit and identifier not in explicit:
                continue
            if node["source"].get("chapter") not in chapters:
                if explicit:
                    raise ValueError(
                        f"Statement node is outside the selected chapters: {identifier}"
                    )
                continue
            if "aux" in node or "informal" in node or "cited" in node:
                if explicit:
                    raise ValueError(f"Statement units require formal primary nodes: {identifier}")
                continue
            selected.append(identifier)
        return selected

    def group(self, identifier: str) -> list[str]:
        return [
            identifier,
            *sorted(
                node_id
                for node_id, header in self.headers.items()
                if header.metadata.get("aux", {}).get("parent") == identifier
                and not header.metadata.get("aux", {}).get("pruned")
            ),
        ]

    def blockers(self, node_ids: list[str]) -> list[str]:
        failures = []
        owned = set(node_ids)
        internal = nx.DiGraph()
        internal.add_nodes_from(owned)
        offset = self.document.get("pdf", {}).get("page_offset", 0)
        for entry in self.document.get("foundations", []):
            if not foundation_confirmed(entry, self.repo):
                failures.append(f"Foundation is not confirmed: {entry.get('notion', 'unknown')}")
        for identifier in node_ids:
            header = self.headers.get(identifier)
            if header is None:
                failures.append(f"{identifier}: node metadata is missing")
                continue
            node = header.metadata
            if not _complete_text(header.sections.get("Statement", "")):
                failures.append(f"{identifier}: complete source Statement text is required")
            if node.get("kind") not in DEFINITIONS:
                parent = self.headers.get(node.get("aux", {}).get("parent", ""))
                definition_support = parent is not None and parent.metadata["kind"] in DEFINITIONS
                if not definition_support and not early_review_valid(
                    self.document.get("early_review"), self.repo
                ):
                    failures.append(f"{identifier}: first-definition early review is required")
                if not _complete_text(header.sections.get("Proof", "")):
                    failures.append(f"{identifier}: complete source Proof text is required")
            pages = node.get("source", {}).get("pages")
            if not isinstance(pages, list) or not pages or any(type(p) is not int for p in pages):
                failures.append(f"{identifier}: explicit source pages are required")
                continue
            parent = node.get("aux", {}).get("parent", identifier)
            inventoried = False
            for page in pages:
                page_key = f"{page + offset:04}"
                entry = self.inventory.get("pages", {}).get(page_key, {})
                if not entry.get("complete"):
                    failures.append(f"{identifier}: source page {page_key} inventory is incomplete")
                inventoried |= any(
                    item.get("node") == parent and item.get("disposition") == "node"
                    for item in entry.get("items", [])
                )
                if (
                    self.document["type"] != "synthetic"
                    and self.pages.get(page_key, {}).get("status") != "reviewed"
                ):
                    failures.append(f"{identifier}: source page {page_key} is not reviewed")
            if not inventoried:
                failures.append(
                    f"{identifier}: no inventoried source occurrence identifies this node"
                )
            dependencies = node.get("deps", {}).get("statement")
            proof_dependencies = node.get("deps", {}).get("proof")
            if (
                not isinstance(dependencies, list)
                or not isinstance(proof_dependencies, list)
                or any(not isinstance(dep, str) for dep in dependencies + proof_dependencies)
            ):
                failures.append(
                    f"{identifier}: explicit statement/proof dependency lists are required"
                )
                continue
            required = set(dependencies)
            internal.add_edges_from((identifier, dep) for dep in required & owned)
            # A proof-only import may contain a planned declaration: its proof is
            # deferred. Other actual local imports are conservative API inputs.
            for module in imports_of(self.sources[identifier]):
                if module.startswith("HomAlg."):
                    target = module.removeprefix("HomAlg.")
                    if "." not in target:
                        failures.append(
                            f"{identifier}: use explicit node imports instead of {module}"
                        )
                    elif target not in proof_dependencies or target in dependencies:
                        required.add(target)
            for dependency in sorted(required - owned):
                if not self.accepted_interface(dependency):
                    failures.append(
                        f"{identifier}: statement interface is not current and reviewed: "
                        f"{dependency}"
                    )
        if not nx.is_directed_acyclic_graph(internal):
            failures.append("Statement unit contains a cyclic interface dependency")
        return sorted(set(failures))


def unit_blockers(
    repo: Path, record: dict[str, Any], *, frontier: StatementFrontier | None = None
) -> list[str]:
    info = record.get("metadata", {}).get("homalg", {})
    if info.get("granularity") != "node":
        return []
    identifiers = info.get("node_ids", [])
    if not identifiers:
        return ["A statement unit must declare its node_ids"]
    expected = {f"HomAlg/{identifier.replace('.', '/', 1)}.lean" for identifier in identifiers}
    actual = {
        path
        for path in record.get("write_set", {}).get("files", [])
        if path.startswith("HomAlg/") and path.endswith(".lean")
    }
    if actual != expected:
        return ["Statement unit node_ids and immutable Lean scope disagree"]
    frontier = frontier or StatementFrontier(repo, info["doc"])
    expanded = sorted({node for identifier in identifiers for node in frontier.group(identifier)})
    return frontier.blockers(expanded)
