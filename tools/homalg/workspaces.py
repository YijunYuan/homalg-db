"""Isolated draft workers and conservative, ledger-only integration.

These are cooperative authoring workspaces, not native Horizon sessions or an OS
sandbox. A successful check supplies compilation evidence, never review approval.
"""

import fcntl
import hashlib
import io
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import tarfile
import tempfile
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from homalg.headers import code_only, parse_header
from homalg.human import active_runs
from homalg.io import atomic_bytes, atomic_bytes_with_receipt, atomic_write, json_text
from homalg.schemas import load_yaml
from homalg.scope import human_fields_changed

STATE = ".archon-horizon/draft-workspaces"
LEDGER = ".archon-horizon/vcs/workspace.git"
NODE = re.compile(r"HomAlg/[A-Za-z][A-Za-z0-9_]*/[A-Za-z][A-Za-z0-9_]*\.lean")
LOCAL_OUTPUTS = {".archon-horizon", ".lake", "build", ".git"}
PRIVATE = {"references", "config.yaml", ".env", ".homalg", ".codex", ".claude", ".mcp.json"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _env() -> dict[str, str]:
    """A child must not inherit native session routing or an unrelated Git index."""
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("ARCHON_HORIZON_", "HOMALG_SESSION_", "GIT_", "LEAN_", "LAKE_"))
        and not key.startswith("HORIZON_LEDGER_")
        and key
        not in {
            "HOMALG_BUILD_LOCK_HELD",
            "HOMALG_BOUNDARY_LOCK_HELD",
            "ELAN_TOOLCHAIN",
            "HORIZON_GIT",
        }
    }


def _horizon_executable() -> str:
    """Honor the engine-stamped fork instead of letting login PATH select upstream."""
    stamped = os.environ.get("HORIZON_BIN")
    if stamped:
        path = Path(stamped)
        if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError("HORIZON_BIN must name an executable absolute path")
        return str(path)
    executable = shutil.which("horizon")
    if not executable:
        raise ValueError("Pinned horizon is unavailable")
    return executable


def _git(
    repo: Path, *args: str, data: bytes | None = None, env: dict[str, str] | None = None
) -> bytes:
    result = subprocess.run(
        ["git", "--git-dir", str(repo / LEDGER), "--work-tree", str(repo), *args],
        cwd=repo,
        input=data,
        capture_output=True,
        env=_env() | (env or {}),
        check=False,
    )
    if result.returncode:
        raise ValueError("Draft workspace Git operation failed: " + result.stderr.decode().strip())
    return result.stdout


def _safe(raw: str) -> str:
    path = PurePosixPath(raw)
    if (
        not raw
        or path.is_absolute()
        or any(p in {"", ".", ".."} for p in raw.split("/"))
        or any(c in raw for c in "*?[]\\\x00\n\r")
        or raw.startswith("-")
    ):
        raise ValueError(f"Expected an explicit repository-relative file: {raw!r}")
    if (
        path.parts[0] in LOCAL_OUTPUTS | PRIVATE
        or ".private" in path.parts
        or raw.lower().endswith((".pdf", ".png"))
        or (path.parts[0] == "literature" and set(path.parts) & {"tex", "text", "pages"})
        or (len(path.parts) == 3 and path.parts[0] == "literature" and path.name == "ingest.yaml")
    ):
        raise ValueError(f"Private/runtime paths are not draft source: {raw}")
    return raw


def _path(root: Path, relative: str) -> Path:
    path = root / relative
    for part in [path, *path.parents]:
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f"Symlink is not allowed in a draft source path: {relative}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes workspace: {relative}")
    return path


def _identity(value: os.stat_result) -> dict[str, int]:
    return {
        "dev": value.st_dev,
        "ino": value.st_ino,
        "size": value.st_size,
        "mtime_ns": value.st_mtime_ns,
        "ctime_ns": value.st_ctime_ns,
    }


def _stable_file(
    path: Path, *, strict: bool = False, independent: bool = True
) -> dict[str, Any] | None:
    """Read one inode consistently, rejecting replacement and in-place changes."""
    if not path.exists():
        return None
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or (independent and before.st_nlink != 1):
            raise ValueError(f"Expected an independent regular file: {path}")
        content = stream.read()
        after = os.fstat(stream.fileno())
    if (
        _identity(before) != _identity(after)
        or _identity(after) != _identity(path.lstat())
        or before.st_mode != after.st_mode
    ):
        raise ValueError(f"File changed while reading its snapshot: {path}")
    result: dict[str, Any] = {"sha256": _digest(content), "mode": after.st_mode & 0o777}
    if strict:
        result["identity"] = _identity(after)
    return result


def _file(root: Path, relative: str, *, strict: bool = False) -> dict[str, Any] | None:
    path = _path(root, relative)
    result = _stable_file(path, strict=strict)
    _path(root, relative)
    return result


def _content(value: dict[str, Any] | None) -> dict[str, Any] | None:
    return {key: item for key, item in value.items() if key != "identity"} if value else None


@contextmanager
def _lock(path: Path) -> Iterator[Callable[[], None]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError(f"Lock must not be a symlink: {path}")
    with path.open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(f"Workspace is busy: {path.name}") from exc
        identity = _identity(os.fstat(stream.fileno()))

        def verify() -> None:
            if path.is_symlink() or _identity(path.stat()) != identity:
                raise ValueError(f"Workspace lock was replaced or changed: {path}")

        verify()
        yield verify


def _native_owner(repo: Path, task_id: str | None = None) -> dict[str, Any]:
    """Bind native operations to a live ancestor run, never merely inherited strings.

    This is cooperative runtime ownership, not an OS sandbox or human authority.
    Isolated concurrent runs use their own landing protocol and are refused here.
    """
    root = os.environ.get("ARCHON_HORIZON_ROOT", "")
    run = os.environ.get("ARCHON_HORIZON_RUN", "")
    session = os.environ.get("ARCHON_HORIZON_SESSION", "")
    task_id = task_id or os.environ.get("ARCHON_HORIZON_TASK", "")
    if (
        not root
        or Path(root).resolve() != repo
        or not re.fullmatch(r"[A-Za-z0-9_-]+", run)
        or not re.fullmatch(r"[A-Za-z0-9_.-]+", session)
        or not task_id
        or task_id != os.environ.get("ARCHON_HORIZON_TASK")
        or os.environ.get("HOMALG_SESSION_MAIN_ROOT")
    ):
        raise ValueError("Native workers require their actual parent Horizon task/session")
    config = load_yaml((repo / "config.yaml").read_text())
    if config.get("workspace", {}).get("session_ledger"):
        raise ValueError("Native draft collection requires a single canonical Horizon run")
    run_dir = _path(repo, f".archon-horizon/runs/{run}")
    session_dir = _path(repo, f".archon-horizon/runs/{run}/sessions/{session}")
    if os.environ.get("ARCHON_HORIZON_SESSION_DIR") != str(session_dir):
        raise ValueError("Native session directory does not match its parent run")
    marker = json.loads((run_dir / "process.json").read_text())
    meta = json.loads((session_dir / "meta.json").read_text())
    pid = marker.get("pid")
    ancestors = {}
    current = os.getpid()
    while current > 1:
        try:
            fields = Path(f"/proc/{current}/stat").read_text().rsplit(")", 1)[1].split()
        except OSError as exc:
            raise ValueError("Cannot verify native run process ancestry") from exc
        ancestors[current] = fields[19]
        current = int(fields[1])
    if (
        type(pid) is not int
        or pid not in ancestors
        or marker.get("host") != socket.gethostname()
        or meta.get("status") != "running"
        or meta.get("role") != "horizon"
        or meta.get("task_id") != task_id
    ):
        raise ValueError("Native worker parent is not this live Horizon session")
    # The parent must already own the run lease. Never bypass an idle-workspace guard
    # just because somebody supplied native environment variables.
    lock_path = _path(repo, ".archon-horizon/locks/run-policy.lock")
    with lock_path.open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise ValueError("Native parent does not hold the workspace run lease")
    return {
        "run": run,
        "session": session,
        "task": task_id,
        "pid": pid,
        "process_start": ancestors[pid],
    }


@contextmanager
def _integration_lock(
    repo: Path, *, native_owner: dict[str, Any] | None = None
) -> Iterator[Callable[[], None]]:
    """Exclude unrelated runs/builds; a verified native parent keeps its run lease."""
    with ExitStack() as stack:
        guards = []
        locks = (
            ".archon-horizon/locks/session-boundary.lock",
            ".archon-horizon/cache/checks/workspace.lock",
            STATE + "/registry.lock",
        )
        if native_owner is None:
            locks = (".archon-horizon/locks/run-policy.lock", *locks)
        for relative in locks:
            guards.append(stack.enter_context(_lock(repo / relative)))
        executable = _horizon_executable()
        process = subprocess.run(
            [executable, "--root", str(repo), "ps", "--json"],
            cwd=repo,
            env=_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode:
            raise ValueError("Cannot verify engine inactivity: horizon ps failed")
        try:
            active = active_runs(json.loads(process.stdout))
        except json.JSONDecodeError as exc:
            raise ValueError("Cannot verify engine inactivity: invalid horizon ps output") from exc
        if active and native_owner is None:
            raise ValueError("A Horizon run is active; defer draft integration until it is idle")
        if native_owner is not None:
            rows = json.loads(process.stdout).get("processes", [])
            if (
                len(rows) != 1
                or rows[0].get("run") != native_owner["run"]
                or rows[0].get("pid") != native_owner["pid"]
            ):
                raise ValueError("Native worker requires exactly its own active Horizon run")

        def verify() -> None:
            for guard in guards:
                guard()
            if native_owner is not None and _native_owner(repo) != native_owner:
                raise ValueError("Native worker session ownership changed")

        verify()
        yield verify


def _record_path(repo: Path, worker_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", worker_id):
        raise ValueError("Worker id must contain only letters, digits, underscores and hyphens")
    return _path(repo, f"{STATE}/{worker_id}/record.json")


def _read(repo: Path, worker_id: str) -> dict[str, Any]:
    record = json.loads(_record_path(repo, worker_id).read_text())
    if (
        record.get("schema_version") != 1
        or record.get("id") != worker_id
        or record.get("source_root") != str(repo.resolve())
    ):
        raise ValueError("Worker record does not belong to this source workspace")
    return record


def _save(repo: Path, record: dict[str, Any]) -> None:
    atomic_write(_record_path(repo, record["id"]), json_text(record))


def _worker(repo: Path, record: dict[str, Any]) -> Path:
    return _path(repo, f"{STATE}/{record['id']}/checkout")


def _tree(repo: Path, revision: str) -> dict[str, dict[str, Any]]:
    result = {}
    for entry in _git(repo, "ls-tree", "-rz", revision).split(b"\0"):
        if not entry:
            continue
        info, name = entry.split(b"\t", 1)
        mode, kind, blob = info.decode().split()
        raw = name.decode()
        # The engine tracks its root config in the source ledger. Project public
        # files explicitly; never clone runtime history into a draft ledger.
        if raw == "config.yaml" and kind == "blob" and mode in {"100644", "100755"}:
            continue
        relative = _safe(raw)
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"Snapshot contains a symlink or unsupported entry: {relative}")
        result[relative] = {
            "sha256": _digest(_git(repo, "cat-file", "blob", blob)),
            "mode": int(mode[-3:], 8),
        }
    return result


def _public_files(root: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        relative_parent = parent.relative_to(root)
        for name in list(dirs):
            path = parent / name
            if relative_parent == Path(".") and name in LOCAL_OUTPUTS:
                if path.is_symlink():
                    raise ValueError(f"Worker runtime directory is shared: {name}")
                dirs.remove(name)
            elif path.is_symlink():
                raise ValueError(f"Worker directory is a symlink: {path.relative_to(root)}")
        for name in files:
            relative = (relative_parent / name).as_posix()
            if relative == ".git":
                pointer = _file(root, relative)
                if not pointer or (root / relative).read_text() != f"gitdir: {LEDGER}\n":
                    raise ValueError("Worker Git pointer no longer names its private ledger")
                continue
            result[relative] = _file(root, relative)
    return result


def _changes(worker: Path, baseline: dict[str, Any]) -> list[str]:
    current = _public_files(worker)
    return sorted(
        path for path in baseline.keys() | current.keys() if baseline.get(path) != current.get(path)
    )


def _protected(before: bytes | None, after: bytes, path: str) -> None:
    old = parse_header(before.decode()).metadata if before is not None else {}
    new = parse_header(after.decode()).metadata
    expected = path.removeprefix("HomAlg/").removesuffix(".lean").replace("/", ".")
    if new.get("id") != expected or new.get("doc") != expected.split(".")[0]:
        raise ValueError(f"Node identity does not match its owned path: {path}")
    if human_fields_changed(old, new) or old.get("fidelity", {}).get("reviewed") != new.get(
        "fidelity", {}
    ).get("reviewed"):
        raise ValueError(f"Draft integration cannot grant or alter review/approval: {path}")


def _context_paths(record: dict[str, Any]) -> set[str]:
    paths = {
        "AGENTS.md",
        "HomAlg/AGENTS.md",
        "lakefile.toml",
        "lakefile.lean",
        "lake-manifest.json",
        "lean-toolchain",
        "horizon-version.txt",
        "horizon/review-policy.yaml",
    } | set(record["extra_dependencies"])
    for path in record["snapshot"]:
        if path.startswith(("tools/homalg/", "schema/", "taxonomy/")):
            paths.add(path)
    for path in record["files"]:
        doc = path.split("/")[1]
        paths.update(
            f"literature/{doc}/{name}"
            for name in ("document.yaml", "inventory.yaml", "hollow-allow.yaml")
        )
        paths.update(
            path
            for path in record["snapshot"]
            if path.startswith(f"literature/{doc}/") and path.endswith(".yaml")
        )
    return paths


def _context_names(repo: Path, record: dict[str, Any]) -> set[str]:
    """Notice newly added uncommitted validation context as well as old files."""
    result = {path for path in _context_paths(record) if _path(repo, path).exists()}
    for relative in ("tools/homalg", "schema", "taxonomy"):
        for path in (repo / relative).rglob("*"):
            if "__pycache__" not in path.parts and (path.is_file() or path.is_symlink()):
                result.add(path.relative_to(repo).as_posix())
    for owned in record["files"]:
        doc = owned.split("/")[1]
        result.update(
            path.relative_to(repo).as_posix()
            for path in (repo / "literature" / doc).rglob("*.yaml")
            if path != repo / "literature" / doc / "ingest.yaml"
        )
    return result


def _task_scope(repo: Path, task_id: str) -> dict[str, Any]:
    from homalg.engine import task

    item = task(repo, task_id)
    scope = item.get("write_set", item.get("scope", {}))
    if scope.get("workspace"):
        raise ValueError("Draft workers require a task with explicit file ownership")
    files = scope.get("files", [])
    for path in files:
        if any(char in path for char in "*?[]") or ".." in Path(path).parts:
            raise ValueError("Registered task has a non-explicit file scope")
    return {
        "id": task_id,
        "write_set": scope,
        "homalg": item["metadata"]["homalg"],
        "objective": item.get("objective", ""),
    }


def _dependencies(worker: Path, record: dict[str, Any]) -> dict[str, Any]:
    paths = _context_paths(record)
    visited: set[str] = set()
    queue = list(record["files"])
    while queue:
        path = queue.pop()
        if path in visited:
            continue
        visited.add(path)
        source = _path(worker, path)
        if not source.is_file():
            raise ValueError(f"Missing owned node or local import: {path}")
        for line in re.findall(
            r"(?m)^\s*(?:public\s+)?import\s+([^\n]+)", code_only(source.read_text())
        ):
            for module in line.split():
                if not re.fullmatch(r"\w+(?:\.\w+)*", module):
                    raise ValueError(f"Unsupported import syntax in {path}")
                local = module.replace(".", "/") + ".lean"
                if local in record["snapshot"] or local in record["files"]:
                    paths.add(local)
                    queue.append(local)
                elif module.startswith("HomAlg."):
                    raise ValueError(f"Local import was absent from the source snapshot: {module}")
                elif module.split(".")[0] in {"Init", "Lean", "Std", "Lake"}:
                    toolchain = _toolchain(worker)
                    prefix = Path(toolchain["prefix"])
                    if not (
                        (prefix / "src/lean" / local).is_file()
                        or (prefix / "lib/lean" / local).with_suffix(".olean").is_file()
                    ):
                        raise ValueError("Unknown toolchain import: " + module)
                else:
                    matches = list((worker / ".lake/packages").glob("*/" + local))
                    if not matches and record.get("native_source_only"):
                        # No compile evidence is claimed: the pinned manifest and
                        # toolchain travel with the draft, and canonical checks
                        # must resolve/typecheck every import after collection.
                        continue
                    if len(matches) != 1:
                        raise ValueError(
                            "External import has no unique snapshotted package source: "
                            + module
                            + "; create with --copy-cache after preparing dependencies"
                        )
                    relative = matches[0].relative_to(worker).as_posix()
                    _file(worker, relative)
    paths -= set(record["files"])
    return {path: _file(worker, path) for path in sorted(paths)}


def _toolchain(worker: Path) -> dict[str, Any]:
    executable = shutil.which("lean")
    if not executable:
        raise ValueError("Lean is unavailable for a pinned toolchain check")
    prefix = subprocess.run(
        [executable, "--print-prefix"],
        cwd=worker,
        env=_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    if prefix.returncode:
        raise ValueError("Cannot resolve the worker's pinned Lean toolchain")
    root = Path(prefix.stdout.strip()).resolve()
    binary = root / "bin/lean"
    if not binary.is_file():
        raise ValueError("Lean toolchain prefix has no compiler binary")
    version = subprocess.run(
        [executable, "--version"],
        cwd=worker,
        env=_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    if version.returncode:
        raise ValueError("Cannot identify the worker's Lean compiler")
    return {
        "prefix": str(root),
        "compiler": _stable_file(binary, strict=True, independent=False),
        "version": (version.stdout + version.stderr).strip(),
    }


def _cache_inputs(worker: Path) -> dict[str, Any]:
    """Bind external package source; generated oleans remain local build outputs."""
    cache = worker / ".lake"
    if not cache.exists():
        return {}
    result = {}
    for directory, dirs, files in os.walk(cache, followlinks=False):
        parent = Path(directory)
        for name in [*dirs, *files]:
            if (parent / name).is_symlink():
                raise ValueError("Worker .lake must contain no shared symlinks")
        dirs[:] = [name for name in dirs if name not in {".git", "build"}]
        for name in files:
            if name.endswith((".lean", ".toml", ".json")) or name == "lean-toolchain":
                relative = (parent / name).relative_to(worker).as_posix()
                result[relative] = _file(worker, relative)
    return result


def _inspect(repo: Path, record: dict[str, Any]) -> dict[str, Any]:
    worker = _worker(repo, record)
    changed = _changes(worker, record["snapshot"])
    unexpected = sorted(set(changed) - set(record["files"]))
    if unexpected:
        raise ValueError("Worker changed files outside its ownership: " + ", ".join(unexpected))
    for path in changed:
        target = _path(worker, path)
        if not target.is_file():
            raise ValueError("Draft integration does not delete nodes: " + path)
        before = (
            _git(repo, "show", record["baseline"] + ":" + path)
            if path in record["snapshot"]
            else None
        )
        _protected(before, target.read_bytes(), path)
    result = {
        "changed": changed,
        "owned": {path: _file(worker, path) for path in record["files"]},
        "dependencies": _dependencies(worker, record),
        "package_inputs": _cache_inputs(worker),
        "toolchain": _toolchain(worker),
    }
    inputs = result["owned"] | result["dependencies"] | result["package_inputs"]
    identities = {}
    for path, expected in inputs.items():
        value = _file(worker, path, strict=True)
        if _content(value) != expected:
            raise ValueError("Worker inputs changed while taking snapshot: " + path)
        identities[path] = value["identity"] if value else None
    result["input_identities"] = identities
    return result


def create(
    repo: Path,
    worker_id: str,
    *,
    author: str,
    files: tuple[str, ...],
    dependencies: tuple[str, ...] = (),
    copy_cache: bool = False,
    task_id: str | None = None,
    native: bool = False,
) -> dict[str, Any]:
    """Lease exact node paths and copy a clean, current source-ledger snapshot."""
    repo = repo.resolve()
    owner = _native_owner(repo, task_id) if native else None
    if native:
        task_id = owner["task"]
    destination = _record_path(repo, worker_id)
    bound_task = _task_scope(repo, task_id) if task_id else None
    if bound_task:
        allowed = {path for path in bound_task["write_set"]["files"] if NODE.fullmatch(path)}
        files = files or tuple(sorted(allowed))
        if not set(files) <= allowed:
            raise ValueError("Owned files exceed the registered task's explicit scope")
    if not author.strip() or not files or len(set(files)) != len(files):
        raise ValueError("Supply a real author identity and distinct explicit owned files")
    for path in files:
        if not NODE.fullmatch(_safe(path)):
            raise ValueError("Draft workers own only explicit HomAlg/<Doc>/<Node>.lean files")
    for path in dependencies:
        _safe(path)
    if set(dependencies) & set(files):
        raise ValueError("Extra dependencies must not duplicate owned files")
    with _integration_lock(repo, native_owner=owner) as verify_locks:
        if destination.parent.exists():
            raise ValueError("Worker id already exists; use a new id to retain its evidence")
        for item in (repo / STATE).glob("*/record.json"):
            other = json.loads(item.read_text())
            if other["status"] not in {"promoted", "retired"} and set(files) & set(other["files"]):
                raise ValueError("File ownership overlaps worker " + other["id"])
        baseline = _git(repo, "rev-parse", "HEAD").decode().strip()
        snapshot = _tree(repo, baseline)
        dirty = [path for path, value in snapshot.items() if _file(repo, path) != value]
        untracked = _git(repo, "ls-files", "--others", "--exclude-standard", "-z")
        if dirty or untracked.strip(b"\0"):
            raise ValueError(
                "Commit or reconcile public source into its ledger before creating workers"
            )
        for path in files:
            if path not in snapshot and (repo / path).exists():
                raise ValueError("New owned path already exists outside the snapshot: " + path)
        for path in dependencies:
            if path not in snapshot:
                raise ValueError("Explicit dependency is absent from the ledger: " + path)
        destination.parent.mkdir(parents=True)
        worker = destination.parent / "checkout"
        worker.mkdir()
        try:
            archive = _git(repo, "archive", baseline)
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                # Names/modes were checked in the immutable tree before extraction.
                for member in tar.getmembers():
                    if member.isfile():
                        if member.name not in snapshot:
                            continue
                        _safe(member.name)
                        target = worker / member.name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        stream = tar.extractfile(member)
                        assert stream is not None
                        target.write_bytes(stream.read())
                        target.chmod(snapshot[member.name]["mode"])
            worker_ledger = worker / LEDGER
            worker_ledger.parent.mkdir(parents=True)
            subprocess.run(
                ["git", "init", "--bare", "-q", str(worker_ledger)],
                capture_output=True,
                check=True,
                env=_env(),
            )
            _git(worker, "config", "core.bare", "false")
            _git(worker, "config", "core.worktree", str(worker))
            identity = {
                "GIT_AUTHOR_NAME": author,
                "GIT_AUTHOR_EMAIL": "draft@homalg.invalid",
                "GIT_COMMITTER_NAME": author,
                "GIT_COMMITTER_EMAIL": "draft@homalg.invalid",
            }
            _git(worker, "add", "--", *snapshot)
            _git(worker, "commit", "-qm", "Isolated public source snapshot", env=identity)
            # Prevent ordinary Git invoked by Lake/editors from walking upward
            # into the canonical user's .git. This pointer names only this ledger.
            (worker / ".git").write_text(f"gitdir: {LEDGER}\n")
            if copy_cache and (repo / ".lake").exists():
                # Reflinks are independent COW files; fallback copies bytes, never hardlinks.
                subprocess.run(
                    ["cp", "-pRL", "--reflink=auto", str(repo / ".lake"), str(worker / ".lake")],
                    capture_output=True,
                    check=True,
                )
            record = {
                "schema_version": 1,
                "kind": "draft-worker",
                "id": worker_id,
                "source_root": str(repo),
                "source_ledger": LEDGER,
                "baseline": baseline,
                "author": author,
                "created_at": _now(),
                "status": "draft",
                "files": sorted(files),
                "extra_dependencies": sorted(set(dependencies)),
                "snapshot": snapshot,
                "copied_cache": copy_cache,
                "registered_task": bound_task,
                "native_owner": owner,
                "native_source_only": native and not copy_cache,
                "check": None,
                "promotion": None,
                "authority": "Draft only; no native task completion, fidelity or human approval",
            }
            if _changes(worker, snapshot):
                raise ValueError("Worker checkout did not reproduce the source ledger")
            _cache_inputs(worker)
            verify_locks()
            _save(repo, record)
        except BaseException:
            shutil.rmtree(destination.parent)
            raise
    return {
        "id": worker_id,
        "checkout": str(worker),
        "baseline": baseline,
        "author": author,
        "files": sorted(files),
        "status": "draft",
        "author_commands": ["homalg", "workspaces", "exec", "--repo", str(repo), worker_id, "--"],
    }


def status(repo: Path, worker_id: str | None = None) -> dict[str, Any]:
    """Inspect current bytes without granting completion or modifying state."""
    repo = repo.resolve()
    ids = (
        [worker_id]
        if worker_id
        else sorted(path.parent.name for path in (repo / STATE).glob("*/record.json"))
    )
    workers = []
    for identifier in ids:
        record = _read(repo, identifier)
        item = {key: record[key] for key in ("id", "author", "baseline", "status", "files")}
        item["checkout"] = str(_worker(repo, record))
        try:
            current = _inspect(repo, record)
            item.update(current)
            item["check_current"] = bool(
                record["check"] and record["check"]["ok"] and record["check"]["inputs"] == current
            )
        except ValueError as exc:
            item["error"] = str(exc)
            item["check_current"] = False
        workers.append(item)
    return {"workers": workers}


def check(repo: Path, worker_id: str, *, by: str, timeout: int = 1800) -> dict[str, Any]:
    """Run the pinned fork's actual check and bind its result to exact draft inputs."""
    repo = repo.resolve()
    if not by.strip() or timeout < 1:
        raise ValueError("A real checker identity and positive timeout are required")
    with _lock(_record_path(repo, worker_id).parent / "worker.lock") as verify_lock:
        record = _read(repo, worker_id)
        if record["status"] in {"promoted", "retired", "recovery-required"}:
            raise ValueError("This worker cannot be checked; retain it and create a fresh worker")
        worker = _worker(repo, record)
        before = _inspect(repo, record)
        expected = (worker / "horizon-version.txt").read_text().splitlines()[0].strip()
        executable = _horizon_executable()
        version = subprocess.run(
            [executable, "--version"],
            cwd=worker,
            env=_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        version_text = (version.stdout + version.stderr).strip()
        if version.returncode or not re.search(
            rf"(?<![\w.+-])v?{re.escape(expected)}(?![\w.+-])", version_text
        ):
            raise ValueError("Required horizon " + expected + "; found " + version_text)
        targets = [path.removesuffix(".lean").replace("/", ".") for path in record["files"]]
        command = [
            executable,
            "--root",
            str(worker),
            "check",
            *targets,
            "--timeout",
            str(timeout),
            "--json",
        ]
        result = subprocess.run(
            command, cwd=worker, env=_env(), capture_output=True, text=True, check=False
        )
        stamp = _now().replace(":", "-")
        evidence = _record_path(repo, worker_id).parent / "checks" / stamp
        evidence.mkdir(parents=True)
        atomic_write(evidence / "stdout.txt", result.stdout)
        atomic_write(evidence / "stderr.txt", result.stderr)
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            output = {}
        if not isinstance(output, dict):
            output = {"invalid_result": output}
        inspection_error = None
        try:
            after = _inspect(repo, record)
        except ValueError as exc:
            after = None
            inspection_error = str(exc)
        # A cold build may populate package sources; it may not rewrite existing inputs.
        stable = after is not None and all(
            before[key] == after[key] for key in ("changed", "owned", "dependencies", "toolchain")
        )
        if after is not None:
            stable &= all(
                after["package_inputs"].get(path) == value
                for path, value in before["package_inputs"].items()
            )
            stable &= all(
                after["input_identities"].get(path) == value
                for path, value in before["input_identities"].items()
            )
        ok = (
            result.returncode == 0
            and output.get("ok") is True
            and output.get("status") in {"passed", "reused"}
            and output.get("returncode") == 0
            and output.get("command") == ["lake", "build", *targets]
            and stable
        )
        checked = {
            "ok": ok,
            "by": by,
            "at": _now(),
            "command": command,
            "engine_version": version_text,
            "engine_sha256": _digest(Path(executable).read_bytes()),
            "returncode": result.returncode,
            "result": output,
            "inputs": after,
            "inputs_stable": stable,
            "inspection_error": inspection_error,
            "stdout_sha256": _digest(result.stdout.encode()),
            "stderr_sha256": _digest(result.stderr.encode()),
            "evidence": str(evidence.relative_to(repo)),
        }
        atomic_write(evidence / "result.json", json_text(checked))
        record["check"] = checked
        record["status"] = "checked" if ok else "check-failed"
        verify_lock()
        _save(repo, record)
        return {"id": worker_id, "ok": ok, "check": checked}


def promote(
    repo: Path,
    worker_id: str,
    *,
    by: str,
    native: bool = False,
    _collect: bool = False,
) -> dict[str, Any]:
    """Integrate checked owned files, preserving all unrelated source and staged edits."""
    repo = repo.resolve()
    if not by.strip():
        raise ValueError("The actual integrating operator identity is required")
    if _collect and not native:
        raise ValueError("Uncompiled collection is owned only by the native Horizon session")
    owner = _native_owner(repo) if native else None
    with (
        _integration_lock(repo, native_owner=owner) as verify_locks,
        _lock(_record_path(repo, worker_id).parent / "worker.lock") as verify_worker_lock,
    ):
        record = _read(repo, worker_id)
        if native and record.get("native_owner") != owner:
            raise ValueError("Worker belongs to another native task/session; use idle recovery")
        if _collect and record["status"] not in {"draft", "checked"}:
            raise ValueError("Only an uncollected candidate can be collected")
        if not _collect and record["status"] != "checked":
            raise ValueError("Worker needs a successful current check before promotion")
        current = _inspect(repo, record)
        if not _collect and (not record["check"]["ok"] or record["check"]["inputs"] != current):
            raise ValueError("Check is stale: worker source or dependencies changed")
        if not current["changed"]:
            raise ValueError("Worker has no changed owned files to promote")
        head = _git(repo, "rev-parse", "HEAD").decode().strip()
        _git(repo, "merge-base", "--is-ancestor", record["baseline"], head)
        tree = _tree(repo, head)
        if _context_paths(record | {"snapshot": tree}) != _context_paths(record):
            raise ValueError("Source validation context gained or lost dependency files")
        context_names = _context_names(repo, record)
        if context_names != _context_paths(record) & set(record["snapshot"]):
            raise ValueError("Source validation context has uncommitted additions or deletions")
        for path in record["files"]:
            baseline = record["snapshot"].get(path)
            if _file(repo, path) != baseline or tree.get(path) != baseline:
                raise ValueError("Owned source changed since worker creation: " + path)
        for path, expected in current["dependencies"].items():
            if _file(repo, path) != expected or tree.get(path) != expected:
                raise ValueError("Source dependency changed since worker creation: " + path)
        for path, expected in current["package_inputs"].items():
            # Canonical dependency caches may be symlinks. Read them only; the
            # worker has a separate copy and is never allowed such links.
            source = (repo / path).resolve()
            value = _stable_file(source, independent=False)
            if value != expected:
                raise ValueError("Source package dependency changed or is unavailable: " + path)
        if _toolchain(repo) != current["toolchain"]:
            raise ValueError("Source Lean toolchain changed since the worker check")
        if (
            record.get("registered_task")
            and _task_scope(repo, record["registered_task"]["id"]) != record["registered_task"]
        ):
            raise ValueError("Registered task scope or objective changed since worker creation")
        # The source ledger's index must not hide a competing edit to an owned path.
        staged = _git(repo, "diff", "--cached", "--name-only", "-z", "HEAD", "--")
        if set(staged.decode().split("\0")) & set(record["files"]):
            raise ValueError("An owned source file has staged edits; reconcile them first")
        worker = _worker(repo, record)
        changes = current["changed"]
        landed = {path: _path(worker, path).read_bytes() for path in changes}
        old = {
            path: (_path(repo, path).read_bytes() if (repo / path).exists() else None)
            for path in changes
        }
        source_inputs = {
            path: _file(repo, path, strict=True)
            for path in set(record["files"]) | set(current["dependencies"])
        }
        source_packages = {
            path: _stable_file((repo / path).resolve(), strict=True, independent=False)
            for path in current["package_inputs"]
        }
        for path, value in source_inputs.items():
            expected = (
                record["snapshot"].get(path)
                if path in record["files"]
                else current["dependencies"][path]
            )
            if _content(value) != expected:
                raise ValueError("Canonical inputs changed during promotion preparation: " + path)
        for path, value in source_packages.items():
            if _content(value) != current["package_inputs"][path]:
                raise ValueError("Canonical package changed during promotion preparation: " + path)
        for path in changes:
            if _digest(landed[path]) != current["owned"][path]["sha256"] or (
                old[path] is not None and _digest(old[path]) != source_inputs[path]["sha256"]
            ):
                raise ValueError("Source bytes changed during promotion preparation")
        journal = {
            "by": by,
            "author": record["author"],
            "started_at": _now(),
            "baseline": record["baseline"],
            "source_before": head,
            "files": changes,
            "inputs": current,
            "source_input_snapshot": source_inputs,
            "source_package_snapshot": source_packages,
            "state": "prepared",
            "native_owner": owner,
            "compilation": "required-at-canonical-acceptance" if _collect else "worker-checked",
        }
        journal_path = _record_path(repo, worker_id).parent / "promotion.json"
        atomic_write(journal_path, json_text(journal))
        updated_ref = False
        written: dict[str, Any] = {}
        try:
            for path in changes:
                if _file(repo, path, strict=True) != source_inputs[path]:
                    raise ValueError("Owned source changed before its atomic replacement: " + path)
                receipt = atomic_bytes_with_receipt(
                    _path(repo, path), landed[path], mode=current["owned"][path]["mode"]
                )
                written[path] = {
                    "sha256": receipt["sha256"],
                    "mode": current["owned"][path]["mode"],
                    "identity": {
                        name: receipt["st_" + name]
                        for name in ("dev", "ino", "size", "mtime_ns", "ctime_ns")
                    },
                }
                if _file(repo, path, strict=True) != written[path]:
                    raise ValueError("Published file no longer matches its write receipt: " + path)
                journal["written_receipts"] = dict(written)
                atomic_write(journal_path, json_text(journal))
            if any(_file(repo, path) != current["owned"][path] for path in changes):
                raise ValueError("Source was edited during draft integration")
            with tempfile.TemporaryDirectory(dir=repo / STATE) as temporary:
                env = {
                    "GIT_INDEX_FILE": str(Path(temporary) / "index"),
                    "GIT_AUTHOR_NAME": record["author"],
                    "GIT_AUTHOR_EMAIL": "draft-author@homalg.invalid",
                    "GIT_COMMITTER_NAME": by,
                    "GIT_COMMITTER_EMAIL": "draft-integrator@homalg.invalid",
                }
                _git(repo, "read-tree", head, env=env)
                _git(repo, "add", "--", *changes, env=env)
                new_tree = _git(repo, "write-tree", env=env).decode().strip()
                commit = (
                    _git(
                        repo,
                        "commit-tree",
                        new_tree,
                        "-p",
                        head,
                        data=f"draft: integrate {worker_id}\n".encode(),
                        env=env,
                    )
                    .decode()
                    .strip()
                )
                staged_tree = _tree(repo, new_tree)
                if any(staged_tree.get(path) != current["owned"][path] for path in changes):
                    raise ValueError("Staged tree contains bytes not covered by the worker check")
                if _inspect(repo, record) != current:
                    raise ValueError("Worker inputs changed during promotion")
                for path, expected in source_inputs.items():
                    if _file(repo, path, strict=True) != written.get(path, expected):
                        raise ValueError("Canonical input changed during promotion: " + path)
                for path, expected in source_packages.items():
                    if (
                        _stable_file((repo / path).resolve(), strict=True, independent=False)
                        != expected
                    ):
                        raise ValueError("Canonical package changed during promotion: " + path)
                if _toolchain(repo) != current["toolchain"]:
                    raise ValueError("Lean compiler changed during promotion")
                if _context_names(repo, record) != context_names:
                    raise ValueError("Canonical validation context changed during promotion")
                if (
                    record.get("registered_task")
                    and _task_scope(repo, record["registered_task"]["id"])
                    != record["registered_task"]
                ):
                    raise ValueError("Registered task changed during promotion")
                verify_locks()
                verify_worker_lock()
                _git(repo, "update-ref", "HEAD", commit, head)
                updated_ref = True
            journal.update(state="committed", source_after=commit, finished_at=_now())
            atomic_write(journal_path, json_text(journal))
            _git(repo, "reset", "-q", commit, "--", *changes)
            record.update(status="promoted", promotion=journal)
            _save(repo, record)
        except BaseException:
            if not updated_ref:
                for path in changes:
                    # Never erase an intervening edit, even during failure recovery.
                    try:
                        still_ours = (
                            path in written and _file(repo, path, strict=True) == written[path]
                        )
                    except (ValueError, OSError):
                        still_ours = False
                    if still_ours:
                        if old[path] is None:
                            (repo / path).unlink()
                        else:
                            atomic_bytes(repo / path, old[path])
                            (repo / path).chmod(record["snapshot"][path]["mode"])
            journal["state"] = "recovery-required"
            atomic_write(journal_path, json_text(journal))
            record.update(status="recovery-required", promotion=journal)
            _save(repo, record)
            raise
    return {
        "id": worker_id,
        "status": "promoted",
        "promotion": journal,
        "review_approval": False,
        "native_task_completed": False,
        "compilation": journal["compilation"],
    }


def collect(repo: Path, worker_id: str, *, by: str) -> dict[str, Any]:
    """Stage native source candidates; compilation/review/acceptance remain pending."""
    return promote(repo, worker_id, by=by, native=True, _collect=True)


def execute(repo: Path, worker_id: str, command: tuple[str, ...]) -> int:
    """Run an author's command in its worker with canonical ledger routing removed."""
    repo = repo.resolve()
    if not command:
        raise ValueError("Supply a worker command after --")
    with _lock(_record_path(repo, worker_id).parent / "worker.lock"):
        record = _read(repo, worker_id)
        if record["status"] in {"promoted", "retired", "recovery-required"}:
            raise ValueError("This worker is no longer writable")
        return subprocess.run(
            command, cwd=_worker(repo, record), env=_env(), check=False
        ).returncode


def retire(repo: Path, worker_id: str, *, by: str, reason: str) -> dict[str, Any]:
    """Release an unused/stale lease without deleting its source or evidence."""
    repo = repo.resolve()
    if not by.strip() or not reason.strip():
        raise ValueError("The actual operator and a retirement reason are required")
    with (
        _integration_lock(repo) as verify_locks,
        _lock(_record_path(repo, worker_id).parent / "worker.lock") as verify_worker_lock,
    ):
        record = _read(repo, worker_id)
        if record["status"] in {"promoted", "retired", "recovery-required"}:
            raise ValueError("Only an unpromoted worker without unresolved recovery can be retired")
        record["retirement"] = {
            "by": by,
            "reason": reason,
            "at": _now(),
            "previous_status": record["status"],
        }
        record["status"] = "retired"
        verify_locks()
        verify_worker_lock()
        _save(repo, record)
    return {
        "id": worker_id,
        "status": "retired",
        "retirement": record["retirement"],
        "checkout_retained": str(_worker(repo, record)),
    }
