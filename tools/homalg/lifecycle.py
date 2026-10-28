"""Session hooks, private rollback, backups and human-confirmed issue escalation."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg import engine, planning, publishing, scope, stages
from homalg.claims import claim_view, instant, load_status_history
from homalg.collaboration import Client, append_merge_records, main_claim, policy_for
from homalg.documents import dump_metadata, parse_metadata
from homalg.extract import extract_document
from homalg.human import check_human_session, record_human_change, require_idle
from homalg.io import atomic_bytes, atomic_write, json_text
from homalg.leanexport import export_lean
from homalg.nodeio import header_mapping, node_path, replace_header
from homalg.repository import documents
from homalg.roots import generate_roots
from homalg.runtime_state import document_state, overlay_nodes
from homalg.schemas import SchemaStore, load_yaml
from homalg.validate import validate_repo


class ScopeViolation(ValueError):
    """Only this exception is serialized to stdout by the session hook's exit-four protocol."""

    def __init__(self, paths: list[str]):
        self.paths = sorted(set(paths))
        super().__init__("Session wrote outside its declared scope")


def git(
    root: Path, *args: str, input: bytes | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Binary-safe Git plumbing for snapshots, with no shell or shared-index mutations."""
    result = subprocess.run(["git", *args], cwd=root, input=input, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    return result


def private_files(root: Path, *, store: bool = False) -> dict[str, dict]:
    """Record tracked/unignored private bytes, modes and symlinks without following links."""
    names = (
        git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
        .stdout.decode()
        .split("\0")
    )
    result = {}
    for name in sorted(set(names) - {""}):
        path = root / name
        if ".." in Path(name).parts or Path(name).is_absolute():
            raise ValueError("Unsafe private Git path")
        if not path.parent.resolve().is_relative_to(root.resolve()):
            # Capture the ancestor symlink itself; never read through it.
            continue
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink():
            content = os.readlink(path).encode()
            mode = "120000"
        elif path.is_file():
            content = path.read_bytes()
            mode = "100755" if path.stat().st_mode & stat.S_IXUSR else "100644"
        else:
            raise ValueError(f"Unsupported private entry: {name}")
        arguments = ["hash-object", "--stdin"]
        if store:
            arguments.insert(1, "-w")
        blob = git(root, *arguments, input=content).stdout.decode().strip()
        result[name] = {"blob": blob, "mode": mode, "sha256": hashlib.sha256(content).hexdigest()}
    return result


def private_snapshot(repo: Path) -> dict[str, Any]:
    """Persist recoverable pre-session bytes, including preexisting unstaged/untracked edits."""
    root = repo / "literature/.private"
    path = repo / ".archon-horizon/overlay/private-start.json"
    if not (root / ".git").exists():
        result = {"available": False}
    else:
        head = git(root, "rev-parse", "HEAD", check=False)
        files = private_files(root, store=True)
        result = {
            "available": True,
            "head": head.stdout.decode().strip() if not head.returncode else None,
            "status": git(root, "status", "--porcelain=v1", "-z").stdout.decode(),
            "index": git(root, "ls-files", "--stage", "-z").stdout.decode(),
            "files": files,
            "hashes": {name: record["sha256"] for name, record in files.items()},
        }
    atomic_write(path, json_text(result))
    return result


def _restore_private(root: Path, name: str, original: dict | None, snapshot: dict) -> None:
    path = root / name
    # A session-created ancestor symlink must never redirect a rollback outside
    # the private checkout. Restore such entries before their children.
    if not path.parent.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Private rollback path escapes its checkout: {name}")
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        raise ValueError(f"Cannot replace a directory during private rollback: {name}")
    if original:
        content = git(root, "cat-file", "blob", original["blob"]).stdout
        path.parent.mkdir(parents=True, exist_ok=True)
        if original["mode"] == "120000":
            path.symlink_to(content.decode())
        else:
            atomic_bytes(path, content)
            path.chmod(0o755 if original["mode"] == "100755" else 0o644)
    index = next(
        (entry for entry in snapshot["index"].split("\0") if entry.partition("\t")[2] == name), None
    )
    git(root, "update-index", "--force-remove", "--", name)
    if index:
        git(root, "update-index", "-z", "--index-info", input=(index + "\0").encode())


def private_after_session(repo: Path, record: dict, session: Path) -> dict:
    """Restore forbidden private changes byte-for-byte and commit only this T task's pages."""
    info = record["metadata"]["homalg"]
    if info["stage"] != "T":
        return {"changed": [], "violations": []}
    root = repo / "literature/.private"
    snapshot_path = repo / ".archon-horizon/overlay/private-start.json"
    if not snapshot_path.exists():
        raise ValueError("A transcription session requires a private-snapshot baseline")
    snapshot = json.loads(snapshot_path.read_text())
    if not snapshot.get("available"):
        raise ValueError("The transcription private repository was unavailable at session start")
    head = git(root, "rev-parse", "HEAD", check=False)
    current_head = head.stdout.decode().strip() if not head.returncode else None
    if current_head != snapshot["head"]:
        raise ValueError("Private HEAD changed during the session; reconcile it before publication")
    current = private_files(root)
    before = snapshot["files"]

    def index_entries(text: str) -> dict[str, str]:
        return {entry.partition("\t")[2]: entry for entry in text.split("\0") if entry}

    old_index = index_entries(snapshot["index"])
    new_index = index_entries(git(root, "ls-files", "--stage", "-z").stdout.decode())
    changed = sorted(
        name
        for name in set(before) | set(current) | set(old_index) | set(new_index)
        if before.get(name) != current.get(name) or old_index.get(name) != new_index.get(name)
    )
    key = info["doc"]
    manifest = f"{key}/transcription.yaml"
    allowed = {manifest, *(f"{key}/tex/page-{page:04}.tex" for page in info["pages"])}
    violations = [name for name in changed if name not in allowed]
    if manifest in changed and manifest in before:
        try:
            old = load_yaml(git(root, "cat-file", "blob", before[manifest]["blob"]).stdout.decode())
            new = load_yaml((root / manifest).read_text())
            pages = {f"{page:04}" for page in info["pages"]}
            if {key: value for key, value in old.items() if key != "pages"} != {
                key: value for key, value in new.items() if key != "pages"
            } or any(
                old["pages"].get(page) != new["pages"].get(page)
                for page in set(old["pages"]) | set(new["pages"])
                if page not in pages
            ):
                violations.append(manifest)
            for page in pages:
                old_human = [
                    review
                    for review in old["pages"].get(page, {}).get("reviews", [])
                    if review.get("kind") == "human"
                ]
                new_human = [
                    review
                    for review in new["pages"].get(page, {}).get("reviews", [])
                    if review.get("kind") == "human"
                ]
                if old_human != new_human:
                    violations.append(manifest)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            violations.append(manifest)
    for name in sorted(set(violations), key=lambda path: (path.count("/"), path)):
        _restore_private(root, name, before.get(name), snapshot)
    if violations:
        publishing.notify(
            repo,
            key,
            "Restored private changes outside this transcription task: "
            + ", ".join(sorted(set(violations))),
            rule="private-scope",
            task=record["id"],
        )
    accepted = sorted(set(changed) - set(violations))
    if accepted:
        git(root, "add", "-A", "--", *accepted)
        if git(root, "diff", "--quiet", "HEAD", "--", *accepted, check=False).returncode:
            git(
                root,
                "commit",
                "--only",
                "-m",
                f"transcription({key}): pages {','.join(map(str, info['pages']))}",
                "--",
                *accepted,
            )
    if current_head is not None or accepted:
        try:
            branch = git(root, "branch", "--show-current").stdout.decode().strip()
            if not branch:
                raise ValueError("Private checkout must use a named branch")
            git(root, "push", "origin", f"HEAD:refs/heads/{branch}")
        except (RuntimeError, ValueError, OSError) as error:
            publishing.log(
                repo, f"Private push failed; retained local commit for retry: {error}", session
            )
    private_snapshot(repo)
    return {"changed": accepted, "violations": sorted(set(violations))}


def progress_made(
    repo: Path,
    record: dict,
    state: dict,
    prior_overlay: dict,
    since: str,
    session: Path,
    private_start: dict | None = None,
) -> bool:
    """Count changed evidence or a new session-tagged proof attempt, never changed prose alone."""
    info = record["metadata"]["homalg"]
    key, stage = info["doc"], info["stage"]
    if stage == "T":
        private = repo / "literature/.private"
        name = f"{key}/transcription.yaml"
        original = (private_start or {}).get("files", {}).get(name)
        old = (
            load_yaml(git(private, "cat-file", "blob", original["blob"]).stdout.decode())
            if original
            else {"pages": {}}
        )
        path = private / name
        new = load_yaml(path.read_text()) if path.exists() else {"pages": {}}
        return any(
            old["pages"].get(f"{page:04}", {}).get("status")
            != new["pages"].get(f"{page:04}", {}).get("status")
            for page in info["pages"]
        )
    if stage == "INV":
        path = f"literature/{key}/inventory.yaml"
        before = scope.ledger(repo, "show", f"{since}:{path}", check=False)
        old = load_yaml(before.stdout) if not before.returncode else {"pages": {}}
        new = load_yaml((repo / path).read_text()) if (repo / path).exists() else {"pages": {}}
        return any(
            entry.get("complete") and not old["pages"].get(page, {}).get("complete")
            for page, entry in new["pages"].items()
        )
    old_file = scope.ledger(repo, "show", f"{since}:literature/{key}/nodes.json", check=False)
    old_nodes = (
        {node["id"]: node for node in json.loads(old_file.stdout)["nodes"]}
        if not old_file.returncode
        else {}
    )
    current_overlay = overlay_nodes(state)
    nodes = stages.task_nodes(state, record)
    for node in nodes:
        identifier = node["id"]
        if identifier in prior_overlay:
            if any(
                prior_overlay[identifier].get(field) != current_overlay[identifier].get(field)
                for field in ("local_status", "locked", "headline")
            ):
                return True
        else:
            previous = old_nodes.get(identifier)
            if (
                previous is None
                or (previous.get("derived") or {}).get("local_status")
                != node["derived"]["local_status"]
                or bool(previous["authored"]["fidelity"].get("reviewed"))
                != bool(node["authored"]["fidelity"].get("reviewed"))
            ):
                return True
    sessions = {str(session), session.name}
    comments = stages.graph_comments(repo, key)
    return any(
        comment.get("session") in sessions
        and comment.get("body", "").lstrip().startswith("attempt:")
        for node in nodes
        for comment in comments.get(node["id"], [])
    )


def update_attempts(
    repo: Path, record: dict, evaluation: dict, progressed: bool, token: str
) -> dict:
    """Make repeated hook invocations idempotent and preserve human-blocked tasks."""
    path = repo / ".archon-horizon/tasks/items" / f"{record['id']}.yaml"
    current = parse_metadata(path.read_text())
    info = current["metadata"]["homalg"]
    if info.get("last_hook") == token:
        return {"attempts": info.get("attempts", 0), "status": current.get("status")}
    complete = evaluation["complete"]
    attempts = 0 if complete or progressed else int(info.get("attempts", 0)) + 1
    info.update(attempts=attempts, last_hook=token)
    atomic_write(path, dump_metadata(current))
    target = "done" if complete else "blocked" if attempts >= 3 else "queued"
    if current.get("status") == "blocked" and not complete:
        target = "blocked"
    args = ["task", "set", current["id"], "--status", target, "--author", "homalg", "--json"]
    if not complete and not progressed:
        args.extend(("--priority", "low"))
    engine.horizon(repo, *args)
    if attempts >= 3 and not complete:
        publishing.notify(
            repo,
            info["doc"],
            f"Task {current['id']} made no evidence progress in three consecutive sessions. "
            "Review its attempts and unblock it after deciding the next step.",
            rule="stalled-task",
            task=current["id"],
        )
    return {"attempts": attempts, "status": target}


def after_session(repo: Path, task_id: str, session: Path, since: str, until: str) -> dict:
    """Apply the nine-step hook, keeping all routine output exclusively in hooks.log."""
    record = engine.task(repo, task_id)
    violations = scope.check_scope(repo, task_id, since, until)
    if violations:
        raise ScopeViolation(violations)
    key = record["metadata"]["homalg"]["doc"]
    session = session if session.is_absolute() else repo / session
    session.mkdir(parents=True, exist_ok=True)
    output = io.StringIO()
    result: dict[str, Any] = {"task": task_id, "doc_key": key, "ok": False}
    overlay_path = repo / ".archon-horizon/overlay/HomAlg.json"
    prior_overlay = json.loads(overlay_path.read_text()) if overlay_path.exists() else {}
    start_path = repo / ".archon-horizon/overlay/private-start.json"
    private_start = json.loads(start_path.read_text()) if start_path.exists() else None
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            result["private"] = private_after_session(repo, record, session)
            schemas = SchemaStore(repo / "schema")
            for path, content in generate_roots(repo, (key,)).items():
                atomic_write(repo / path, content)
            atomic_write(
                repo / f"literature/{key}/nodes.json",
                json_text(extract_document(repo, key, schemas)),
            )
            export = repo / "build" / f"lean-export-{key}.json"
            build_error = None
            try:
                export_lean(repo, key, export)
            except (ValueError, RuntimeError, OSError) as error:
                build_error = error
                publishing.log(repo, f"Lean export failed: {error}", session)
            findings, skipped, data = validate_repo(
                repo,
                (key,),
                fast=build_error is not None,
                no_build=build_error is None,
                export=export if build_error is None else None,
            )
            report = {
                "command": "validate",
                "ok": not any(item.severity == "error" for item in findings)
                and build_error is None,
                "at": publishing.timestamp(datetime.now(UTC)),
                "findings": [asdict(item) for item in findings],
                "skipped": skipped,
                "data": data,
            }
            if build_error:
                report["findings"].append(
                    {
                        "rule": getattr(build_error, "rule", "lean-build"),
                        "severity": "error",
                        "file": "lakefile.toml",
                        "message": str(build_error),
                    }
                )
            atomic_write(repo / f".archon-horizon/overlay/validate-{key}.json", json_text(report))
            for finding in report["findings"]:
                if finding["severity"] != "error":
                    continue
                node = finding.get("node")
                path = finding.get("file", "")
                if not node and re.fullmatch(r"HomAlg/[^/]+/[^/]+\.lean", path):
                    node = path.removeprefix("HomAlg/").removesuffix(".lean").replace("/", ".", 1)
                publishing.notify(
                    repo, key, finding["message"], rule=finding["rule"], node=node, task=task_id
                )
            state = document_state(repo, key)
            overlay = {
                node: value
                for node, value in prior_overlay.items()
                if not node.startswith(key + ".")
            }
            overlay.update(overlay_nodes(state))
            atomic_write(overlay_path, json_text(overlay))
            evaluation = stages.evaluate(repo, record, refresh_exports=False)
            if not report["ok"]:
                evaluation["complete"] = False
            progressed = progress_made(
                repo, record, state, prior_overlay, since, session, private_start
            )
            token = f"{session}:{since}:{until}"
            result.update(update_attempts(repo, record, evaluation, progressed, token))
            plan_path = repo / f".archon-horizon/overlay/plan-{key}.json"
            prior_plan = json.loads(plan_path.read_text()) if plan_path.exists() else {}
            result["plan"] = planning.plan(
                repo, key, advance=True, no_claim=prior_plan.get("no_claim", False)
            )
            for operation, action in (
                ("publish", lambda: publishing.publish_status(repo, key, session=session)),
                ("backup", lambda: backup(repo, session=session)),
            ):
                try:
                    result[operation] = action()
                except (ValueError, RuntimeError, OSError) as error:
                    publishing.log(repo, f"{operation} deferred; retry next time: {error}", session)
                    result[operation] = {"reason": str(error)}
            result.update(ok=report["ok"], progressed=progressed, evaluation=evaluation)
        except (ValueError, RuntimeError, OSError, KeyError) as error:
            publishing.log(repo, f"Session hook failed: {error}", session)
            result["error"] = str(error)
        finally:
            if output.getvalue():
                publishing.log(repo, output.getvalue(), session)
            publishing.log(repo, json_text(result), session)
    return result


def backup(
    repo: Path,
    *,
    force: bool = False,
    now: datetime | None = None,
    session: Path | None = None,
    client: Client | None = None,
) -> dict:
    """Export owned run logs and fast-forward a private backup without publishing work publicly."""
    current = instant(now or datetime.now(UTC))
    if publishing.throttled(repo, "backup", 360, current, force=force):
        return {"backed_up": False, "reason": "throttled"}
    login = engine.settings(repo).get("login")
    if not login:
        raise ValueError("Run horizon-init before backing up a contribution")
    client = client or Client(repo)
    remote = os.environ.get("HOMALG_BACKUP_REMOTE")
    private = repo / "literature/.private"
    if not remote:
        configured = repo / ".homalg/literature-url"
        remote = configured.read_text().splitlines()[0].strip() if configured.exists() else None
    if not remote and (private / ".git").exists():
        remote = git(private, "remote", "get-url", "origin").stdout.decode().strip()
    if not remote:
        raise ValueError("Configure HOMALG_BACKUP_REMOTE or the private literature remote")
    resolved = client.run("git", "remote", "get-url", remote, check=False)
    remote_url = resolved.stdout.strip() if not resolved.returncode else remote
    public = client.run("git", "remote", "get-url", "origin", check=False).stdout.strip()
    if public and remote_url.rstrip("/") == public.rstrip("/"):
        raise ValueError("The private backup destination must differ from the public origin")
    keys = []
    for key in documents(repo):
        claim = load_yaml((repo / f"literature/{key}/claim.yaml").read_text())
        if claim["claims"] and claim["claims"][0]["holder"].casefold() == login.casefold():
            keys.append(key)
    paths = [path for key in keys for path in publishing.export_logs(repo, repo, key)]
    if paths and client.git("status", "--porcelain", "--", *paths).strip():
        client.git("add", "-A", "--", *paths)
        client.git(
            "commit", "--only", "-m", "backup: archive local contribution discussions", "--", *paths
        )
    try:
        if (private / ".git").exists():
            branch = git(private, "branch", "--show-current").stdout.decode().strip()
            if branch:
                git(private, "push", "origin", f"HEAD:refs/heads/{branch}")
        client.git("push", remote, f"HEAD:refs/heads/backup/{login}/work")
        publishing.stamp(repo, "backup", current)
        return {"backed_up": True, "documents": keys, "archived": paths}
    except (RuntimeError, OSError) as error:
        publishing.log(repo, f"Backup failed; retained local commits for retry: {error}", session)
        return {"backed_up": False, "reason": "network-or-git-error"}


def sync_main(repo: Path, *, client: Client | None = None, now: datetime | None = None) -> dict:
    """Merge current main with explicit owned-document and append-only conflict rules."""
    from homalg import taxonomy

    require_idle(repo)
    client = client or Client(repo)
    if client.git("status", "--porcelain").strip():
        raise ValueError("Commit or stash working-tree changes before sync-main")
    branch = client.git("branch", "--show-current").strip()
    if not branch or branch in {"main", "master"}:
        raise ValueError("Sync from a named contribution work branch")
    login = engine.settings(repo).get("login")
    if not login:
        raise ValueError("Run horizon-init before synchronizing contributions")
    current = instant(now or datetime.now(UTC))
    client.fetch()
    schemas = SchemaStore(repo / "schema")
    owned = set()
    for key in documents(repo):
        claim = main_claim(client, key, schemas)
        if not claim["claims"] or claim["claims"][0]["holder"].casefold() != login.casefold():
            continue
        present = client.fetch(key)
        history = load_status_history(repo, key, schemas=schemas) if present else []
        view = claim_view(
            claim, history, current, schemas=schemas, policy=policy_for(repo, schemas)
        )
        if view["state"] == "active":
            owned.add(key)
    work = client.git("rev-parse", "HEAD").strip()
    base = client.git("merge-base", work, "origin/main").strip()
    old_manifest = client.blob(work, "lake-manifest.json")
    outcome = client.run("git", "merge", "--no-commit", "--no-ff", "origin/main", check=False)
    conflicts = client.git("diff", "--name-only", "--diff-filter=U").splitlines()
    if outcome.returncode and not conflicts:
        raise RuntimeError(outcome.stderr.strip() or outcome.stdout.strip())
    regenerate = set()
    try:
        for path in conflicts:
            match = re.fullmatch(r"literature/([^/]+)/nodes\.json", path)
            if path == "HomAlg.lean" or match:
                client.git("checkout", "--ours", "--", path)
                if match:
                    regenerate.add(match[1])
                continue
            field = (
                "tags"
                if path == "taxonomy/tags.yaml"
                else "concepts"
                if path == "taxonomy/concepts.yaml"
                else "relations"
                if re.fullmatch(r"taxonomy/relations/[^_][^/]*\.yaml", path)
                else None
            )
            if field:

                def record(ref: str, path: str = path, field: str = field) -> dict:
                    text = client.blob(ref, path)
                    return load_yaml(text) if text is not None else {"schema_version": 1, field: []}

                merged = append_merge_records(
                    record(base), record("origin/main"), record(work), field
                )
                atomic_write(repo / path, dump_metadata(merged))
                client.git("add", "--", path)
            elif any(
                path == f"HomAlg/{key}.lean"
                or path.startswith((f"HomAlg/{key}/", f"literature/{key}/"))
                for key in owned
            ):
                if client.blob(work, path) is None:
                    client.git("rm", "--", path)
                else:
                    client.git("checkout", "--ours", "--", path)
                    client.git("add", "--", path)
            else:
                raise ValueError(f"Unresolved merge conflict outside owned/generated paths: {path}")
        taxonomy.apply_merges(repo)
        for path, content in generate_roots(repo).items():
            atomic_write(repo / path, content)
        manifest_path = repo / "lake-manifest.json"
        new_manifest = manifest_path.read_text() if manifest_path.exists() else None
        if old_manifest != new_manifest:
            client.run("lake", "exe", "cache", "get")
        for key in sorted(regenerate | owned):
            atomic_write(
                repo / f"literature/{key}/nodes.json",
                json_text(extract_document(repo, key, schemas)),
            )
            export_lean(repo, key)
        client.git("add", "-A")
        merging = (
            client.run("git", "rev-parse", "--verify", "MERGE_HEAD", check=False).returncode == 0
        )
        if merging or client.git("diff", "--cached", "--name-only").strip():
            client.git("commit", "-m", "sync: merge origin/main and regenerate derived data")
    except (ValueError, RuntimeError, OSError):
        client.run("git", "merge", "--abort", check=False)
        key = next(iter(sorted(owned)), next(iter(documents(repo)), None))
        if key:
            publishing.notify(
                repo,
                key,
                "sync-main stopped on an unsupported conflict; the merge was aborted. "
                "Resolve the conflict with human review.",
                rule="sync-conflict",
            )
        raise
    return {
        "merged": client.git("rev-parse", "HEAD").strip(),
        "owned": sorted(owned),
        "resolved": conflicts,
    }


def escalate(repo: Path, key: str, *, client: Client | None = None, confirm=None) -> dict:
    """Publish only individually confirmed unresolved items, with an idempotent local trail."""
    documents(repo, (key,))
    records = publishing.related_items(repo, key)
    candidates = []
    for item in records:
        comments = item.get("comments", item.get("metadata", {}).get("comments", []))
        if item.get("status") != "open" or any(
            "github-issue:" in comment.get("body", "") for comment in comments
        ):
            continue
        requested = any(
            comment.get("author") == "human"
            and comment.get("body", "").strip() == "escalate: github"
            for comment in comments
        )
        if item["kind"] in {"dispute", "document-error", "issue"} or requested:
            candidates.append(item)
    if not candidates:
        return {"candidates": 0, "published": []}
    check_human_session("Escalate unresolved run items to GitHub", repo)
    client = client or Client(repo)
    journal_path = repo / f".archon-horizon/overlay/escalated-{key}.json"
    journal = json.loads(journal_path.read_text()) if journal_path.exists() else {}
    approved = []
    # The injectable callback is only a UI/test boundary; the human-session guard
    # remains mandatory and there is deliberately no noninteractive --yes flag.
    for item in candidates:
        if item["id"] in journal:
            # A previous individually confirmed publication succeeded, but its
            # local cross-reference may still need repair after an interruption.
            accepted = True
        elif confirm is None:
            print(f"{item['id']} ({item['kind']}):\n{item['body']}\n")
            accepted = input("Create a GitHub Issue for this item? Type yes: ") == "yes"
        else:
            accepted = bool(confirm(item))
        if accepted:
            approved.append(item)
    published = []
    for item in approved:
        nodes = [
            node.removeprefix("label:") for node in item.get("scope", {}).get("blueprint_nodes", [])
        ]
        label = {"dispute": "dispute", "document-error": "document-error"}.get(
            item["kind"], "run-issue"
        )
        title = f"{key}: {item['kind']} {item['id']}"
        remote = json.loads(client.gh("repo", "view", "--json", "nameWithOwner"))["nameWithOwner"]
        pages = f"https://{remote.split('/')[0]}.github.io/{remote.split('/')[1]}/"
        links = [f"- [{node}]({pages}#/node/{node.replace('.', '/', 1)})" for node in nodes]
        claim = load_yaml((repo / f"literature/{key}/claim.yaml").read_text())
        pr = claim["claims"][0].get("pr") if claim["claims"] else None
        body = f"Archived run item `{item['id']}` for {key}.\n\n{item['body']}\n\n" + "\n".join(
            links
        )
        if pr:
            body += f"\n\nRelated PR: #{pr}\n"
        body += "\n\n```yaml\n" + dump_metadata(item) + "```\n"
        if item["id"] in journal:
            url = journal[item["id"]]["url"]
        else:
            with tempfile.TemporaryDirectory(prefix="homalg-escalate-") as temporary:
                path = Path(temporary) / "body.md"
                path.write_text(body)
                url = client.gh(
                    "issue", "create", "--label", label, "--title", title, "--body-file", str(path)
                ).strip()
        match = re.search(r"/issues/(\d+)$", url)
        if not match:
            raise RuntimeError(f"GitHub did not return the new issue URL for {item['id']}")
        number = int(match[1])
        journal[item["id"]] = {"url": url, "issue": number}
        atomic_write(journal_path, json_text(journal))
        engine.horizon(
            repo,
            "inbox",
            "comment",
            item["id"],
            "--author",
            "homalg",
            "--body",
            f"github-issue: {url}",
            "--json",
        )
        paths = []
        for node in nodes:
            source = node_path(repo, node)
            if not source.exists():
                continue
            text = source.read_text()
            metadata = header_mapping(text)
            dispute = metadata.get("dispute")
            if dispute and dispute.get("inbox") == item["id"]:
                dispute["issue"] = number
                atomic_write(source, replace_header(text, metadata, SchemaStore(repo / "schema")))
                paths.append(source)
        if paths:
            record_human_change(repo, f"record GitHub escalation {number}", paths)
        published.append({"inbox": item["id"], "issue": number, "url": url})
    return {"candidates": len(candidates), "published": published}


class LifecycleHooks:
    """The concrete engine hooks consumed by the scoped submission workflow."""

    def ensure_idle(self, repo: Path, key: str) -> None:
        require_idle(repo)
        path = repo / f".archon-horizon/overlay/validate-{key}.json"
        if not path.exists():
            raise ValueError("Run after-session validation before submitting this document")
        report = json.loads(path.read_text())
        if (
            any(item["severity"] == "error" for item in report.get("findings", []))
            or report.get("ok") is False
        ):
            raise ValueError("The latest session validation has errors")

    def backup(self, repo: Path) -> None:
        result = backup(repo, force=True)
        if not result["backed_up"]:
            raise RuntimeError("Private backup failed; submission has not been published")

    def export_logs(self, repo: Path, tree: Path, key: str) -> None:
        publishing.export_logs(repo, tree, key)

    def publish_status(self, repo: Path, key: str) -> None:
        publishing.publish_status(repo, key, force=True)

    def escalate(self, repo: Path, key: str) -> None:
        escalate(repo, key)
