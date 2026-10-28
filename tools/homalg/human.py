"""One guard for human-only approvals, including Horizon activity and ledger synchronization."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


class HumanApprovalRequired(ValueError):
    """A guarded change was refused before any authored data was modified."""


def active_runs(payload: Any) -> bool:
    """Interpret Horizon process output conservatively across supported wrapper shapes."""
    if isinstance(payload, list):
        return any(active_runs(item) for item in payload)
    if isinstance(payload, dict):
        if "runs" in payload:
            return active_runs(payload["runs"])
        if "data" in payload:
            return active_runs(payload["data"])
        if "processes" in payload:
            return active_runs(payload["processes"])
        if payload.get("active") is True or payload.get("running") is True:
            return True
        if "status" in payload:
            return payload["status"] not in {
                "done",
                "completed",
                "stopped",
                "failed",
                "exited",
                "dead",
                "idle",
            }
        if "pid" in payload:
            return bool(payload["pid"])
        if payload.get("active") is False or payload.get("running") is False:
            return False
    raise HumanApprovalRequired("Cannot verify engine inactivity: unknown horizon ps response")


def require_idle(repo: Path) -> None:
    """Refuse guarded operations while a local Horizon run may still be writing."""
    if not (repo / ".archon-horizon").exists():
        return
    if not (repo / "config.yaml").exists() and not (repo / ".archon-horizon/vcs").exists():
        return
    executable = shutil.which("horizon")
    if executable is None:
        raise HumanApprovalRequired("Cannot verify engine inactivity: horizon is unavailable")
    result = subprocess.run(
        [executable, "ps", "--json"], cwd=repo, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise HumanApprovalRequired("Cannot verify engine inactivity: horizon ps failed")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HumanApprovalRequired(
            "Cannot verify engine inactivity: invalid horizon ps output"
        ) from exc
    if active_runs(payload):
        raise HumanApprovalRequired(
            "A Horizon run is active. Wait for it to finish, or use horizon ps --kill RUN; "
            "resume interrupted work using horizon run --resume latest."
        )


def check_human_session(action: str, repo: Path) -> None:
    """Reject nonhuman or active contexts before any command preparation that can write."""
    if "ARCHON_HORIZON_SESSION" in os.environ or not sys.stdin.isatty():
        raise HumanApprovalRequired(f"{action} requires a human in an interactive terminal")
    require_idle(repo)


def require_human(action: str, repo: Path, *, details: str = "") -> None:
    """Require an interactive human outside an agent session and outside active runs."""
    check_human_session(action, repo)
    print(f"Human confirmation: {action}\n{details}", file=sys.stderr)
    if input("Type yes to confirm: ") != "yes":
        raise HumanApprovalRequired("Confirmation declined; no changes were written")


def record_human_change(repo: Path, action: str, paths: list[Path]) -> None:
    """Commit approved paths to the engine ledger, preserving unrelated staged changes."""
    ledger = repo / ".archon-horizon/vcs/workspace.git"
    if not ledger.is_dir():
        return
    relative = [str(path.resolve().relative_to(repo.resolve())) for path in paths]
    prefix = ["git", "--git-dir", str(ledger), "--work-tree", str(repo)]
    for args in (
        ["add", "--", *relative],
        ["commit", "--only", "-m", f"human: {action}", "--", *relative],
    ):
        result = subprocess.run(
            [*prefix, *args], cwd=repo, capture_output=True, text=True, check=False
        )
        if result.returncode:
            raise RuntimeError(
                f"Human change was written but ledger recording failed: {result.stderr}"
            )
