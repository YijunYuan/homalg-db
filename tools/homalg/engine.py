"""Horizon workspace setup, task metadata and serialized active-document builds."""

import json
import os
import re
import shutil
import subprocess
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from homalg.claims import claim_view, load_status_history
from homalg.documents import dump_metadata, parse_metadata
from homalg.human import require_idle
from homalg.io import atomic_write
from homalg.leanexport import module_list, run_tool, workspace_lock
from homalg.literature import references_link
from homalg.repository import documents
from homalg.schemas import SchemaStore, load_yaml

IGNORE_PATHS = (
    "build/",
    ".lake/",
    "*.pdf",
    ".homalg/",
    "config.yaml",
    ".archon-horizon/",
    ".claude/",
    ".codex/",
    ".mcp.json",
    ".env",
    "blueprint/",
    "hgraph/",
    "references",
    "literature/.private/",
    "literature/*/text/",
    "literature/*/pages/",
    "literature/*/ingest.yaml",
    "site/node_modules/",
    "site/dist/",
    "site/public/data/",
    "__pycache__/",
)


def horizon(repo: Path, *args: str) -> str:
    """Call the fork as a process, keeping its implementation outside the package API."""
    return run_tool(repo, ["horizon", "--root", str(repo), *args])


def settings(repo: Path) -> dict[str, Any]:
    """Read locally cached login/model preferences without a network request."""
    path = repo / ".archon-horizon/overlay/homalg.yaml"
    return parse_metadata(path.read_text()) if path.exists() else {}


def tasks(repo: Path, key: str | None = None) -> list[dict[str, Any]]:
    """Read Horizon's public task shards without altering statuses or scope."""
    records = []
    for path in sorted((repo / ".archon-horizon/tasks/items").glob("*.yaml")):
        item = parse_metadata(path.read_text())
        if key is None or item.get("metadata", {}).get("homalg", {}).get("doc") == key:
            records.append(item)
    return records


def task(repo: Path, task_id: str) -> dict[str, Any]:
    """Require a registered HomAlg task with a filename-safe id."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", task_id):
        raise ValueError("Invalid task id")
    path = repo / ".archon-horizon/tasks/items" / f"{task_id}.yaml"
    data = parse_metadata(path.read_text())
    if data.get("id") != task_id or not data.get("metadata", {}).get("homalg", {}).get("doc"):
        raise ValueError("Task is not a registered HomAlg task")
    return data


def active_documents(repo: Path, *, now: datetime | None = None) -> list[str]:
    """Union the cached user's active claims with documents having runnable/live tasks."""
    selected = {
        item["metadata"]["homalg"]["doc"]
        for item in tasks(repo)
        if item.get("status") in {"queued", "running"} and item.get("metadata", {}).get("homalg")
    }
    login = settings(repo).get("login", "")
    if login:
        current = now or datetime.now(UTC)
        policy = load_yaml((repo / "taxonomy/policy.yaml").read_text())
        schemas = SchemaStore(repo / "schema")
        for key in documents(repo):
            claim = load_yaml((repo / "literature" / key / "claim.yaml").read_text())
            view = claim_view(
                claim, load_status_history(repo, key), current, policy=policy, schemas=schemas
            )
            if view["state"] == "active" and view["holder"].lower() == login.lower():
                selected.add(key)
    return sorted(selected)


def shared_workspace_conflicts(repo: Path) -> list[str]:
    """Detect another worktree using this checkout's Lake build directory."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    candidates = [
        Path(line[9:]) for line in result.stdout.splitlines() if line.startswith("worktree ")
    ]
    cache = (repo / ".lake/build").resolve()
    return [
        str(path)
        for path in candidates
        if path.resolve() != repo.resolve()
        and (path / ".archon-horizon").exists()
        and (path / ".lake/build").resolve() == cache
    ]


def doctor(repo: Path) -> dict[str, Any]:
    """Check the exact engine version, one-workspace cache boundary and ignore contract."""
    errors = []
    expected = (repo / "horizon-version.txt").read_text().splitlines()[0].strip()
    executable = shutil.which("horizon")
    version = "unavailable"
    if executable:
        result = subprocess.run(
            [executable, "--version"], cwd=repo, capture_output=True, text=True, check=False
        )
        if result.returncode:
            raise RuntimeError("Horizon version query failed: " + result.stderr)
        version = (result.stdout + result.stderr).strip()
        if not re.search(rf"(?<![\w.+-])v?{re.escape(expected)}(?![\w.+-])", version):
            errors.append(f"Required homalg-horizon {expected}; found {version}")
    else:
        errors.append(f"Install homalg-horizon {expected} before initializing")
    ignore = repo / ".gitignore"
    lines = {line.strip().lstrip("/") for line in ignore.read_text().splitlines() if line.strip()}
    missing = sorted(set(IGNORE_PATHS) - lines)
    if missing:
        errors.append("Missing .gitignore entries: " + ", ".join(missing))
    tracked = subprocess.run(
        ["git", "ls-files", "-ci", "--exclude-standard"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if tracked.stdout.strip():
        errors.append(
            "Ignore rules match tracked files: " + tracked.stdout.strip().replace("\n", ", ")
        )
    conflicts = shared_workspace_conflicts(repo)
    if conflicts:
        errors.append("Another workspace shares .lake/build: " + ", ".join(conflicts))
    return {"expected_version": expected, "engine_version": version, "errors": errors}


def initialize(
    repo: Path,
    *,
    engine: str = "codex",
    model: str | None = None,
    effort: str | None = None,
    transcriber_model: str | None = None,
) -> dict[str, Any]:
    """Render the fixed workspace configuration, cache identity and update fork resources."""
    require_idle(repo)
    diagnostics = doctor(repo)
    if diagnostics["errors"]:
        raise ValueError("; ".join(diagnostics["errors"]))
    if not (repo / ".git").exists():
        raise ValueError("Initialize the user repository before Horizon")
    references_link(repo)
    config = parse_metadata((repo / "horizon/config.template.yaml").read_text())
    manifest = json.loads((repo / "lake-manifest.json").read_text())
    revision = next(
        package["rev"] for package in manifest["packages"] if package["name"] == "mathlib"
    )
    harness: dict[str, Any] = {"kind": engine, "options": {}}
    previous = (
        parse_metadata((repo / "config.yaml").read_text())
        if (repo / "config.yaml").exists()
        else {}
    )
    old = previous.get("harnesses", {}).get("primary", {})
    if model or old.get("model"):
        harness["model"] = model or old["model"]
    if effort or old.get("options", {}).get("effort"):
        harness["options"]["effort"] = effort or old["options"]["effort"]
    config["harnesses"] = {"primary": harness}
    config["external_libraries"][0]["rev"] = revision
    identity = run_tool(repo, ["gh", "api", "user", "--jq", ".login"]).strip()
    cached = settings(repo) | {"login": identity}
    if transcriber_model:
        cached["transcriber_model"] = transcriber_model
    changes = [key for key in config if config.get(key) != previous.get(key)]
    atomic_write(repo / "config.yaml", dump_metadata(config))
    atomic_write(repo / ".archon-horizon/overlay/homalg.yaml", dump_metadata(cached))
    before = (repo / ".gitignore").read_bytes()
    output = horizon(repo, "init", "--update", "--no-interactive")
    if (repo / ".gitignore").read_bytes() != before:
        raise RuntimeError("Horizon modified .gitignore despite manage_gitignore: false")
    return {"updated_config_keys": changes, "engine": engine, "login": identity, "output": output}


def build_active(repo: Path) -> dict[str, Any]:
    """Build active document roots and orphan leaves under the shared workspace lock."""
    keys = active_documents(repo)
    modules = module_list(repo, keys)
    if modules:
        context = (
            nullcontext()
            if os.environ.get("HOMALG_BUILD_LOCK_HELD") == "1"
            else workspace_lock(repo)
        )
        with context:
            run_tool(repo, ["lake", "build", *modules])
    return {"documents": keys, "modules": modules}


def private_snapshot(repo: Path) -> dict[str, Any]:
    """Persist a recoverable private-source baseline before a session starts."""
    from homalg.lifecycle import private_snapshot as capture

    return capture(repo)
