"""Create only newly unlocked stage tasks with explicit, immutable file scopes."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg.blueprint import source_order
from homalg.claims import claim_view, load_status_history
from homalg.documents import dump_metadata, parse_metadata, read_document, write_metadata
from homalg.engine import horizon, settings, tasks
from homalg.headers import parse_header
from homalg.human import record_human_change, require_human
from homalg.io import atomic_write, json_text
from homalg.repository import node_paths
from homalg.review_policy import (
    agent_review_record,
    agent_reviews_allowed,
    early_review_valid,
    foundation_confirmed,
    valid_agent_review,
)
from homalg.schemas import SchemaStore, load_yaml
from homalg.stages import DEFINITION_KINDS, evaluate
from homalg.transcription import status as transcription_status

STAGES = ("T", "INV", "DAG", "CITED", "STMT", "PROOF")
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


def scope_nodes(
    repo: Path, key: str, chapter: str | None, kind_group: str | None = None
) -> list[dict[str, Any]]:
    """Select source items and their existing auxiliaries in document order."""
    nodes = [parse_header(path.read_text()).metadata for path in node_paths(repo, [key])]
    primary = [
        node
        for node in nodes
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
        repo,
        key,
        [
            node
            for node in nodes
            if node["id"] in selected or node.get("aux", {}).get("parent") in selected
        ],
    )


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
    nodes = scope_nodes(repo, key, chapter, kind_group)
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
    repo: Path, key: str, chapters: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Evaluate stage prerequisites from current evidence, preserving existing task statuses."""
    document = read_document(repo, key)
    synthetic = document["type"] == "synthetic"
    offset = document.get("pdf", {}).get("page_offset", 0)
    reviewed = {} if synthetic else transcription_status(repo, key)["pages"]
    proposals: list[dict[str, Any]] = []
    existing = {record["id"]: record for record in tasks(repo, key)}

    def complete(candidate: dict[str, Any]) -> bool:
        record = existing.get(candidate["id"])
        if record is None:
            return False
        try:
            return evaluate(repo, record, refresh_exports=False)["complete"]
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
                proposals.append(proposed_task(repo, key, "T", number, pages=chunk))
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
            candidate = proposed_task(
                repo,
                key,
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
        dag = proposed_task(repo, key, "DAG", number, chapter=chapter["chapter"])
        dag_candidates.append(dag)
        if all(complete(candidate) for candidate in inventory):
            proposals.append(dag)
        dag_ready[chapter["chapter"]] = complete(dag)
        definitions.append(
            proposed_task(
                repo, key, "STMT", number, chapter=chapter["chapter"], kind_group="definitions"
            )
        )
    cited = proposed_task(repo, key, "CITED", 1, kind_group="cited")
    if all(dag_ready.values()):
        proposals.append(cited)
    blocked_foundations = early_review_valid(document.get("early_review"), repo) and any(
        not foundation_confirmed(entry, repo) for entry in document["foundations"]
    )
    for chapter, definition in zip(chapters, definitions, strict=True):
        number = chapter_numbers[chapter["chapter"]]
        if dag_ready[chapter["chapter"]] and not blocked_foundations:
            proposals.append(definition)
        theorems = proposed_task(
            repo,
            key,
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
            proposals.append(proposed_task(repo, key, "PROOF", number, chapter=chapter["chapter"]))
    first_definitions = complete(
        proposed_task(
            repo,
            key,
            "STMT",
            1,
            chapter=document["structure"][0]["chapter"],
            kind_group="definitions",
        )
    )
    return proposals, first_definitions


def create_task(
    repo: Path, record: dict[str, Any], *, login: str, document: dict[str, Any]
) -> None:
    """Create through the engine CLI, then add only the documented HomAlg metadata."""
    info = record["metadata"]["homalg"]
    template = (repo / "horizon/tasks" / f"{TEMPLATES[info['stage']]}.md").read_text()
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
    }
    objective = template.format_map(fields)
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
    horizon(repo, *args)
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    saved = parse_metadata(path.read_text())
    saved.setdefault("metadata", {})["homalg"] = info
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
) -> dict[str, Any]:
    """Plan eligible work using explicit human or enabled independent-agent review evidence."""
    document = read_document(repo, key)
    overlay = repo / ".archon-horizon/overlay" / f"plan-{key}.json"
    prior = json.loads(overlay.read_text()) if overlay.exists() else {}
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
    proposals, first_complete = unlocked_tasks(repo, key, selected)
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
        proposals, first_complete = unlocked_tasks(repo, key, selected)
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
    existing = {record["id"] for record in tasks(repo, key)}
    created = []
    for record in proposals:
        if record["id"] not in existing:
            create_task(repo, record, login=login, document=document)
            created.append(record["id"])
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
        "early_review": "accepted"
        if early_review_valid(document.get("early_review"), repo)
        else "pending"
        if pending
        else "waiting",
        "requested": request,
    }
    atomic_write(overlay, json_text(state))
    return {**state, "created_tasks": created}
