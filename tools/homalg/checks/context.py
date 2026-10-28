"""Shared rule context and portable findings (R7.1)."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from homalg.headers import Header
from homalg.leantext import Command
from homalg.schemas import SchemaStore


@dataclass(frozen=True)
class Finding:
    """One actionable validation diagnostic."""

    rule: str
    severity: Literal["error", "warning"]
    file: str
    message: str
    line: int | None = None
    node: str | None = None
    fix: str | None = None


@dataclass
class Context:
    """Read-only authored and compiled facts shared by independently registered rules."""

    repo: Path
    schemas: SchemaStore
    docs: dict[str, dict[str, Any]] = field(default_factory=dict)
    headers: dict[str, Header] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)
    valid_headers: dict[str, Header] = field(default_factory=dict)
    taxonomy: dict[str, dict[str, Any]] = field(default_factory=dict)
    selected: tuple[str, ...] = ()
    all_docs: dict[str, dict[str, Any]] = field(default_factory=dict)
    all_headers: dict[str, Header] = field(default_factory=dict)
    all_sources: dict[str, str] = field(default_factory=dict)
    commands: dict[str, list[Command]] = field(default_factory=dict)
    claims: dict[str, dict[str, Any]] = field(default_factory=dict)
    inventories: dict[str, dict[str, Any]] = field(default_factory=dict)
    retired: dict[str, dict[str, Any]] = field(default_factory=dict)
    existing_nodes: set[str] = field(default_factory=set)
    nodes_files: dict[str, dict[str, Any]] = field(default_factory=dict)
    expected_nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    derived: dict[str, dict[str, Any]] = field(default_factory=dict)
    declarations: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    changed_paths: set[str] = field(default_factory=set)
    base_sources: dict[str, str] = field(default_factory=dict)
    pr: dict[str, Any] = field(default_factory=dict)
    preloaded: list[Finding] = field(default_factory=list)
    pr_findings: list[Finding] = field(default_factory=list)
    relation_records: list[tuple[str, dict[str, Any], bool]] = field(default_factory=list)
    relation_reviews: dict[str, Any] = field(default_factory=dict)
    evolution_files: dict[str, dict[str, Any]] = field(default_factory=dict)
    health: dict[str, Any] = field(default_factory=dict)
    now: str | None = None
    file_mode: bool = False

    def node_headers(self) -> dict[str, Header]:
        """Index all valid authored headers by stable node id."""
        return {header.metadata["id"]: header for header in self.all_headers.values()}

    def main_declarations(self, header: Header) -> list[dict[str, Any]]:
        """Select exactly the main declarations owned by this node's module."""
        records = self.declarations.get(f"HomAlg.{header.metadata['id']}", {})
        return [records[name] for name in header.metadata.get("decls", []) if name in records]

    def resolve_node(self, identifier: str) -> str:
        """Follow retired aliases, rejecting cycles rather than hiding dangling history."""
        seen = set()
        while identifier in self.retired:
            if identifier in seen:
                raise ValueError(f"Retired-node alias cycle at {identifier}")
            seen.add(identifier)
            record = self.retired[identifier]
            target = record.get("moved_to") or record.get("merged_into")
            if not target:
                break
            identifier = target
        return identifier
