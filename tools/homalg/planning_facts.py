"""Explicit sweep-local reuse; changed evidence aborts rather than authorizing stale work."""

import copy
import os
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from homalg.claims import effective_expiry, instant, load_status_history
from homalg.leanexport import file_fingerprint
from homalg.schemas import SchemaStore, load_yaml


class StalePlanningInputs(RuntimeError):
    """The caller must restart the complete read phase; partial proposals are not valid."""


def _git(repo: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    return result.returncode, result.stdout


def _inputs(repo: Path) -> dict[str, Any]:
    """Cover validator/state inputs, including absence, ordering and cross-document facts."""
    paths: set[Path] = set()
    for directory in ("HomAlg", "taxonomy", "schema", "horizon", "docs/fixtures", "hgraph"):
        paths.update(path for path in (repo / directory).rglob("*") if path.is_file())
    for document in (repo / "literature").iterdir():
        if document.name.startswith(".") or not document.is_dir():
            continue
        paths.update(path for path in document.rglob("*") if path.is_file())
    private = repo / "literature/.private"
    if private.exists():
        for document in private.iterdir():
            if document.name.startswith(".") or not document.is_dir():
                continue
            paths.add(document / "transcription.yaml")
            paths.update((document / "tex").rglob("*.tex"))
    paths.update((repo / "build").glob("lean-export*.json"))
    paths.update((repo / ".archon-horizon/tasks/items").glob("*.yaml"))
    paths.update(
        repo / name
        for name in (
            "HomAlg.lean",
            "lean-toolchain",
            "lakefile.toml",
            "lake-manifest.json",
            "site/public/data/health.json",
            "config.yaml",
            "literature/.private/.git",
        )
    )
    # These authority files are read only when native owner-decision replay is present.
    run, session = os.environ.get("ARCHON_HORIZON_RUN"), os.environ.get("ARCHON_HORIZON_SESSION")
    if run and session:
        paths.add(repo / f".archon-horizon/runs/{run}/process.json")
        paths.add(repo / f".archon-horizon/runs/{run}/sessions/{session}/meta.json")
    index = _git(repo, "rev-parse", "--git-path", "index")
    if index[0] == 0:
        path = Path(index[1].strip())
        paths.add(path if path.is_absolute() else repo / path)
    # no-pdf observes names outside the mathematical-input directories too.
    public_pdfs = []
    ignored = {".git", ".lake", ".private", ".venv", "node_modules", "build", ".archon-horizon"}
    for directory, children, files in os.walk(repo):
        children[:] = [name for name in children if name not in ignored]
        public_pdfs.extend(
            str(Path(directory) / name) for name in files if name.lower().endswith(".pdf")
        )
    ledger = repo / ".archon-horizon/vcs/workspace.git"
    ledger_head = (
        _git(repo, "--git-dir", str(ledger), "rev-parse", "HEAD") if ledger.is_dir() else None
    )
    return {
        "files": {
            str(path): file_fingerprint(path) if path.is_file() else None for path in sorted(paths)
        },
        "private_checkout_exists": (private / ".git").exists(),
        "public_pdfs": sorted(public_pdfs),
        "git_head": _git(repo, "rev-parse", "HEAD"),
        "git_index_path": index,
        "tracked": _git(repo, "ls-files", "-z"),
        "status_refs": _git(
            repo, "for-each-ref", "--format=%(refname) %(objectname)", "refs/remotes/origin/status/"
        ),
        "ledger_head": ledger_head,
        "native_identity": {
            name: value
            for name, value in os.environ.items()
            if name.startswith("ARCHON_HORIZON_") or name == "HOMALG_SESSION_MAIN_ROOT"
        },
    }


class PlanningFacts:
    """One read phase's exact validation results and document projections, never task verdicts."""

    def __init__(self, repo: Path, *, clock: Callable[[], datetime] | None = None):
        self.repo = repo.resolve()
        self._clock = clock or (lambda: datetime.now(UTC))
        self.started = instant(self._clock())
        self._baseline = _inputs(self.repo)
        self._cache: dict[tuple, Any] = {}
        self._deadline = self._claim_deadline()
        self.assert_current()

    def _claim_deadline(self) -> datetime | None:
        """Reject expiration and future-publication admission boundaries even without file edits."""
        deadlines = []
        try:
            schemas = SchemaStore(self.repo / "schema")
            policy = load_yaml((self.repo / "taxonomy/policy.yaml").read_text())
            if schemas.validate(policy, "policy.schema.json"):
                return None
        except (OSError, ValueError, KeyError, TypeError):
            return None  # Ordinary validation retains its malformed-input findings/errors.
        for path in (self.repo / "literature").glob("*/claim.yaml"):
            try:
                claim = load_yaml(path.read_text())
                if schemas.validate(claim, "claim.schema.json") or not claim["claims"]:
                    continue
            except (OSError, ValueError, KeyError, TypeError):
                continue  # The ordinary validator still reports malformed claims.
            key = claim["doc_key"]
            try:
                history = load_status_history(self.repo, key, schemas=schemas)
            except ValueError:
                history = []  # Match out_of_scope's existing unavailable-history behavior.
            try:
                expiry = effective_expiry(
                    claim["claims"][0],
                    history,
                    self.started,
                    schemas=schemas,
                    doc_key=key,
                    grace_days=policy.get("claim_activity_grace_days", 14),
                )
            except ValueError:
                continue  # Preserve the evaluator's existing invalid-claim error path.
            if expiry > self.started:
                deadlines.append(expiry)
            for status in history:
                if status["holder"].lower() != claim["claims"][0]["holder"].lower() or instant(
                    status["generated_at"]
                ) < instant(claim["claims"][0]["claimed_at"]):
                    continue
                admission = instant(status["generated_at"]) - timedelta(minutes=10)
                if admission > self.started:
                    deadlines.append(admission)
        return min(deadlines) if deadlines else None

    def assert_current(self) -> None:
        """A stale condition escapes the planner's per-task ValueError fallback."""
        now = instant(self._clock())
        if now < self.started or (self._deadline is not None and now >= self._deadline):
            raise StalePlanningInputs(
                "Planning claim/time boundary changed; restart the complete sweep"
            )
        try:
            current = _inputs(self.repo)
        except (OSError, ValueError) as exc:
            raise StalePlanningInputs(
                "Planning inputs changed while reading; restart the sweep"
            ) from exc
        if current != self._baseline:
            raise StalePlanningInputs("Planning inputs changed; restart the complete sweep")

    def require_repo(self, repo: Path) -> None:
        if repo.resolve() != self.repo:
            raise ValueError("Planning facts belong to another repository")
        self.assert_current()

    def _get(self, key: tuple, compute: Callable[[], Any]) -> Any:
        self.assert_current()
        if key not in self._cache:
            value = compute()
            self.assert_current()
            self._cache[key] = value
        return copy.deepcopy(self._cache[key])

    def state(self, key: str, load: Callable) -> dict[str, Any]:
        return self._get(("state", key, load), lambda: load(self.repo, key))

    def validation(
        self, key: str, load: Callable, *, fast: bool, export: Path | None = None
    ) -> Any:
        if fast != (export is None):
            raise ValueError(
                "Planning validation requires fast mode or an explicit existing export"
            )
        if (
            export is not None
            and export.resolve() != (self.repo / "build" / f"lean-export-{key}.json").resolve()
        ):
            raise ValueError("Planning validation export is outside its guarded document path")
        options = {"fast": fast, "now": self.started.isoformat()}
        if export is not None:
            options.update(no_build=True, export=export)
        return self._get(
            ("validation", key, load, fast, str(export) if export else None),
            lambda: load(self.repo, (key,), **options),
        )
