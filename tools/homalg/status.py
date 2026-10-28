"""Shared local/global/headline status semantics for index, dashboard and progress."""

from collections import Counter
from typing import Any

STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
HEADLINES = ("in-progress", "statement-complete", "proof-complete", "error")
STATUSES = (
    "planned",
    "stated",
    "proved-pending-deps",
    "proved-modulo-citations",
    "proved",
    "proved-with-axioms",
    "disputed",
    "pruned",
)


def local_status(declarations: list[str], exported: dict[str, dict[str, Any]]) -> str:
    """Require every main declaration to be present and free of directly introduced sorry."""
    if not declarations or any(name not in exported for name in declarations):
        return "planned"
    return "stated" if any(exported[name]["direct_sorry"] for name in declarations) else "proved"


def compute_status(
    authored: dict[str, Any],
    derived: dict[str, Any],
    axioms: dict[str, dict[str, Any]],
    blocked_by: list[str],
    *,
    reopened: bool = False,
) -> tuple[str, str | None]:
    """Return detailed/headline states, distinguishing raised from confirmed disputes."""
    auxiliary = authored.get("aux", {})
    local = derived["local_status"]
    if auxiliary.get("pruned", False):
        base = "pruned"
    elif local != "proved":
        base = local
    elif blocked_by and all(node.split(".", 1)[1].startswith("Cited_") for node in blocked_by):
        base = "proved-modulo-citations"
    elif any(value["transitive_sorry"] for value in axioms.values()):
        base = "proved-pending-deps"
    elif any(set(value["axioms"]) - STANDARD_AXIOMS for value in axioms.values()):
        base = "proved-with-axioms"
    else:
        base = "proved"
    dispute = authored.get("dispute", {})
    disputed = dispute.get("status") == "open"
    status = "disputed" if disputed and base != "pruned" else base
    if base == "pruned" or "informal" in authored:
        headline = None
    elif disputed and dispute.get("confirmed_by"):
        headline = "error"
    else:
        locked = bool(authored.get("fidelity", {}).get("reviewed")) and not reopened
        if auxiliary:
            locked = bool(authored.get("decls")) and local != "planned"
        if not locked:
            headline = "in-progress"
        elif base in {"proved", "proved-with-axioms", "proved-modulo-citations"}:
            headline = "proof-complete"
        else:
            headline = "statement-complete"
    return status, headline


def status_counts(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Count items, auxiliaries and citations separately; omit informal/pruned headlines."""
    output: dict[str, Any] = {
        "headline_counts": dict.fromkeys(HEADLINES, 0),
        "aux_headline_counts": dict.fromkeys(HEADLINES, 0),
        "cited_headline_counts": dict.fromkeys(HEADLINES, 0),
        "node_counts": dict.fromkeys((*STATUSES, "informal", "cited"), 0),
        "fidelity_counts": dict.fromkeys(("faithful", "foundation", "deviates", "reviewed"), 0),
        "items_total": 0,
        "aux_total": 0,
    }
    for node in nodes:
        authored, global_ = node["authored"], node["global"]
        is_cited = node["id"].split(".", 1)[1].startswith("Cited_")
        is_aux = bool(authored.get("aux"))
        if "informal" in authored:
            output["node_counts"]["informal"] += 1
        else:
            output["node_counts"][global_["status"]] += 1
        output["node_counts"]["cited"] += int(is_cited)
        output["aux_total"] += int(is_aux)
        output["items_total"] += int(not is_aux and not is_cited)
        group = (
            "aux_headline_counts"
            if is_aux
            else ("cited_headline_counts" if is_cited else "headline_counts")
        )
        if global_["headline"] is not None:
            output[group][global_["headline"]] += 1
        output["fidelity_counts"][authored["fidelity"]["status"]] += 1
        output["fidelity_counts"]["reviewed"] += int(
            bool(authored["fidelity"].get("reviewed")) and not global_["reopened"]
        )
    return output


def facets(nodes: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Build stable multi-value search facets from joined nodes."""
    groups: dict[str, Counter[str]] = {
        key: Counter()
        for key in (
            "doc",
            "year",
            "author",
            "kind",
            "headline",
            "status",
            "fidelity",
            "tag",
            "concept",
        )
    }
    for node in nodes:
        authored, global_ = node["authored"], node["global"]
        values = {
            "doc": [authored["doc"]],
            "year": [str(global_["doc_year"])],
            "author": global_["doc_authors"],
            "kind": [authored["kind"]],
            "headline": [global_["headline"]] if global_["headline"] else [],
            "status": [global_["status"]],
            "fidelity": [authored["fidelity"]["status"]],
            "tag": authored["tags"],
            "concept": sorted(set(sum(authored.get("concepts", {}).values(), []))),
        }
        for key, items in values.items():
            groups[key].update(items)
    return {key: dict(sorted(counter.items())) for key, counter in groups.items()}
