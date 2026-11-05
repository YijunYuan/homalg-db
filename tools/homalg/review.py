"""Statement-lock review evidence, source hashes and reopening diagnostics."""

import copy
import hashlib
import json
import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from homalg.headers import code_only, parse_header
from homalg.human import check_human_session, record_human_change, require_human, require_idle
from homalg.io import atomic_bytes, atomic_write, atomic_write_with_receipt, json_text
from homalg.leantext import commands, statement_hashes
from homalg.nodeio import header_mapping, node_path, replace_header
from homalg.review_policy import (
    agent_review_record,
    agent_reviews_allowed,
    require_report_provenance,
    valid_agent_review,
)
from homalg.schemas import SchemaStore, load_yaml

REVIEW_STATUSES = {"satisfactory", "partial", "mismatch", "unverified", "needs-adjudication"}


def authoring_source_fingerprint(text: str) -> str:
    """Hash all source except a well-formed agent fidelity.reviewed envelope.

    Human/legacy/malformed records remain part of the fingerprint. Every other
    metadata value, header prose (including notes/proofs) and Lean byte is retained.
    YAML serialization is canonicalized so tool-managed header formatting is harmless.
    """
    from homalg.documents import dump_metadata

    header = parse_header(text)
    metadata = header_mapping(text, header)
    reviewed = metadata.get("fidelity", {}).get("reviewed")
    hashes = reviewed.get("decl_hashes") if isinstance(reviewed, dict) else None
    valid_hashes = isinstance(hashes, dict) and all(
        isinstance(item, dict)
        and set(item) == {"statement_sha256", "type_hash", "meaning_hash"}
        and all(
            isinstance(item[key], str) and re.fullmatch(pattern, item[key])
            for key, pattern in (
                ("statement_sha256", r"[0-9a-f]{64}"),
                ("type_hash", r"[0-9a-f]{16}"),
                ("meaning_hash", r"[0-9a-f]{16}"),
            )
        )
        for item in hashes.values()
    )
    if valid_agent_review(reviewed) and valid_hashes:
        metadata["fidelity"].pop("reviewed")
    opening = text.index("```yaml node", header.start) + len("```yaml node")
    closing = text.index("```", opening)
    normalized = text[:opening] + "\n" + dump_metadata(metadata).rstrip() + "\n" + text[closing:]
    return hashlib.sha256(normalized.encode()).hexdigest()


class _AuthoringContextReads:
    """Parsed reads for one guarded batch capture, never retained across captures."""

    def __init__(self):
        self.nodes: dict[Path, tuple[str, dict[str, Any]]] = {}
        self.yaml: dict[Path, Any] = {}

    def node(self, path: Path) -> tuple[str, dict[str, Any]]:
        if path not in self.nodes:
            source = path.read_text()
            self.nodes[path] = source, parse_header(source).metadata
        return self.nodes[path]

    def document(self, path: Path) -> Any:
        if path not in self.yaml:
            self.yaml[path] = load_yaml(path.read_text())
        return self.yaml[path]


TOOLCHAIN_FILES = (
    "lean-toolchain",
    "lakefile.toml",
    "lake-manifest.json",
    "horizon/review-policy.yaml",
)


def _portable_name(repo: Path, path: Path) -> str:
    """Name evidence relative to its workspace so it survives an isolated checkout."""
    private = (repo / "literature/.private").resolve()
    for base, prefix in ((private, "literature/.private/"), (repo, "")):
        try:
            return prefix + path.resolve().relative_to(base).as_posix()
        except ValueError:
            continue
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path.resolve())


def _scoped_compilation(repo: Path, closure: list[str]) -> dict[str, Any]:
    """Exactly what a statement's compilation depends on inside this repository.

    The node files of its import/dependency closure plus the pinned toolchain and
    package manifest. Other nodes, tooling and generated roots do not affect it.
    """
    files: dict[str, Any] = {}
    for node_id in closure:
        path = node_path(repo, node_id)
        name = path.relative_to(repo).as_posix() if path.is_relative_to(repo) else str(path)
        files[name] = authoring_source_fingerprint(path.read_text()) if path.is_file() else None
    for name in TOOLCHAIN_FILES:
        path = repo / name
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return {"files": files}


def authoring_context_inputs(
    repo: Path,
    node_ids: list[str] | tuple[str, ...] | None = None,
    *,
    _reads: _AuthoringContextReads | None = None,
) -> dict[str, Any]:
    """Bind validation and source context without copying private source text.

    Source pages use printed page + PDF offset. With node ids, follow authored
    dependencies and local imports; without them, conservatively include all nodes.
    PDF/PNG bodies are not hashed: their registered document identity remains the
    boundary. TeX pages and transcription evidence are bound to actual local bytes.
    """
    from homalg.leanexport import file_fingerprint

    repo = repo.resolve()
    pending = (
        list(node_ids)
        if node_ids is not None
        else [f"{path.parent.name}.{path.stem}" for path in (repo / "HomAlg").glob("*/*.lean")]
    )
    seen = set()
    decision_paths = set()
    pages: dict[str, set[int]] = {}
    while pending:
        node_id = pending.pop()
        if node_id in seen:
            continue
        seen.add(node_id)
        path = node_path(repo, node_id)
        if _reads is None:
            source = path.read_text()
            header = parse_header(source).metadata
        else:
            source, header = _reads.node(path)
        resolution = header.get("dispute", {}).get("resolution", {})
        if resolution.get("kind") == "owner-decision-replay":
            from homalg.owner_decisions import POLICY

            decision_paths.update({repo / POLICY, repo / resolution["receipt"]})
        key = header["doc"]
        path = repo / "literature" / key / "document.yaml"
        document = load_yaml(path.read_text()) if _reads is None else _reads.document(path)
        offset = document.get("pdf", {}).get("page_offset", 0)
        pages.setdefault(key, set()).update(page + offset for page in header["source"]["pages"])
        pending.extend(header["deps"]["statement"] + header["deps"]["proof"])
        # Lean permits multiple modules on one import line. Do not lose source
        # context for modules after the first token; comments/literals are masked.
        pending.extend(
            name.removeprefix("HomAlg.")
            for line in re.findall(r"(?m)^\s*(?:public\s+)?import[ \t]+([^\n]*)", code_only(source))
            for name in re.findall(r"\bHomAlg\.\w+\.\w+\b", line)
        )
    paths = decision_paths
    # Append-only taxonomy cannot invalidate an authored statement; schemas can.
    for suffix in ("*.yaml", "*.yml", "*.json"):
        paths.update((repo / "schema").rglob(suffix))
    selections = {}
    for key, selected in pages.items():
        # Foundations, PDF identity and early review; written only by guarded commands.
        paths.add(repo / "literature" / key / "document.yaml")
        inventory = repo / "literature" / key / "inventory.yaml"
        paths.add(inventory)
        # Only the node's own pages: inventorying other chapters is unrelated work.
        selections[str(inventory)] = sorted(selected)
        paths.add(repo / "docs/fixtures" / f"{key}.md")
    private = (repo / "literature/.private").resolve()
    for key, selected in pages.items():
        directory = private / key
        if not directory.resolve().is_relative_to(private):
            raise ValueError("Private source directory escapes its checkout")
        manifest = directory / "transcription.yaml"
        source_paths = {manifest, *(directory / "tex" / f"page-{page:04}.tex" for page in selected)}
        if any(not path.resolve().is_relative_to(directory.resolve()) for path in source_paths):
            raise ValueError("Private transcription path escapes its document")
        paths.update(source_paths)
        selections[str(manifest)] = sorted(selected)
    files = {}
    for path in sorted(paths):
        name = _portable_name(repo, path)
        if not path.exists():
            files[name] = None
            continue
        fingerprint = file_fingerprint(path)
        if str(path) in selections:
            data = (load_yaml(path.read_text()) if _reads is None else _reads.document(path)) or {}
            projection = {key: value for key, value in data.items() if key != "pages"}
            projection["pages"] = {
                f"{number:04}": data.get("pages", {}).get(f"{number:04}")
                for number in selections[str(path)]
            }
            fingerprint["selected_sha256"] = hashlib.sha256(
                json_text(projection).encode()
            ).hexdigest()
            if file_fingerprint(path) != {
                k: v for k, v in fingerprint.items() if k != "selected_sha256"
            }:
                raise ValueError("Transcription evidence changed while freezing inputs")
        files[name] = fingerprint
    return {
        "node_ids": sorted(seen),
        "source_pages": {k: sorted(v) for k, v in sorted(pages.items())},
        "files": files,
    }


def _authoring_snapshot(
    repo: Path, context: dict[str, Any], compilation: dict[str, Any] | None = None
) -> dict[str, Any]:
    from homalg.repository import canonical_root

    return {
        "schema_version": 2,
        "kind": "authoring-input-snapshot",
        "workspace": canonical_root(repo),
        "compilation": compilation or _scoped_compilation(repo, context["node_ids"]),
        "context": context
        | {
            "files": {
                name: value.get("selected_sha256", value["sha256"]) if value else None
                for name, value in context["files"].items()
            }
        },
    }


def freeze_authoring_inputs(
    repo: Path,
    node_ids: list[str] | tuple[str, ...] | None = None,
    *,
    _reads: _AuthoringContextReads | None = None,
) -> dict[str, Any]:
    """Stable delivery fingerprint, scoped source context, no independent review reports.

    Only valid agent locks are excluded. The snapshot covers the nodes' import and
    dependency closure, the toolchain, and the selected pages of the inventory and
    transcription, named relative to the workspace. Unrelated nodes, chapters and
    checkouts therefore do not invalidate a delivery; any change it depends on does.
    """
    from homalg.leanexport import workspace_lock

    repo = repo.resolve()
    if _reads is not None:
        # Read-only comparison inside one planning sweep, whose own input guard
        # rejects concurrent edits; parsed sources are shared across deliveries.
        context = authoring_context_inputs(repo, node_ids, _reads=_reads)
        return _authoring_snapshot(repo, context)
    with workspace_lock(repo):
        context = authoring_context_inputs(repo, node_ids)
        compilation = _scoped_compilation(repo, context["node_ids"])
        # A writer must not change the inputs while the normalized snapshot is read;
        # the raw context also binds file identity, so even a restored edit counts.
        if (
            authoring_context_inputs(repo, node_ids) != context
            or _scoped_compilation(repo, context["node_ids"]) != compilation
        ):
            raise ValueError("Authoring inputs changed while freezing the delivery")
        return _authoring_snapshot(repo, context, compilation)


def freeze_authoring_batch_inputs(
    repo: Path, groups: list[list[str] | tuple[str, ...]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Capture exact author snapshots together, sharing only operation-local reads.

    Each group keeps its own dependency/source-page projection. Union-context reads
    guard the whole capture; no parsed object or fingerprint survives this call.
    The caller still rechecks the union after its scope checks.
    """
    from homalg.leanexport import workspace_lock

    if not groups or any(not group for group in groups):
        raise ValueError("An author batch requires nonempty node groups")
    repo = repo.resolve()
    union = sorted({node_id for group in groups for node_id in group})
    with workspace_lock(repo):
        reads = _AuthoringContextReads()
        context = authoring_context_inputs(repo, union, _reads=reads)
        compilation = _scoped_compilation(repo, context["node_ids"])
        contexts = [authoring_context_inputs(repo, group, _reads=reads) for group in groups]
        if (
            authoring_context_inputs(repo, union, _reads=_AuthoringContextReads()) != context
            or _scoped_compilation(repo, context["node_ids"]) != compilation
        ):
            raise ValueError("Authoring inputs changed while freezing the delivery")
        files = compilation["files"]
        snapshots = []
        for selected in contexts:
            owned = {
                f"HomAlg/{node_id.replace('.', '/', 1)}.lean" for node_id in selected["node_ids"]
            }
            subset = {
                name: value
                for name, value in files.items()
                if name in owned or name in TOOLCHAIN_FILES
            }
            snapshots.append(_authoring_snapshot(repo, selected, {"files": subset}))
        union_snapshot = _authoring_snapshot(repo, context, compilation)
        # Deliveries are independent objects even where their immutable values agree.
        return [copy.deepcopy(item) for item in snapshots], copy.deepcopy(union_snapshot)


def review_blocks(text: str) -> dict[str, dict[str, str]]:
    """Read each kind's latest verdict; earlier reviews cannot mask a later failure."""
    headings = list(re.finditer(r"(?m)^##\s+(source-fidelity|honesty)\s+[—–-]\s+(.+)$", text))
    output = {}
    for position, heading in enumerate(headings):
        end = headings[position + 1].start() if position + 1 < len(headings) else len(text)
        body = text[heading.end() : end]
        status = re.search(r"(?m)^Status:\s*(\S+)\s*$", body)
        verdict = re.search(r"(?m)^Verdict:\s*(.+)$", body)
        output[heading.group(1)] = {
            "status": status.group(1)
            if status and status.group(1) in REVIEW_STATUSES
            else "unverified",
            "verdict": verdict.group(1) if verdict else "",
            "heading": heading.group(2),
            "body": body,
        }
    return output


def current_declarations(repo: Path, node_id: str) -> dict[str, dict[str, Any]]:
    """Read exported declaration facts; callers must check source freshness."""
    key = node_id.split(".", 1)[0]
    path = repo / "literature" / key / "nodes.json"
    nodes = json.loads(path.read_text())["nodes"]
    node = next((node for node in nodes if node["id"] == node_id), None)
    if node is None or node["derived"] is None:
        raise ValueError(f"{node_id}: export Lean before reviewing fidelity")
    return {declaration["name"]: declaration for declaration in node["derived"]["decl_info"]}


def lock_changes(
    text: str, authored: dict[str, Any], declarations: dict[str, dict[str, Any]]
) -> list[dict[str, str]]:
    """Detect statement/type changes as errors and semantic closure changes as warnings."""
    reviewed = authored.get("fidelity", {}).get("reviewed")
    if not reviewed:
        return []
    current = statement_hashes(text)
    locked = reviewed["decl_hashes"]
    changes = []
    names = set(authored["decls"]) | set(locked)
    for name in sorted(names):
        saved, declaration = locked.get(name, {}), declarations.get(name, {})
        if (
            name not in authored["decls"]
            or current.get(name) != saved.get("statement_sha256")
            or declaration.get("type_hash") != saved.get("type_hash")
        ):
            changes.append(
                {"decl": name, "severity": "error", "reason": "Statement or type changed"}
            )
        elif declaration.get("meaning_hash") != saved.get("meaning_hash"):
            changes.append(
                {"decl": name, "severity": "warning", "reason": "A referenced definition changed"}
            )
    return changes


def _prepare_review(
    repo: Path,
    node_id: str,
    *,
    by: str,
    session: str | None,
    author_session: str | None,
    human: bool,
    now: datetime | None,
) -> dict[str, Any]:
    """Validate one complete report and provenance without writing any lock."""
    path = node_path(repo, node_id)
    source = path.read_text()
    header = parse_header(source)
    authored = header.metadata
    if not authored["decls"]:
        raise ValueError("A planned/informal node has no statements to lock")
    reviewed = authored["fidelity"].get("reviewed")
    if not human and reviewed and reviewed.get("kind") != "agent":
        raise ValueError("An agent review cannot replace an existing human fidelity record")
    if not human and authored.get("dispute", {}).get("status") == "open":
        raise ValueError(
            "An unresolved mathematical/source dispute requires adjudication before locking"
        )
    from homalg.owner_decisions import validate_resolution

    validate_resolution(repo, source)
    from homalg.agent_errata import validate_resolution as validate_agent_erratum

    validate_agent_erratum(repo, source)
    independent = not human and agent_reviews_allowed(repo)
    agent_record = None
    if independent:
        agent_record = agent_review_record(
            repo,
            by=by,
            session=session or "",
            author_session=author_session or "",
            now=now,
        )
        if authored["fidelity"]["status"] == "deviates" and any(
            not item.get("what", "").strip() or not item.get("why", "").strip()
            for item in authored["fidelity"].get("deviations", [])
        ):
            raise ValueError("Agent review requires every deviation to be explicitly explained")
    elif authored["fidelity"]["status"] in {"foundation", "deviates"} and not human:
        raise ValueError(
            "Foundation and deviating statements require a human review or enabled policy"
        )
    key, local = node_id.split(".", 1)
    reviews = repo / "literature" / key / "reviews" / f"{local}.md"
    report_text = reviews.read_text()
    if independent:
        require_report_provenance(
            report_text,
            session=session or "",
            author_session=author_session or "",
        )
    blocks = review_blocks(report_text)
    required = ["source-fidelity"]
    if "honesty" in blocks or any(
        command.kind in {"structure", "class", "instance"} for command in commands(source)
    ):
        required.append("honesty")
    for kind in required:
        block = blocks.get(kind, {})
        if block.get("status") != "satisfactory" or not block.get("verdict"):
            raise ValueError(f"Latest {kind} review must have Status: satisfactory and a Verdict")
        if not re.search(r"(?m)^\|.*\|", block["body"]):
            raise ValueError(f"Latest {kind} review must include its comparison table")
    if authored["id"] != node_id:
        raise ValueError(f"Node identity does not match its path: {node_id}")
    return {
        "id": node_id,
        "path": path,
        "source": source,
        "header": header,
        "authored": authored,
        "report_path": reviews,
        "report": report_text,
        "agent_record": agent_record,
    }


def _batch_ids(node_ids: list[str] | tuple[str, ...]) -> list[str]:
    ids = list(node_ids)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("A review batch requires nonempty, unique node ids")
    if any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*\.[A-Za-z][A-Za-z0-9_]*", item) for item in ids):
        raise ValueError("Invalid node id in review batch")
    if len({item.split(".", 1)[0] for item in ids}) != 1:
        raise ValueError("A review batch must belong to one document")
    return ids


def freeze_fidelity_inputs(
    repo: Path, node_ids: list[str] | tuple[str, ...], *, expected_author_session: str | None = None
) -> dict[str, Any]:
    """Capture review/build inputs, not an approval or reusable compiled export.

    A supplied snapshot must match exactly at registration; even a touched or
    replaced input is stale. No node lock is written by this function.
    """
    from homalg.leanexport import compilation_inputs, file_fingerprint, workspace_lock

    repo = repo.resolve()
    ids = _batch_ids(node_ids)
    if expected_author_session is not None and (
        not isinstance(expected_author_session, str) or not expected_author_session.strip()
    ):
        raise ValueError("An expected author session must be a nonempty actual session")
    with workspace_lock(repo):
        reports = {}
        for node_id in ids:
            node_path(repo, node_id).read_bytes()
            key, local = node_id.split(".", 1)
            path = repo / "literature" / key / "reviews" / f"{local}.md"
            reports[str(path)] = file_fingerprint(path)
        frozen = {
            "schema_version": 1,
            "kind": "fidelity-input-snapshot",
            "repo": str(repo),
            "node_ids": ids,
            "compilation": compilation_inputs(repo),
            "context": authoring_context_inputs(repo, ids),
            "reports": reports,
        }
        if expected_author_session is not None:
            frozen["expected_author_session"] = expected_author_session.strip()
        return frozen


def _assert_snapshot(repo: Path, ids: list[str], expected: dict[str, Any]) -> None:
    if (
        freeze_fidelity_inputs(
            repo, ids, expected_author_session=expected.get("expected_author_session")
        )
        != expected
    ):
        raise ValueError("Review inputs changed or snapshot is stale; review the current inputs")


def _transaction_directory(repo: Path) -> Path:
    return repo / ".archon-horizon/cache/fidelity-transactions"


def _require_finished_transactions(repo: Path) -> None:
    for path in _transaction_directory(repo).glob("*.json"):
        status = json.loads(path.read_text()).get("status")
        if status not in {"committed", "rolled-back"}:
            raise ValueError(f"Unfinished fidelity transaction requires recovery: {path}")


def _write_batch(
    repo: Path,
    ids: list[str],
    snapshot: dict[str, Any],
    updates: list[dict[str, Any]],
    exported_files: dict[str, Any],
    *,
    extra_guard: Callable[[], None] | None = None,
    evidence: dict[str, Any] | None = None,
) -> None:
    """Journal first, then register under the workspace lock; roll back failures.

    The journal makes interruption/partial recovery explicit. Uncooperative edits
    are never overwritten during rollback. Such a conflict blocks later batches
    until the recorded transaction has been inspected and recovered.
    """
    from homalg.leanexport import assert_workspace_lock, file_fingerprint

    def verify(expected: dict[str, Any]) -> None:
        assert_workspace_lock(repo)
        if extra_guard is not None:
            extra_guard()
        _assert_snapshot(repo, ids, expected)
        if any(file_fingerprint(Path(name)) != value for name, value in exported_files.items()):
            raise ValueError("Compiled export changed during review registration")
        if extra_guard is not None:
            extra_guard()

    verify(snapshot)
    journal_path = _transaction_directory(repo) / f"{uuid.uuid4().hex}.json"
    journal = {
        "schema_version": 1,
        "status": "prepared",
        "node_ids": ids,
        "snapshot": snapshot,
        "updates": updates,
    }
    if evidence is not None:
        journal["evidence"] = copy.deepcopy(evidence)
    atomic_write(journal_path, json_text(journal))
    expected = copy.deepcopy(snapshot)
    attempted = []
    try:
        verify(expected)
        for update in updates:
            assert_workspace_lock(repo)
            path = Path(update["path"])
            before_fingerprint = file_fingerprint(path)
            if before_fingerprint != expected["compilation"]["files"][str(path)]:
                raise ValueError(f"Node changed before registration: {path}")
            update["before_fingerprint"] = before_fingerprint
            attempted.append(update)
            fingerprint = atomic_write_with_receipt(path, update["after"])
            update["written_fingerprint"] = fingerprint
            if file_fingerprint(path) != fingerprint:
                raise ValueError(f"Node changed during registration: {path}")
            expected["compilation"]["files"][str(path)] = fingerprint
            atomic_write(journal_path, json_text(journal))
        verify(expected)
        journal["status"] = "committed"
        atomic_write(journal_path, json_text(journal))
    except BaseException as error:
        conflicts = []
        for update in reversed(attempted):
            path = Path(update["path"])
            try:
                current = file_fingerprint(path)
                if current == update.get("written_fingerprint"):
                    atomic_bytes(path, update["before"].encode())
                elif current != update["before_fingerprint"]:
                    conflicts.append(str(path))
            except BaseException as recovery_error:
                conflicts.append(f"{path}: {recovery_error}")
        journal.update(
            status="recovery-required" if conflicts else "rolled-back",
            failure=str(error),
            recovery_conflicts=conflicts,
        )
        atomic_write(journal_path, json_text(journal))
        raise ValueError(
            f"Fidelity batch failed; {journal['status']}; journal: {journal_path}"
        ) from error


def _review_lock(
    item: dict[str, Any],
    exported_declarations: dict[str, Any],
    *,
    by: str,
    session: str | None,
    human: bool,
    note: str,
    now: datetime | None,
) -> dict[str, Any]:
    """Construct the ordinary per-node lock only after caller-owned review gates."""
    declarations = exported_declarations.get(f"HomAlg.{item['id']}", {})
    hashes = statement_hashes(item["source"])
    names = item["authored"]["decls"]
    if any(name not in hashes or name not in declarations for name in names):
        raise ValueError("A main declaration is missing from the source analysis or Lean export")
    lock = {
        "by": by,
        "kind": "human" if human else "agent",
        "status": "satisfactory",
        "on": (now or datetime.now(UTC)).date().isoformat(),
        "decl_hashes": {
            name: {
                "statement_sha256": hashes[name],
                "type_hash": declarations[name]["type_hash"],
                "meaning_hash": declarations[name]["meaning_hash"],
            }
            for name in names
        },
    }
    if session:
        lock["session"] = session
    if item["agent_record"]:
        lock["author_session"] = item["agent_record"]["author_session"]
    if note:
        lock["note"] = note
    return lock


def _review_many(
    repo: Path,
    node_ids: list[str] | tuple[str, ...],
    *,
    by: str,
    session: str | None,
    author_session: str | None,
    human: bool,
    note: str,
    now: datetime | None,
    snapshot: dict[str, Any] | None,
    independent_required: bool = False,
) -> dict[str, dict[str, Any]]:
    from homalg.leanexport import (
        compilation_inputs,
        declaration_map,
        export_lean,
        file_fingerprint,
        workspace_lock,
    )

    repo = repo.resolve()
    ids = _batch_ids(node_ids)
    if bool(session) == human:
        raise ValueError("Choose exactly one of --session or --human")
    if snapshot is not None and not isinstance(snapshot, dict):
        raise ValueError("A fidelity snapshot must be a JSON object")
    if human:
        check_human_session(f"review-fidelity {ids[0]}", repo)
    with workspace_lock(repo):
        _require_finished_transactions(repo)
        login_schema = SchemaStore(repo / "schema").schemas["common.schema.json"]["$defs"]["Login"]
        if not Draft202012Validator(login_schema).is_valid(by):
            raise ValueError(
                "--by must be a valid short reviewer identifier; put the full identity in --session"
            )
        initial_inputs = compilation_inputs(repo)
        if independent_required:
            agent_review_record(
                repo, by=by, session=session or "", author_session=author_session or "", now=now
            )
        # All node/report checks run before the first export or header write.
        prepared = [
            _prepare_review(
                repo,
                node_id,
                by=by,
                session=session,
                author_session=author_session,
                human=human,
                now=now,
            )
            for node_id in ids
        ]
        expected_author = snapshot.get("expected_author_session") if snapshot is not None else None
        if expected_author is not None and expected_author != (author_session or "").strip():
            raise ValueError("Batch author session differs from the frozen author delivery")
        frozen = freeze_fidelity_inputs(repo, ids, expected_author_session=expected_author)
        if frozen["compilation"] != initial_inputs:
            raise ValueError("Review inputs changed during preflight")
        if snapshot is not None and snapshot != frozen:
            raise ValueError(
                "Review inputs changed or snapshot is stale; review the current inputs"
            )
        # Catch edits between reading the reports/source and freezing them.
        if any(
            item["path"].read_text() != item["source"]
            or item["report_path"].read_text() != item["report"]
            for item in prepared
        ):
            raise ValueError("The node or report changed during review")
        key = ids[0].split(".", 1)[0]
        # Scoped to the batch: the lock records only these declarations' hashes. The
        # outer hook refreshes the canonical export and nodes.json afterwards.
        raw = export_lean(
            repo,
            doc=key,
            out=repo / "build/registration-export.json",
            merge=False,
            modules=[f"HomAlg.{node_id}" for node_id in ids],
        )
        exported_declarations = declaration_map(raw)
        _assert_snapshot(repo, ids, frozen)
        export_path = repo / "literature" / key / "nodes.json"
        exported_files = {str(export_path): file_fingerprint(export_path)}
        schemas = SchemaStore(repo / "schema")
        locks = {}
        updates = []
        for item in prepared:
            lock = _review_lock(
                item, exported_declarations, by=by, session=session, human=human, note=note, now=now
            )
            if human:
                require_human(
                    f"review-fidelity {item['id']}",
                    repo,
                    details=json.dumps(
                        {"statement": item["header"].sections["Statement"], "lock": lock}, indent=2
                    ),
                )
            metadata = header_mapping(item["source"], item["header"])
            metadata["fidelity"]["reviewed"] = lock
            updates.append(
                {
                    "path": str(item["path"]),
                    "before": item["source"],
                    "after": replace_header(item["source"], metadata, schemas),
                }
            )
            locks[item["id"]] = lock
        _write_batch(repo, ids, frozen, updates, exported_files)
        if human:
            record_human_change(repo, f"review-fidelity {ids[0]}", [prepared[0]["path"]])
        return locks


def review_fidelity_batch(
    repo: Path,
    node_ids: list[str] | tuple[str, ...],
    *,
    by: str,
    session: str,
    author_session: str,
    note: str = "",
    now: datetime | None = None,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Register one genuine independent agent's reviews with exactly one fresh export.

    All nodes must share a document and reviewer/author provenance. This API does
    not create review reports or human evidence and never reuses a previous export.
    """
    agent_review_record(repo, by=by, session=session, author_session=author_session, now=now)
    return _review_many(
        repo,
        node_ids,
        by=by,
        session=session,
        author_session=author_session,
        human=False,
        note=note,
        now=now,
        snapshot=snapshot,
        independent_required=True,
    )


def review_fidelity(
    repo: Path,
    node_id: str,
    *,
    by: str,
    session: str | None = None,
    author_session: str | None = None,
    human: bool = False,
    note: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Compatible single-node API, with the build lock held through registration."""
    return _review_many(
        repo,
        [node_id],
        by=by,
        session=session,
        author_session=author_session,
        human=human,
        note=note,
        now=now,
        snapshot=None,
    )[node_id]


def relock_all(repo: Path, *, reason: str) -> dict[str, list[str]]:
    """Refresh toolchain-sensitive hashes only for interfaces whose source locks still match."""
    if not reason.strip():
        raise ValueError("Relocking requires a reason")
    require_idle(repo)
    from homalg.leanexport import export_lean
    from homalg.repository import documents, node_paths

    export_lean(repo)
    schemas = SchemaStore(repo / "schema")
    updates = {}
    result: dict[str, list[str]] = {"updated": [], "changed_statements": []}
    for path in node_paths(repo, documents(repo)):
        source = path.read_text()
        metadata = header_mapping(source)
        reviewed = metadata["fidelity"].get("reviewed")
        if not reviewed:
            continue
        hashes = statement_hashes(source)
        if set(reviewed["decl_hashes"]) != set(metadata["decls"]) or any(
            hashes.get(name) != lock["statement_sha256"]
            for name, lock in reviewed["decl_hashes"].items()
        ):
            result["changed_statements"].append(metadata["id"])
            continue
        declarations = current_declarations(repo, metadata["id"])
        for name, lock in reviewed["decl_hashes"].items():
            if name not in declarations:
                raise ValueError(f"Missing declaration while relocking: {name}")
            lock["type_hash"] = declarations[name]["type_hash"]
            lock["meaning_hash"] = declarations[name]["meaning_hash"]
        updates[path] = replace_header(source, metadata, schemas)
        result["updated"].append(metadata["id"])
    for path, source in updates.items():
        atomic_write(path, source)
        key, local = path.parent.name, path.stem
        review_path = repo / "literature" / key / "reviews" / f"{local}.md"
        previous = review_path.read_text() if review_path.exists() else ""
        atomic_write(
            review_path, previous.rstrip() + f"\n\nRelocked {datetime.now(UTC).date()}: {reason}\n"
        )
    return result


def unlock_fidelity(repo: Path, node_id: str, *, by: str, reason: str) -> None:
    """Remove an obsolete lock while preserving an append-only review trail."""
    if not reason.strip():
        raise ValueError("Unlocking requires a reason")
    path = node_path(repo, node_id)
    text = path.read_text()
    metadata = header_mapping(text)
    metadata["fidelity"].pop("reviewed", None)
    updated = replace_header(text, metadata, SchemaStore(repo / "schema"))
    doc, local = node_id.split(".", 1)
    review_path = repo / "literature" / doc / "reviews" / f"{local}.md"
    previous = review_path.read_text() if review_path.exists() else ""
    atomic_write(
        review_path,
        previous.rstrip() + f"\n\nUnlocked {datetime.now(UTC).date()} by {by}: {reason}\n",
    )
    atomic_write(path, updated)
