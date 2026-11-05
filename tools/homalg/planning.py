"""Create only newly unlocked stage tasks with explicit, immutable file scopes."""

import hashlib
import json
import re
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

from homalg import settlement
from homalg.blueprint import source_order, source_rank
from homalg.claims import claim_view, load_status_history
from homalg.documents import dump_metadata, parse_metadata, read_document, write_metadata
from homalg.engine import horizon, settings, tasks
from homalg.headers import imports_of, parse_header
from homalg.human import record_human_change, require_human
from homalg.io import atomic_write, json_text
from homalg.planning_facts import PlanningFacts, StalePlanningInputs
from homalg.repository import node_paths
from homalg.review_policy import (
    agent_review_record,
    agent_reviews_allowed,
    early_review_valid,
    foundation_confirmed,
    valid_agent_review,
)
from homalg.runtime_state import document_state
from homalg.schemas import SchemaStore, load_yaml
from homalg.stages import DEFINITION_KINDS, evaluate
from homalg.statement_frontier import StatementFrontier, unit_blockers
from homalg.transcription import status as transcription_status

STAGES = ("T", "INV", "DAG", "CITED", "STMT", "PROOF")
AUTHOR_GROUP_SIZE = 4
DEFAULT_STATEMENT_BATCH = 12
DEFAULT_REVIEW_BATCH = 16
MAX_STATEMENT_BATCH = 32

TEMPLATES = {
    "T": "transcribe",
    "INV": "inventory",
    "DAG": "dag",
    "CITED": "cited",
    "STMT": "statements",
    "PROOF": "proofs",
}


def chapter_ranges(document: dict[str, Any], selected: tuple[str, ...]) -> list[dict[str, Any]]:
    """Require integer source ranges for every selected chapter and section."""
    chapters = [
        item
        for item in document.get("structure", [])
        if not selected or item["chapter"] in selected
    ]
    if not chapters or set(selected) - {item["chapter"] for item in chapters}:
        raise ValueError("Select known document chapters with populated page ranges")
    if not document.get("item_kinds"):
        raise ValueError("Fill document.item_kinds before planning")
    for chapter in chapters:
        for item in [chapter, *chapter.get("sections", [])]:
            pages = item.get("pages", {}) if isinstance(item, dict) else {}
            if (
                not all(type(pages.get(name)) is int for name in ("first", "last"))
                or pages["first"] > pages["last"]
            ):
                raise ValueError(
                    "Every selected chapter/section needs integer first/last page bounds"
                )
            if (
                item != chapter
                and not chapter["pages"]["first"]
                <= pages["first"]
                <= pages["last"]
                <= chapter["pages"]["last"]
            ):
                raise ValueError("Section pages must lie within their chapter")
            offset = document.get("pdf", {}).get("page_offset", 0)
            if (
                "pdf" in document
                and not 1
                <= pages["first"] + offset
                <= pages["last"] + offset
                <= document["pdf"]["pages"]
            ):
                raise ValueError("Source page ranges map outside the registered PDF")
    return chapters


class AuthoredNodeIndex:
    """One planning call's authored nodes and inventory order, with no persistent cache."""

    def __init__(self, repo: Path, key: str):
        self.repo, self.key = repo, key
        self.nodes = [parse_header(path.read_text()).metadata for path in node_paths(repo, [key])]
        self.rank = source_rank(repo, key)

    def select(self, chapter: str | None, kind_group: str | None) -> list[dict[str, Any]]:
        """Keep the original primary/immediate-auxiliary selection and stable ordering."""
        primary = [
            node
            for node in self.nodes
            if "aux" not in node
            and (chapter is None or node["source"].get("chapter") == chapter)
            and (kind_group == "cited") == ("cited" in node)
        ]
        if kind_group in {"definitions", "theorems"}:
            primary = [
                node
                for node in primary
                if (node["kind"] in DEFINITION_KINDS) == (kind_group == "definitions")
            ]
        selected = {node["id"] for node in primary}
        return source_order(
            self.repo,
            self.key,
            [
                node
                for node in self.nodes
                if node["id"] in selected or node.get("aux", {}).get("parent") in selected
            ],
            rank=self.rank,
        )


def scope_nodes(
    repo: Path, key: str, chapter: str | None, kind_group: str | None = None
) -> list[dict[str, Any]]:
    """Select current source items and auxiliaries; independent callers always reread inputs."""
    return AuthoredNodeIndex(repo, key).select(chapter, kind_group)


def proposed_task(
    repo: Path,
    key: str,
    stage: str,
    number: int,
    *,
    chapter: str | None = None,
    section: str | None = None,
    pages: list[int] | None = None,
    kind_group: str | None = None,
    node_index: AuthoredNodeIndex | None = None,
) -> dict[str, Any]:
    """Construct explicit scopes before handing the task to the engine."""
    task_id = f"{key}.{stage}.{number}"
    info: dict[str, Any] = {
        "doc": key,
        "stage": stage,
        "chapter": chapter,
        "attempts": 0,
        "pages": pages or [],
    }
    if section:
        info["section"] = section
    if kind_group:
        info["kind_group"] = kind_group
    if node_index is not None and (node_index.repo != repo or node_index.key != key):
        raise ValueError("Authored node index belongs to another repository/document")
    nodes = (
        node_index.select(chapter, kind_group)
        if node_index is not None
        else scope_nodes(repo, key, chapter, kind_group)
    )
    if stage == "T":
        files = [f"references/{key}/tex/page-{page:04}.tex" for page in pages or []]
        files.append(f"references/{key}/transcription.yaml")
    elif stage == "INV":
        files = [f"literature/{key}/inventory.yaml", f"literature/{key}/document.yaml"]
    else:
        files = [f"HomAlg/{key}/{node['id'].split('.', 1)[1]}.lean" for node in nodes]
        if stage != "DAG":
            files.extend(
                f"literature/{key}/reviews/{node['id'].split('.', 1)[1]}.md" for node in nodes
            )
    return {
        "id": task_id,
        "metadata": {"homalg": info},
        "write_set": {"files": sorted(set(files))},
        "node_ids": [node["id"] for node in nodes],
        "roadmap_refs": [f"{key}.{stage}"],
    }


def unlocked_tasks(
    repo: Path,
    key: str,
    chapters: list[dict[str, Any]],
    *,
    persist_transcription: bool = True,
    statement_frontier: bool = False,
    statement_nodes: tuple[str, ...] = (),
    statement_batch_size: int = 4,
) -> tuple[list[dict[str, Any]], bool]:
    """Evaluate stage prerequisites from current evidence, preserving existing task statuses."""
    # Finish allowed reconciliation, then read every planning input inside the guard.
    if read_document(repo, key)["type"] != "synthetic":
        transcription_status(repo, key, persist=persist_transcription)
    facts = PlanningFacts(repo)
    document = read_document(repo, key)
    if chapter_ranges(document, tuple(chapter["chapter"] for chapter in chapters)) != chapters:
        raise StalePlanningInputs("Selected chapter ranges changed; restart the complete sweep")
    synthetic = document["type"] == "synthetic"
    offset = document.get("pdf", {}).get("page_offset", 0)
    reviewed = {} if synthetic else transcription_status(repo, key, persist=False)["pages"]
    proposals: list[dict[str, Any]] = []
    existing = {record["id"]: record for record in tasks(repo, key)}
    propose = partial(proposed_task, repo, key, node_index=AuthoredNodeIndex(repo, key))

    def complete(candidate: dict[str, Any]) -> bool:
        record = existing.get(candidate["id"])
        if record is None:
            return False
        try:
            return evaluate(
                repo,
                record,
                refresh_exports=False,
                persist_transcription=False,
                facts=facts,
            )["complete"]
        except (OSError, ValueError):
            return False

    if not synthetic:
        selected_pages = {
            page + offset
            for chapter in chapters
            for page in range(chapter["pages"]["first"], chapter["pages"]["last"] + 1)
        }
        pages = sorted(
            {
                page + offset
                for chapter in document["structure"]
                for page in range(chapter["pages"]["first"], chapter["pages"]["last"] + 1)
            }
        )
        first = re.match(r"([0-9]+)[–-]", document.get("journal", {}).get("pages", ""))
        if first:
            pages = sorted(set(pages) | set(range(int(first.group(1)) + offset, pages[0])))
        chunks: list[list[int]] = []
        for page in pages:
            if not chunks or len(chunks[-1]) == 5 or chunks[-1][-1] + 1 != page:
                chunks.append([])
            chunks[-1].append(page)
        for number, chunk in enumerate(chunks, 1):
            if selected_pages.intersection(chunk):
                proposals.append(propose("T", number, pages=chunk))
    inventory_number = 0
    dag_ready: dict[str, bool] = {}
    dag_candidates = []
    definitions = []
    chapter_numbers = {
        chapter["chapter"]: number for number, chapter in enumerate(document["structure"], 1)
    }
    selected_ids = {chapter["chapter"] for chapter in chapters}
    for number, chapter in enumerate(document["structure"], 1):
        if chapter["chapter"] not in selected_ids:
            inventory_number += len(chapter.get("sections") or [chapter])
            continue
        inventory = []
        for section in chapter.get("sections") or [chapter]:
            inventory_number += 1
            pages = list(
                range(section["pages"]["first"] + offset, section["pages"]["last"] + offset + 1)
            )
            candidate = propose(
                "INV",
                inventory_number,
                chapter=chapter["chapter"],
                section=section.get("id"),
                pages=pages,
            )
            inventory.append(candidate)
            if synthetic or all(
                reviewed.get(f"{page:04}", {}).get("status") == "reviewed" for page in pages
            ):
                proposals.append(candidate)
        dag = propose("DAG", number, chapter=chapter["chapter"])
        dag_candidates.append(dag)
        if all(complete(candidate) for candidate in inventory):
            proposals.append(dag)
        dag_ready[chapter["chapter"]] = complete(dag)
        definitions.append(
            propose("STMT", number, chapter=chapter["chapter"], kind_group="definitions")
        )
    cited = propose("CITED", 1, kind_group="cited")
    if all(dag_ready.values()):
        proposals.append(cited)
    blocked_foundations = early_review_valid(document.get("early_review"), repo) and any(
        not foundation_confirmed(entry, repo) for entry in document["foundations"]
    )
    for chapter, definition in zip(chapters, definitions, strict=True):
        number = chapter_numbers[chapter["chapter"]]
        if dag_ready[chapter["chapter"]] and not blocked_foundations:
            proposals.append(definition)
        theorems = propose(
            "STMT",
            len(document["structure"]) + number,
            chapter=chapter["chapter"],
            kind_group="theorems",
        )
        if (
            early_review_valid(document.get("early_review"), repo)
            and complete(cited)
            and dag_ready[chapter["chapter"]]
            and not blocked_foundations
        ):
            proposals.append(theorems)
        if complete(definition) and complete(theorems) and not blocked_foundations:
            proposals.append(propose("PROOF", number, chapter=chapter["chapter"]))
    first_definitions = complete(
        propose(
            "STMT",
            1,
            chapter=document["structure"][0]["chapter"],
            kind_group="definitions",
        )
    )
    if statement_frontier or statement_nodes:
        frontier = StatementFrontier(
            repo, key, state_loader=lambda root, doc: facts.state(doc, document_state)
        )
        records = tasks(repo, key)
        proposals.extend(
            candidate
            for candidate in statement_units(
                repo,
                key,
                chapters,
                statement_nodes,
                batch_size=statement_batch_size,
                frontier=frontier,
            )
            if not candidate["blockers"]
        )
        # Delivered nodes go to separate review units, whole author deliveries each.
        from homalg.phases import review_units

        proposals.extend(
            review_units(
                repo,
                key,
                chapters,
                frontier=frontier,
                batch_size=DEFAULT_REVIEW_BATCH,
                records=records,
            )
        )
    facts.assert_current()
    return proposals, first_definitions


def statement_units(
    repo: Path,
    key: str,
    chapters: list[dict[str, Any]],
    explicit: tuple[str, ...] = (),
    *,
    frontier: StatementFrontier | None = None,
    batch_size: int = 1,
) -> list[dict[str, Any]]:
    """Discover independent execution units without completing a chapter stage."""
    frontier = frontier or StatementFrontier(repo, key)
    candidates = []
    for identifier in frontier.node_ids({chapter["chapter"] for chapter in chapters}, explicit):
        node = frontier.headers[identifier].metadata
        identifiers = frontier.group(identifier)
        local = identifier.split(".", 1)[1]
        files = [f"HomAlg/{value.replace('.', '/', 1)}.lean" for value in identifiers]
        files += [f"literature/{key}/reviews/{value.split('.', 1)[1]}.md" for value in identifiers]
        candidates.append(
            {
                "id": f"{key}.STMT.Unit_{local}",
                "metadata": {
                    "roadmap_status_sync": False,
                    "homalg": {
                        "doc": key,
                        "stage": "STMT",
                        "phase": "author",
                        "chapter": node["source"]["chapter"],
                        "section": node["source"].get("section"),
                        "attempts": 0,
                        "pages": node["source"]["pages"],
                        "granularity": "node",
                        "kind_group": "definitions"
                        if node["kind"] in DEFINITION_KINDS
                        else "theorems",
                        "node_ids": identifiers,
                    },
                },
                "write_set": {"files": sorted(files)},
                "node_ids": identifiers,
                "roadmap_refs": [f"{key}.STMT"],
                "blockers": frontier.blockers(identifiers),
            }
        )
    if batch_size < 1:
        raise ValueError("Statement batch size must be positive")
    # Registered scopes never grow or get duplicated by a later frontier sweep.
    # Preserve held/cancelled units too: batching cannot bypass an operator hold.
    by_primary = {candidate["node_ids"][0]: candidate for candidate in candidates}
    records = tasks(repo, key)
    # A settlement explicitly hands released primaries back to the frontier. A
    # cancelled unit keeps holding every other primary, but not those.
    released = {
        primary
        for record in records
        for entry in record.get("metadata", {}).get("homalg", {}).get("settlements", [])
        for primary in entry.get("released", {})
    }
    reserved = set()
    preserved = []
    phased = False
    for record in records:
        info = record.get("metadata", {}).get("homalg", {})
        if info.get("granularity") != "node":
            continue
        if info.get("phase") in {"author", "review"}:
            phased = True
            if record.get("status") not in {"queued", "running", "blocked"}:
                # A finished author/review unit holds nothing: each primary's derived
                # state (settled, awaiting review, parked, needs authoring) decides.
                continue
        primary = info.get("primary_nodes") or [
            identifier
            for identifier in info.get("node_ids", [])
            if identifier in frontier.headers and "aux" not in frontier.headers[identifier].metadata
        ]
        if record.get("status") == "cancelled":
            reserved.update(identifier for identifier in primary if identifier not in released)
            if any(identifier in released for identifier in primary):
                continue
        else:
            reserved.update(primary)
        if primary and all(identifier in by_primary for identifier in primary):
            preserved.append(
                {
                    **record,
                    "node_ids": info["node_ids"],
                    "roadmap_refs": [f"{key}.STMT"],
                    "blockers": unit_blockers(repo, record, frontier=frontier),
                }
            )
    if phased:
        from homalg.phases import node_states

        states = node_states(repo, key, frontier, records)
        reserved.update(
            node_id
            for node_id, state in states.items()
            if state["state"] in {"awaiting_review", "parked"}
        )
    fresh = [
        candidate
        for candidate in candidates
        if candidate["node_ids"][0] not in reserved
        and not all(frontier.settled_statement(identifier) for identifier in candidate["node_ids"])
    ]
    held = [candidate for candidate in fresh if candidate["blockers"]]
    ready = [candidate for candidate in fresh if not candidate["blockers"]]

    def dependencies(candidate: dict[str, Any]) -> set[str]:
        result = set()
        for identifier in candidate["node_ids"]:
            node = frontier.headers[identifier].metadata
            result.update(node["deps"]["statement"])
            result.update(
                module.removeprefix("HomAlg.")
                for module in imports_of(frontier.sources[identifier])
                if module.startswith("HomAlg.")
                and module.removeprefix("HomAlg.") not in node["deps"]["proof"]
            )
        return result

    def disputed(candidate: dict[str, Any]) -> bool:
        # An open dispute refuses the statement lock until adjudication; batching
        # it would hold every independent sibling behind that one decision.
        return any(
            frontier.headers[identifier].metadata.get("dispute", {}).get("status") == "open"
            for identifier in candidate["node_ids"]
            if identifier in frontier.headers
        )

    batches = []
    while ready:
        selected = [ready.pop(0)]
        for candidate in list(ready):
            if len(selected) >= batch_size or disputed(selected[0]):
                break
            if disputed(candidate):
                continue
            if (
                candidate["metadata"]["homalg"]["chapter"]
                != selected[0]["metadata"]["homalg"]["chapter"]
            ):
                continue
            if all(
                not (dependencies(candidate) & set(other["node_ids"]))
                and not (dependencies(other) & set(candidate["node_ids"]))
                for other in selected
            ):
                selected.append(candidate)
                ready.remove(candidate)
        if len(selected) == 1:
            batches.extend(selected)
            continue
        primary = [candidate["node_ids"][0] for candidate in selected]
        digest = hashlib.sha256("\0".join(sorted(primary)).encode()).hexdigest()[:12]
        identifiers = [identifier for candidate in selected for identifier in candidate["node_ids"]]
        info = dict(selected[0]["metadata"]["homalg"])
        # Contiguous groups of a few primaries: one writer each, all in one wave.
        chunks = [
            selected[index : index + AUTHOR_GROUP_SIZE]
            for index in range(0, len(selected), AUTHOR_GROUP_SIZE)
        ]
        info.update(
            primary_nodes=primary,
            node_ids=identifiers,
            author_groups=[
                {
                    "primary": chunk[0]["node_ids"][0],
                    "node_ids": [node for candidate in chunk for node in candidate["node_ids"]],
                }
                for chunk in chunks
            ],
        )
        info["pages"] = sorted(
            {page for candidate in selected for page in candidate["metadata"]["homalg"]["pages"]}
        )
        info["kind_group"] = (
            "definitions"
            if all(
                candidate["metadata"]["homalg"]["kind_group"] == "definitions"
                for candidate in selected
            )
            else "items"
        )
        batches.append(
            {
                "id": f"{key}.STMT.UnitBatch_{digest}",
                "metadata": {"homalg": info, "roadmap_status_sync": False},
                "node_ids": identifiers,
                "roadmap_refs": [f"{key}.STMT"],
                "blockers": [],
                "write_set": {
                    "files": sorted(
                        {path for candidate in selected for path in candidate["write_set"]["files"]}
                    )
                },
            }
        )
    return [*preserved, *batches, *held]


def render_objective(
    repo: Path, record: dict[str, Any], *, login: str, document: dict[str, Any]
) -> str:
    """Render the generated objective exactly as task creation would."""
    info = record["metadata"]["homalg"]
    name = {"author": "statement-author", "review": "statement-review"}.get(
        info.get("phase"), TEMPLATES[info["stage"]]
    )
    template = (repo / "horizon/tasks" / f"{name}.md").read_text()
    handoffs = "\n".join(
        f"- {item['path']} (task {item['task']}, author {item['author_session']}): "
        + ", ".join(item["node_ids"])
        for item in info.get("handoffs", [])
    )
    fields = {
        "doc_key": info["doc"],
        "doc_title": document["title"],
        "chapter": info.get("chapter") or "all",
        "section": info.get("section") or "all",
        "pages": ", ".join(map(str, info["pages"])),
        "kind_group": info.get("kind_group") or "items",
        "node_list": ", ".join(record["node_ids"]) or "none yet",
        "write_scope": ", ".join(record["write_set"]["files"]),
        "login": login,
        "task_id": record["id"],
        "transcriber_model": settings(repo).get("transcriber_model", "a vision-capable model"),
        "handoff_list": handoffs or "none",
    }
    objective = template.format_map(fields)
    if info.get("author_groups"):
        objective += AUTHOR_GROUPS_HEADER
        objective += "\n".join(
            f"- {group['primary']}: {', '.join(group['node_ids'])}"
            for group in info["author_groups"]
        )
        objective += AUTHOR_GROUPS_FOOTER
    return objective


AUTHOR_GROUPS_HEADER = "\nNative parallel author groups (each group has one actual author):\n"
AUTHOR_GROUPS_FOOTER = (
    "\nDispatch these independent groups concurrently in isolated native-owned workers. "
    "Keep independent review and canonical acceptance coordinated.\n"
)


def create_task(
    repo: Path,
    record: dict[str, Any],
    *,
    login: str,
    document: dict[str, Any],
    guidance: str = "",
    inbox_refs: tuple[str, ...] | list[str] = (),
) -> None:
    """Create through the engine CLI, then add only the documented HomAlg metadata.

    ``guidance`` carries obligations a settled source task attached to released
    nodes; it is appended verbatim and makes the objective non-generated.
    """
    info = record["metadata"]["homalg"]
    objective = render_objective(repo, record, login=login, document=document)
    generated = objective
    if guidance.strip():
        objective += "\n\n" + guidance.strip() + "\n"
    args = [
        "task",
        "add",
        "--id",
        record["id"],
        "--project",
        "HomAlg",
        "--objective",
        objective,
        "--title",
        f"{info['doc']} {info['stage']} {info.get('chapter') or ''}",
        "--roadmap-ref",
        record["roadmap_refs"][0],
        "--author",
        "homalg",
    ]
    for file in record["write_set"]["files"]:
        args.extend(("--file", file))
    if info.get("granularity") == "node":
        # Review first: downstream authoring waits on accepted interfaces.
        args.extend(("--priority", "urgent" if info.get("phase") == "review" else "high"))
    horizon(repo, *args)
    if inbox_refs:
        refs = ["task", "set", record["id"], "--author", "homalg", "--json"]
        for ref in dict.fromkeys(inbox_refs):
            refs.extend(("--inbox-ref", ref))
        horizon(repo, *refs)
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    saved = parse_metadata(path.read_text())
    stored = dict(info)
    if objective == generated:
        # Lets settlement tell a plain generated objective from one later extended.
        stored["objective_sha256"] = hashlib.sha256(objective.encode()).hexdigest()
    saved.setdefault("metadata", {})["homalg"] = stored
    if record.get("metadata", {}).get("roadmap_status_sync") is False:
        saved["metadata"]["roadmap_status_sync"] = False
    atomic_write(path, dump_metadata(saved))


def plan(
    repo: Path,
    key: str,
    *,
    chapters: tuple[str, ...] = (),
    advance: bool = False,
    early_review_ok: bool = False,
    by: str | None = None,
    session: str | None = None,
    author_session: str | None = None,
    no_claim: bool = False,
    proofs: str | None = None,
    statement_frontier: bool | None = None,
    statement_nodes: tuple[str, ...] = (),
    statement_batch_size: int | None = None,
) -> dict[str, Any]:
    """Plan eligible work using explicit human or enabled independent-agent review evidence."""
    document = read_document(repo, key)
    overlay = repo / ".archon-horizon/overlay" / f"plan-{key}.json"
    prior = json.loads(overlay.read_text()) if overlay.exists() else {}
    proofs = proofs or prior.get("proofs", "included")
    explicitly_disabled = statement_frontier is False
    statement_frontier = (
        prior.get("statement_frontier", False) if statement_frontier is None else statement_frontier
    )
    statement_nodes = statement_nodes or (
        () if explicitly_disabled else tuple(prior.get("statement_nodes", []))
    )
    statement_batch_size = (
        prior.get("statement_batch_size", DEFAULT_STATEMENT_BATCH)
        if statement_batch_size is None
        else statement_batch_size
    )
    if not 1 <= statement_batch_size <= MAX_STATEMENT_BATCH:
        raise ValueError(f"Statement batch size must be between 1 and {MAX_STATEMENT_BATCH}")
    unit_options = (
        {
            "statement_frontier": statement_frontier,
            "statement_nodes": statement_nodes,
            "statement_batch_size": statement_batch_size,
        }
        if statement_frontier or statement_nodes
        else {}
    )
    if proofs not in {"deferred", "included"}:
        raise ValueError("Proof mode must be deferred or included")
    if advance and not chapters:
        chapters = tuple(prior.get("chapters", []))
        no_claim = prior.get("no_claim", no_claim)
    login = settings(repo).get("login")
    if no_claim:
        if document["type"] != "synthetic":
            raise ValueError("--no-claim is restricted to synthetic documents")
        login = login or "fixture-user"
    else:
        if not login:
            raise ValueError("Run homalg horizon-init to cache the current GitHub identity")
        claim = load_yaml((repo / "literature" / key / "claim.yaml").read_text())
        view = claim_view(
            claim,
            load_status_history(repo, key),
            datetime.now(UTC),
            policy=load_yaml((repo / "taxonomy/policy.yaml").read_text()),
            schemas=SchemaStore(repo / "schema"),
        )
        if view["state"] != "active" or view["holder"].lower() != login.lower():
            raise ValueError("Planning requires an active claim held by the cached GitHub identity")
        claimed = view.get("scope", {}).get("chapters", [])
        if claimed and chapters and set(chapters) - set(claimed):
            raise ValueError("Requested chapters exceed the active claim")
        if claimed and not chapters:
            chapters = tuple(claimed)
    selected = chapter_ranges(document, chapters)
    selected_ids = [item["chapter"] for item in selected]
    if (
        prior.get("chapters")
        and prior["chapters"] != selected_ids
        and any(record.get("status") not in {"done", "cancelled"} for record in tasks(repo, key))
    ):
        raise ValueError(
            "Existing task scopes are immutable; finish this chapter plan before changing scope"
        )
    proposals, first_complete = unlocked_tasks(repo, key, selected, **unit_options)
    if early_review_ok:
        if (
            not by
            or not first_complete
            or any(not foundation_confirmed(entry, repo) for entry in document["foundations"])
        ):
            raise ValueError(
                "Early review requires --by, completed first definitions and confirmed foundations"
            )
        if session:
            previous = document.get("early_review", {})
            if previous and previous.get("kind") != "agent":
                raise ValueError(
                    "An agent review cannot replace existing human early-review evidence"
                )
            evidence = agent_review_record(
                repo,
                by=by,
                session=session,
                author_session=author_session or "",
            )
            for node in scope_nodes(repo, key, document["structure"][0]["chapter"], "definitions"):
                lock = node["fidelity"].get("reviewed", {})
                if lock.get("kind") != "human" and not valid_agent_review(lock):
                    raise ValueError(
                        "First definitions need independent, satisfactory review locks"
                    )
        else:
            if author_session:
                raise ValueError("--author-session requires --session")
            require_human(f"plan {key} --early-review-ok", repo, details=dump_metadata(document))
            evidence = {"by": by, "on": datetime.now(UTC).date().isoformat()}
        if read_document(repo, key) != document:
            raise ValueError("Document changed while human review was pending")
        document["early_review"] = evidence
        path = repo / "literature" / key / "document.yaml"
        write_metadata(path, document, "document.schema.json", SchemaStore(repo / "schema"))
        if not session:
            record_human_change(repo, f"plan {key} --early-review-ok", [path])
        proposals, first_complete = unlocked_tasks(repo, key, selected, **unit_options)
    for stage in (None, *STAGES):
        item_id = key if stage is None else f"{key}.{stage}"
        path = repo / ".archon-horizon/roadmap/items" / f"{item_id}.yaml"
        if path.exists():
            continue
        args = [
            "roadmap",
            "add",
            "--id",
            item_id,
            "--title",
            item_id,
            "--project",
            "HomAlg",
            "--owner",
            login,
            "--milestone",
            key,
            "--author",
            "homalg",
        ]
        if stage:
            args.extend(("--parent", key))
        horizon(repo, *args)
        saved = parse_metadata(path.read_text())
        saved.setdefault("metadata", {})["homalg"] = {
            "doc": key,
            "stage": stage,
            "chapter": None,
            "attempts": 0,
        }
        atomic_write(path, dump_metadata(saved))
    current_tasks = tasks(repo, key)
    existing = {record["id"] for record in current_tasks}
    inherited = settlement.inheritance(current_tasks)
    created = []
    finished = {item["id"] for item in current_tasks if item.get("status") in {"done", "cancelled"}}
    for record in proposals:
        if proofs == "deferred" and record["metadata"]["homalg"]["stage"] == "PROOF":
            continue
        phase = record["metadata"]["homalg"].get("phase")
        if phase in {"author", "review"} and record["id"] in finished and "status" not in record:
            # The same nodes again after a replan, a failed review or a stale delivery:
            # a new unit, never a reopened finished one.
            base, number = record["id"], 2
            while f"{base}_r{number}" in existing:
                number += 1
            record = {**record, "id": f"{base}_r{number}"}
        if record["id"] not in existing:
            sources = [
                inherited[identifier]
                for identifier in record.get("node_ids", [])
                if identifier in inherited
            ]
            create_task(
                repo,
                record,
                login=login,
                document=document,
                guidance=settlement.guidance_text(sources),
                inbox_refs=[ref for source in sources for ref in source.get("inbox_refs", [])],
            )
            existing.add(record["id"])
            created.append(record["id"])
    if unit_options or prior.get("statement_frontier") or prior.get("statement_nodes"):
        reconcile_frontier_holds(
            repo,
            key,
            selected,
            bool(unit_options),
            statement_nodes,
            batch_size=statement_batch_size,
        )
    pending = (
        first_complete
        and not early_review_valid(document.get("early_review"), repo)
        and not any(entry["status"] == "draft" for entry in document["foundations"])
    )
    needs_foundation = early_review_valid(document.get("early_review"), repo) and any(
        not foundation_confirmed(entry, repo) for entry in document["foundations"]
    )
    request = "foundations" if needs_foundation else "early-review" if pending else None
    if request and prior.get("requested") != request:
        horizon(
            repo,
            "inbox",
            "add",
            "--kind",
            "conversation",
            "--to",
            "horizon" if agent_reviews_allowed(repo) else "human",
            "--author",
            "homalg",
            "--body",
            f"{key}: {request} required\n\nReview first-chapter definitions in /blueprint/HomAlg "
            f"and foundations in literature/{key}/document.yaml. "
            + (
                "Use an independent agent session and retain the author-session provenance."
                if agent_reviews_allowed(repo)
                else "Stop/wait for the run before confirming."
            ),
        )
    state = {
        "doc_key": key,
        "chapters": selected_ids,
        "no_claim": no_claim,
        "proofs": proofs,
        "statement_frontier": statement_frontier,
        "statement_nodes": list(statement_nodes),
        "statement_batch_size": statement_batch_size,
        "early_review": "accepted"
        if early_review_valid(document.get("early_review"), repo)
        else "pending"
        if pending
        else "waiting",
        "requested": request,
    }
    atomic_write(overlay, json_text(state))
    return {**state, "created_tasks": created}


def disputed_exclusive(frontier: StatementFrontier, info: dict[str, Any]) -> str | None:
    """Run a unit alone in the canonical workspace while one of its nodes is disputed.

    Dispute adjudication, typed errata and owner-decision replay are guarded native
    operations bound to the canonical workspace; concurrent lanes run every other
    unit in isolated session checkouts. Only units with an open dispute are marked.
    """
    if info.get("granularity") != "node":
        return None
    disputed = sorted(
        identifier
        for identifier in info.get("node_ids", [])
        if identifier in frontier.headers
        and frontier.headers[identifier].metadata.get("dispute", {}).get("status") == "open"
    )
    if not disputed:
        return None
    return "open dispute on " + ", ".join(disputed) + "; adjudication needs the canonical workspace"


def reconcile_frontier_holds(
    repo: Path,
    key: str,
    chapters: list[dict[str, Any]],
    enabled: bool,
    explicit: tuple[str, ...] = (),
    *,
    batch_size: int = 4,
) -> None:
    """Update only our dispatch holds, retaining task scope/status and human holds."""
    facts = PlanningFacts(repo)
    frontier = (
        StatementFrontier(
            repo, key, state_loader=lambda root, doc: facts.state(doc, document_state)
        )
        if enabled
        else None
    )
    units = (
        {
            record["id"]: record
            for record in statement_units(
                repo, key, chapters, explicit, frontier=frontier, batch_size=batch_size
            )
        }
        if enabled
        else {}
    )
    updates = []
    for record in tasks(repo, key):
        if record.get("status") in {"done", "cancelled", "running"}:
            continue
        metadata = record.get("metadata", {})
        info = metadata.get("homalg", {})
        if info.get("stage") != "STMT":
            continue
        if metadata.get("dispatch_hold") and not info.get("frontier_dispatch_hold"):
            continue
        reason = None
        if info.get("granularity") == "node" and info.get("phase") == "review":
            # Review units come from deliveries, not from the authoring frontier.
            failures = unit_blockers(repo, record, frontier=frontier) if enabled else []
            if not enabled:
                reason = "Statement unit is outside the enabled frontier"
            elif failures:
                reason = "; ".join(failures)
        elif info.get("granularity") == "node":
            candidate = units.get(record["id"])
            if not enabled or candidate is None:
                reason = "Statement unit is outside the enabled frontier"
            else:
                # The ordinary scope contract permits newly authored descendants;
                # their appearance must not rewrite the registered parent scope.
                failures = unit_blockers(repo, record, frontier=frontier)
                if failures:
                    reason = "; ".join(failures)
        elif enabled:
            try:
                complete = evaluate(
                    repo, record, refresh_exports=False, persist_transcription=False, facts=facts
                )["complete"]
            except (OSError, ValueError):
                complete = False
            if not complete:
                reason = "Statement units own authoring; chapter task awaits aggregate acceptance"
        if reason:
            metadata["dispatch_hold"] = reason
            info["frontier_dispatch_hold"] = True
        else:
            metadata.pop("dispatch_hold", None)
            info.pop("frontier_dispatch_hold", None)
        exclusive = disputed_exclusive(frontier, info) if frontier is not None else None
        if exclusive:
            metadata["exclusive"] = exclusive
            info["frontier_exclusive"] = True
        elif info.pop("frontier_exclusive", None):
            metadata.pop("exclusive", None)
        path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
        updates.append((path, dump_metadata(record)))
    facts.assert_current()
    for path, text in updates:
        atomic_write(path, text)
