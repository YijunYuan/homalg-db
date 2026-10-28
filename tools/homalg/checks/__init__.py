"""Complete validation registry with explicit environmental prerequisites."""

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module

from homalg.checks.context import Context, Finding


@dataclass(frozen=True)
class Rule:
    """A check and the facts needed to evaluate it, never an implicit pass."""

    name: str
    check: Callable[[Context], list[Finding]]
    needs_lean: bool = False
    needs_pr_context: bool = False
    needs_private: bool = False
    needs_prerender: bool = False
    explicit_only: bool = False

    @property
    def needs_pr(self) -> bool:
        """Public metadata alias used by editor and CI integrations."""
        return self.needs_pr_context

    def __call__(self, ctx: Context) -> list[Finding]:
        """Keep rule invocation concise for the runner and standalone tests."""
        return self.check(ctx)


_NAMES = [
    "aux-parent",
    "bridge-witness",
    "cited-source",
    "cited-used",
    "claim-author",
    "claim-files-only",
    "claim-limit",
    "claim-owner",
    "claim-schema",
    "claim-sync",
    "claim-window",
    "collaborator-only",
    "concepts-known",
    "decl-unique",
    "decls-exist",
    "deps-acyclic",
    "deps-exist",
    "deps-imported",
    "deps-statement-unused",
    "deps-verified",
    "deviation-justified",
    "dispute-sync",
    "dispute-valid",
    "doc-acyclic",
    "doc-import-direction",
    "english-only",
    "evolution-valid",
    "fidelity-reopened",
    "file-size",
    "foundation-declared",
    "foundations-confirmed",
    "header-sections",
    "header-syntax",
    "hollow-def",
    "hypothesis-packaging",
    "id-grammar",
    "id-path",
    "instance-scope",
    "inventory-valid",
    "kind-decl",
    "label-unique",
    "lean-build",
    "lean-style",
    "markdown-renders",
    "mathlib-bypass-proof",
    "mathlib-bypass-statement",
    "mathlib-decls-exist",
    "namespace",
    "no-pdf",
    "nodes-json-fresh",
    "nodes-json-stale",
    "out-of-scope",
    "owner-approval",
    "registry-none",
    "relation-append-only",
    "relation-review",
    "relation-reviews-valid",
    "relations-valid",
    "relations-year-order",
    "review-policy",
    "roots-fresh",
    "route-faithful",
    "schema-claim",
    "schema-document",
    "schema-header",
    "schema-taxonomy",
    "sorry-named",
    "statement-provenance",
    "tags-known",
    "taxonomy-append-only",
    "taxonomy-merge-cycle",
    "touch-scope",
]
_LEAN = [
    "bridge-witness",
    "decls-exist",
    "deps-statement-unused",
    "deps-verified",
    "fidelity-reopened",
    "hollow-def",
    "hypothesis-packaging",
    "instance-scope",
    "kind-decl",
    "lean-build",
    "mathlib-bypass-proof",
    "mathlib-bypass-statement",
    "mathlib-decls-exist",
    "nodes-json-fresh",
    "route-faithful",
]
_PR = [
    "claim-author",
    "claim-files-only",
    "claim-limit",
    "claim-owner",
    "claim-schema",
    "claim-sync",
    "claim-window",
    "collaborator-only",
    "foundations-confirmed",
    "owner-approval",
    "relation-append-only",
    "taxonomy-append-only",
    "touch-scope",
]

RULES = {
    name: Rule(
        name,
        import_module(f"homalg.checks.{name.replace('-', '_')}").check,
        needs_lean=name in _LEAN,
        needs_pr_context=name in _PR,
        needs_private=name == "statement-provenance",
        needs_prerender=name == "markdown-renders",
        explicit_only=name == "owner-approval",
    )
    for name in _NAMES
}
PENDING_RULES: list[str] = []
