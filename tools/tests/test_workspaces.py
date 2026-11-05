"""Real temporary Git ledgers; check executables below are explicitly fictional."""

import fcntl
import json
import os
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import pytest
from click.testing import CliRunner

from homalg import workspaces

A = "HomAlg/Demo/A.lean"
B = "HomAlg/Demo/B.lean"
C = "HomAlg/Demo/C.lean"


def node(name: str, *, imports: str = "", extra: str = "", body: str = "") -> str:
    return (
        f"{imports}\n/-!\n```yaml node\nid: Demo.{name}\ndoc: Demo\n{extra}```\n"
        f"## Statement\nFictional test node {name}.\n-/\n"
        f"namespace Demo\ndef {name} : Nat := 0\n{body}\nend Demo\n"
    )


def git(repo: Path, *args: str, ledger: bool = True) -> str:
    prefix = (
        ["git", "--git-dir", str(repo / workspaces.LEDGER), "--work-tree", str(repo)]
        if ledger
        else ["git"]
    )
    return subprocess.run(
        [*prefix, *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def commit(repo: Path, *paths: str) -> str:
    git(repo, "add", "--", *(paths or (".",)))
    git(repo, "commit", "-qm", "fictional ledger fixture", "--only", "--", *(paths or (".",)))
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Every generic worker case uses the fictional executable below. Tests of
    # explicit executable pinning set their own HORIZON_BIN after this fixture.
    monkeypatch.delenv("HORIZON_BIN", raising=False)
    repo = tmp_path / "source"
    (repo / "HomAlg/Demo").mkdir(parents=True)
    (repo / "literature/Demo").mkdir(parents=True)
    (repo / "schema").mkdir()
    (repo / "schema/fictional.json").write_text("{}\n")
    (repo / A).write_text(node("A", body="-- older user branch"))
    (repo / B).write_text(node("B"))
    (repo / C).write_text(node("C"))
    (repo / "literature/Demo/document.yaml").write_text("title: Fictional fixture\n")
    (repo / ".gitignore").write_text(".archon-horizon/\n.lake/\nbuild/\nconfig.yaml\n")
    (repo / "lean-toolchain").write_text("fictional-toolchain\n")
    (repo / "horizon-version.txt").write_text("0.1.5+homalg.1\n")
    (repo / "lake-manifest.json").write_text('{"packages": []}\n')
    (repo / "lakefile.toml").write_text('name = "fictional"\n')
    git(repo, "init", "-q", ledger=False)
    for ledger in (False, True):
        if ledger:
            subprocess.run(
                ["git", "init", "--bare", "-q", str(repo / workspaces.LEDGER)], check=True
            )
        git(repo, "config", "user.name", "Fictional test", ledger=ledger)
        git(repo, "config", "user.email", "fiction@example.invalid", ledger=ledger)
        git(repo, "add", ".", ledger=ledger)
        git(repo, "commit", "-qm", "fictional baseline", ledger=ledger)
    (repo / A).write_text(node("A", body="-- current private ledger"))
    commit(repo, A)
    binary = tmp_path / "bin"
    binary.mkdir()
    toolchain = tmp_path / "fictional-toolchain"
    (toolchain / "bin").mkdir(parents=True)
    (toolchain / "bin/lean").write_text("fictional compiler, not executable\n")
    (binary / "lean").write_text(
        f"#!{sys.executable}\nimport sys\n"
        f"print({str(toolchain)!r} if '--print-prefix' in sys.argv else 'Fictional Lean 1')\n"
    )
    (binary / "lean").chmod(0o755)
    (binary / "horizon").write_text(
        f"#!{sys.executable}\n"
        + """
# This test double supplies fictional compile evidence, never a real Lean result.
import json, os, sys, time
from pathlib import Path
if '--version' in sys.argv:
    print(os.environ.get('HOMALG_TEST_VERSION', '0.1.5+homalg.1'), file=sys.stderr)
elif 'ps' in sys.argv:
    if os.environ.get('HOMALG_TEST_NATIVE_PS'):
        print(os.environ['HOMALG_TEST_NATIVE_PS'])
        sys.exit(0)
    active = [{'status': 'running'}] if os.environ.get('HOMALG_TEST_ACTIVE') else []
    print(json.dumps({'runs': active}))
else:
    targets = sys.argv[sys.argv.index('check')+1:sys.argv.index('--timeout')]
    root = Path.cwd()
    output = root / '.lake/build/fictional-check.txt'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(str(root))
    sync = os.environ.get('HOMALG_TEST_SYNC_DIR')
    if sync:
        sync = Path(sync)
        (sync / root.parent.name).write_text(str(os.getpid()))
        start = time.monotonic()
        while len(list(sync.iterdir())) < 2:
            if time.monotonic() - start > 5:
                sys.exit(7)
            time.sleep(.02)
    ok = not os.environ.get('HOMALG_TEST_FAIL')
    if os.environ.get('HOMALG_TEST_MUTATE'):
        target = root / (targets[0].replace('.', '/') + '.lean')
        target.write_text(target.read_text() + '\\n-- edited during check\\n')
    if os.environ.get('HOMALG_TEST_ABA'):
        target = root / (targets[0].replace('.', '/') + '.lean')
        original = target.read_bytes()
        target.write_bytes(original + b'\\n-- transient edit\\n')
        target.write_bytes(original)
    if os.environ.get('HOMALG_TEST_BAD_JSON'):
        print('not a result')
        sys.exit(0)
    print(json.dumps({'ok': ok, 'status': 'passed' if ok else 'failed',
                      'command': ['lake', 'build', *targets], 'returncode': 0 if ok else 1}))
    sys.exit(0 if ok else 1)
"""
    )
    (binary / "horizon").chmod(0o755)
    monkeypatch.setenv("PATH", str(binary) + os.pathsep + os.environ["PATH"])
    return repo


def create(source: Path, name: str = "worker-a", file: str = A, **options: object) -> Path:
    result = workspaces.create(
        source, name, author="fictional-author/" + name, files=(file,), **options
    )
    return Path(result["checkout"])


def edit(worker: Path, path: str = A) -> None:
    target = worker / path
    target.write_text(target.read_text() + "\n-- fictional draft change\n")


def check(source: Path, name: str = "worker-a") -> dict:
    return workspaces.check(source, name, by="fictional-checker")


def test_ledger_snapshot_not_user_head_and_two_workers(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Disjoint real checkouts compile concurrently and land without cross-overwriting."""
    user_head = git(source, "rev-parse", "HEAD", ledger=False)
    user_index = (source / ".git/index").read_bytes()
    one, two = create(source), create(source, "worker-b", B)
    assert "current private ledger" in (one / A).read_text()
    assert "older user branch" in git(source, "show", "HEAD:" + A, ledger=False)
    assert (one / ".git").read_text() == f"gitdir: {workspaces.LEDGER}\n"
    assert git(one, "rev-parse", "HEAD", ledger=False) != user_head
    assert not (one / "config.yaml").exists()
    assert not (one / "references").exists()
    assert not (one / ".archon-horizon/tasks").exists()
    assert (one / workspaces.LEDGER).is_dir()
    edit(one)
    edit(two, B)
    sync = tmp_path / "checks-overlap"
    sync.mkdir()
    monkeypatch.setenv("HOMALG_TEST_SYNC_DIR", str(sync))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda name: check(source, name), ["worker-a", "worker-b"]))
    assert all(result["ok"] for result in results)
    assert (one / ".lake/build/fictional-check.txt").read_text() == str(one)
    assert (two / ".lake/build/fictional-check.txt").read_text() == str(two)
    first = workspaces.promote(source, "worker-a", by="fictional-integrator")
    assert not first["native_task_completed"] and not first["review_approval"]
    second = workspaces.promote(source, "worker-b", by="fictional-integrator")
    assert first["promotion"]["source_after"] == second["promotion"]["source_before"]
    assert (source / A).read_bytes() == (one / A).read_bytes()
    assert (source / B).read_bytes() == (two / B).read_bytes()
    assert git(source, "rev-parse", "HEAD", ledger=False) == user_head
    assert (source / ".git/index").read_bytes() == user_index
    assert (
        git(
            source,
            "diff",
            "--name-only",
            first["promotion"]["source_before"],
            first["promotion"]["source_after"],
        )
        == A
    )
    assert (
        git(
            source,
            "diff",
            "--name-only",
            second["promotion"]["source_before"],
            second["promotion"]["source_after"],
        )
        == B
    )


@pytest.mark.parametrize(
    "path",
    [
        "../outside.lean",
        "HomAlg/Demo/*.lean",
        "/tmp/x.lean",
        "references/page.tex",
        "literature/Demo/document.yaml",
        "HomAlg.lean",
        "HomAlg/Demo.lean",
    ],
)
def test_invalid_scope_rejected(source: Path, path: str) -> None:
    with pytest.raises(ValueError):
        create(source, file=path)


def test_overlap_dirty_and_untracked_source_rejected(source: Path) -> None:
    create(source)
    with pytest.raises(ValueError, match="overlaps"):
        create(source, "overlapping")
    edit(source, B)
    with pytest.raises(ValueError, match="reconcile public source"):
        create(source, "dirty", B)
    commit(source, B)
    (source / "stray.txt").write_text("untracked public source")
    with pytest.raises(ValueError, match="reconcile public source"):
        create(source, "untracked", B)


def test_worker_scope_violation_and_symlink_rejected(source: Path, tmp_path: Path) -> None:
    worker = create(source)
    edit(worker, B)
    with pytest.raises(ValueError, match="outside its ownership"):
        check(source)
    (worker / B).write_bytes((source / B).read_bytes())
    (worker / A).unlink()
    (worker / A).symlink_to(source / A)
    with pytest.raises(ValueError, match="Symlink"):
        check(source)


def test_changed_owned_source_never_overwritten(source: Path) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    (source / A).write_text((source / A).read_text() + "\n-- human edit\n")
    before = (source / A).read_bytes()
    with pytest.raises(ValueError, match="Owned source changed"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")
    assert (source / A).read_bytes() == before


def test_transitive_dependency_change_refuses_promotion(source: Path) -> None:
    (source / A).write_text(node("A", imports="import HomAlg.Demo.B"))
    (source / B).write_text(node("B", imports="import HomAlg.Demo.C"))
    commit(source, A, B)
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    edit(source, C)
    commit(source, C)
    with pytest.raises(ValueError, match="dependency changed.*C.lean"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")


@pytest.mark.parametrize(
    "path",
    ["lean-toolchain", "lake-manifest.json", "lakefile.toml", "literature/Demo/document.yaml"],
)
def test_build_and_document_context_staleness(source: Path, path: str) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    (source / path).write_text((source / path).read_text() + "\n ")
    commit(source, path)
    with pytest.raises(ValueError, match="dependency changed"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")


def test_stale_check_failed_check_and_missing_check(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = create(source)
    edit(worker)
    with pytest.raises(ValueError, match="successful current check"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")
    monkeypatch.setenv("HOMALG_TEST_FAIL", "1")
    assert not check(source)["ok"]
    monkeypatch.delenv("HOMALG_TEST_FAIL")
    assert check(source)["ok"]
    edit(worker)
    assert not workspaces.status(source, "worker-a")["workers"][0]["check_current"]
    with pytest.raises(ValueError, match="Check is stale"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")


@pytest.mark.parametrize(
    "extra",
    [
        "fidelity:\n  reviewed:\n    kind: human\n    by: imaginary\n",
        "fidelity:\n  reviewed:\n    kind: agent\n    session: invented\n",
        "dispute:\n  status: resolved\n  kind: statement\n",
    ],
)
def test_no_review_or_human_approval_can_be_imported(source: Path, extra: str) -> None:
    worker = create(source)
    (worker / A).write_text(node("A", extra=extra))
    with pytest.raises(ValueError, match="review/approval"):
        check(source)


def test_unrelated_staged_edits_survive(source: Path) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    edit(source, B)
    git(source, "add", B)
    staged = git(source, "show", ":" + B)
    result = workspaces.promote(source, "worker-a", by="fictional-integrator")
    assert git(source, "show", ":" + B) == staged
    assert git(source, "diff", "--cached", "--name-only") == B
    assert (
        git(
            source,
            "diff",
            "--name-only",
            result["promotion"]["source_before"],
            result["promotion"]["source_after"],
        )
        == A
    )


def test_task_binding_derives_and_revalidates_scope(source: Path) -> None:
    task = source / ".archon-horizon/tasks/items/Demo.STMT.1.yaml"
    task.parent.mkdir(parents=True)
    task.write_text(
        "id: Demo.STMT.1\nmetadata:\n  homalg: {doc: Demo, stage: STMT}\n"
        f"write_set:\n  files: [{A}, literature/Demo/document.yaml]\n"
    )
    result = workspaces.create(
        source, "bound", author="fictional-author", files=(), task_id="Demo.STMT.1"
    )
    assert result["files"] == [A]
    worker = Path(result["checkout"])
    edit(worker)
    assert check(source, "bound")["ok"]
    with pytest.raises(ValueError, match="exceed"):
        create(source, "outside-task", B, task_id="Demo.STMT.1")
    task.write_text(task.read_text() + "objective: changed intent\n")
    with pytest.raises(ValueError, match="Registered task scope"):
        workspaces.promote(source, "bound", by="fictional-integrator")


def test_new_owned_node_and_unknown_import(source: Path) -> None:
    path = "HomAlg/Demo/New.lean"
    worker = create(source, file=path)
    (worker / path).write_text(node("New", imports="import HomAlg.Demo.A"))
    assert check(source)["ok"]
    workspaces.promote(source, "worker-a", by="fictional-integrator")
    other = create(source, "unknown", B)
    (other / B).write_text(node("B", imports="import Unknown.Module"))
    with pytest.raises(ValueError, match="External import"):
        check(source, "unknown")


def test_independent_cache_copy_and_stale_package(source: Path) -> None:
    package = source / ".lake/packages/fiction/Fiction.lean"
    package.parent.mkdir(parents=True)
    package.write_text("-- fictional external dependency\n")
    (source / A).write_text(node("A", imports="import Fiction"))
    commit(source, A)
    worker = create(source, copy_cache=True)
    copied = worker / package.relative_to(source)
    assert copied.read_bytes() == package.read_bytes()
    assert copied.stat().st_ino != package.stat().st_ino
    edit(worker)
    assert check(source)["ok"]
    package.write_text("-- changed external source\n")
    with pytest.raises(ValueError, match="package dependency changed"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")


def test_active_run_and_wrong_version_refused(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOMALG_TEST_ACTIVE", "1")
    with pytest.raises(ValueError, match="run is active"):
        create(source)
    monkeypatch.delenv("HOMALG_TEST_ACTIVE")
    worker = create(source)
    edit(worker)
    monkeypatch.setenv("HOMALG_TEST_VERSION", "99.0.0")
    with pytest.raises(ValueError, match="Required horizon"):
        check(source)


def test_failure_restores_only_own_bytes_and_records_recovery(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    original = (source / A).read_bytes()
    head = git(source, "rev-parse", "HEAD")
    real_git = workspaces._git

    def fail(repo: Path, *args: str, **options: object) -> bytes:
        if args[0] == "write-tree":
            raise ValueError("fictional injected disk failure")
        return real_git(repo, *args, **options)

    monkeypatch.setattr(workspaces, "_git", fail)
    with pytest.raises(ValueError, match="injected"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")
    assert (source / A).read_bytes() == original
    assert git(source, "rev-parse", "HEAD") == head
    assert workspaces.status(source, "worker-a")["workers"][0]["status"] == "recovery-required"


def test_cli_registration_and_machine_output(source: Path) -> None:
    from homalg.cli import cli
    from homalg.cli_workspaces import register_commands

    if "workspaces" not in cli.commands:
        register_commands(cli)
    result = CliRunner().invoke(
        cli,
        [
            "workspaces",
            "create",
            "cli-worker",
            "--author",
            "fictional-author",
            "--file",
            A,
            "--repo",
            str(source),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"]["id"] == "cli-worker"


@pytest.mark.parametrize(
    "variable", ["HOMALG_TEST_MUTATE", "HOMALG_TEST_BAD_JSON", "HOMALG_TEST_ABA"]
)
def test_check_mutation_or_malformed_success_is_not_evidence(
    source: Path, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    worker = create(source)
    edit(worker)
    monkeypatch.setenv(variable, "1")
    result = check(source)
    assert not result["ok"]
    assert (source / result["check"]["evidence"] / "result.json").exists()
    with pytest.raises(ValueError, match="successful current check"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")


def test_native_run_lock_and_worker_lock_exclude_competitors(source: Path) -> None:
    with workspaces._lock(source / ".archon-horizon/locks/run-policy.lock"):
        with pytest.raises(ValueError, match="busy"):
            create(source)
    worker = create(source)
    edit(worker)
    with workspaces._lock(worker.parent / "worker.lock"):
        with pytest.raises(ValueError, match="busy"):
            check(source)


def test_snapshot_refuses_tracked_private_source(source: Path) -> None:
    private = source / "references/private.tex"
    private.parent.mkdir()
    private.write_text("fictional private source must not enter a draft clone")
    commit(source, "references/private.tex")
    with pytest.raises(ValueError, match="Private/runtime"):
        create(source)


def test_shared_worker_build_cache_is_rejected(source: Path) -> None:
    worker = create(source)
    (source / ".lake").mkdir()
    (worker / ".lake").symlink_to(source / ".lake", target_is_directory=True)
    with pytest.raises(ValueError, match="runtime directory is shared"):
        check(source)


def test_staged_owned_edit_cannot_be_hidden_by_restoring_worktree(source: Path) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    original = (source / A).read_bytes()
    edit(source)
    git(source, "add", A)
    (source / A).write_bytes(original)
    with pytest.raises(ValueError, match="staged edits"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")


def test_failed_promotion_preserves_intervening_human_edit(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    real_git = workspaces._git
    human = b"human edit during integration must survive\n"

    def fail(repo: Path, *args: str, **options: object) -> bytes:
        if args[0] == "write-tree":
            (source / A).write_bytes(human)
            raise ValueError("fictional competing edit")
        return real_git(repo, *args, **options)

    monkeypatch.setattr(workspaces, "_git", fail)
    with pytest.raises(ValueError, match="competing edit"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")
    assert (source / A).read_bytes() == human
    record = json.loads((worker.parent / "record.json").read_text())
    assert record["status"] == "recovery-required"


@contextmanager
def native_session(source: Path, monkeypatch: pytest.MonkeyPatch):
    """An explicitly fictional engine identity with a real held run lease."""
    run, session, task_id = "fictional-run", "fictional-session", "Demo.STMT.1"
    directory = source / f".archon-horizon/runs/{run}/sessions/{session}"
    directory.mkdir(parents=True)
    (directory / "meta.json").write_text(
        json.dumps(
            {
                "role": "horizon",
                "status": "running",
                "task_id": task_id,
            }
        )
    )
    (directory.parent.parent / "process.json").write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "host": socket.gethostname(),
            }
        )
    )
    (source / "config.yaml").write_text("workspace: {session_ledger: false}\n")
    task = source / f".archon-horizon/tasks/items/{task_id}.yaml"
    task.parent.mkdir(parents=True)
    task.write_text(
        f"id: {task_id}\nmetadata:\n  homalg: {{doc: Demo, stage: STMT}}\n"
        f"write_set:\n  files: [{A}, {B}]\n"
    )
    for key, value in {
        "ROOT": str(source),
        "RUN": run,
        "SESSION": session,
        "SESSION_DIR": str(directory),
        "TASK": task_id,
    }.items():
        monkeypatch.setenv("ARCHON_HORIZON_" + key, value)
    monkeypatch.setenv(
        "HOMALG_TEST_NATIVE_PS",
        json.dumps(
            {
                "processes": [
                    {
                        "pid": os.getpid(),
                        "run": run,
                        "status": "active",
                    }
                ]
            }
        ),
    )
    lock = source / ".archon-horizon/locks/run-policy.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield directory


def test_runtime_config_projected_without_runtime_history(source: Path) -> None:
    runtime = source / "config.yaml"
    runtime.write_text("fictional_private_runtime_secret: must-not-be-copied\n")
    git(source, "add", "-f", "config.yaml")
    git(source, "commit", "-qm", "fictional runtime config")
    before = git(source, "rev-parse", "HEAD", ledger=False)
    worker = create(source)
    assert not (worker / "config.yaml").exists()
    history = git(worker, "rev-list", "--objects", "--all")
    assert "config.yaml" not in history
    assert len(git(worker, "rev-list", "--all").splitlines()) == 1
    assert git(source, "rev-parse", "HEAD", ledger=False) == before
    edit(worker)
    assert check(source)["ok"]
    workspaces.promote(source, "worker-a", by="fictional-integrator")
    assert "must-not-be-copied" in runtime.read_text()


def test_native_source_only_workers_collect_without_cache_or_acceptance(
    source: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_head = git(source, "rev-parse", "HEAD", ledger=False)
    user_index = (source / ".git/index").read_bytes()
    with native_session(source, monkeypatch):
        one = create(source, native=True)
        two = create(source, "worker-b", B, native=True)
        assert not (one / ".lake").exists()
        # External import resolution is pending the canonical compiler, not
        # represented as fictional successful compilation of a source-only draft.
        (one / A).write_text(node("A", imports="import Mathlib.Algebra.Group.Defs"))
        edit(two, B)
        for name in ("worker-a", "worker-b"):
            result = workspaces.collect(source, name, by="fictional-native-lead")
            assert result["compilation"] == "required-at-canonical-acceptance"
            assert not result["review_approval"] and not result["native_task_completed"]
        assert (source / A).read_bytes() == (one / A).read_bytes()
        assert (source / B).read_bytes() == (two / B).read_bytes()
        with pytest.raises(ValueError, match="busy"):
            create(source, "external", C)
    assert git(source, "rev-parse", "HEAD", ledger=False) == user_head
    assert (source / ".git/index").read_bytes() == user_index


def test_native_scope_dependencies_and_changed_session_are_guarded(
    source: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with native_session(source, monkeypatch) as directory:
        with pytest.raises(ValueError, match="exceed"):
            create(source, "outside", C, native=True)
        worker = create(source, native=True, dependencies=(C,))
        edit(worker)
        edit(source, C)
        with pytest.raises(ValueError, match="dependency changed"):
            workspaces.collect(source, "worker-a", by="fictional-native-lead")
        assert (source / A).read_bytes() != (worker / A).read_bytes()
        meta = json.loads((directory / "meta.json").read_text())
        meta["status"] = "interrupted"
        (directory / "meta.json").write_text(json.dumps(meta))
        with pytest.raises(ValueError, match="live Horizon session"):
            workspaces.collect(source, "worker-a", by="fictional-native-lead")


def test_native_requires_actual_ancestry_and_exclusive_parent(
    source: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="actual parent"):
        create(source, native=True)
    with native_session(source, monkeypatch) as directory:
        marker = directory.parent.parent / "process.json"
        payload = json.loads(marker.read_text())
        payload["pid"] = 99999999
        marker.write_text(json.dumps(payload))
        with pytest.raises(ValueError, match="live Horizon session"):
            create(source, native=True)
        payload["pid"] = os.getpid()
        marker.write_text(json.dumps(payload))
        monkeypatch.setenv(
            "HOMALG_TEST_NATIVE_PS",
            json.dumps(
                {
                    "processes": [
                        {"pid": os.getpid(), "run": "fictional-run", "status": "active"},
                        {"pid": 99999999, "run": "other", "status": "active"},
                    ]
                }
            ),
        )
        with pytest.raises(ValueError, match="exactly its own"):
            create(source, native=True)
    with pytest.raises(ValueError, match="does not hold"):
        create(source, native=True)


def test_stamped_horizon_precedes_path_and_invalid_stamp_is_refused(
    source: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    original = workspaces._horizon_executable()
    monkeypatch.setenv("HORIZON_BIN", original)
    other = tmp_path / "wrong-fork"
    other.mkdir()
    executable = other / "horizon"
    executable.write_text("#!/bin/sh\nexit 99\n")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(other) + os.pathsep + os.environ["PATH"])
    assert workspaces._horizon_executable() == original
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    monkeypatch.setenv("HORIZON_BIN", "relative-horizon")
    with pytest.raises(ValueError, match="executable absolute path"):
        workspaces._horizon_executable()


def test_native_collection_preserves_private_ingestion_config(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private = source / "literature/Demo/ingest.yaml"
    private.write_text("private_source_path: fictional-private-input.pdf\n")
    (source / ".gitignore").write_text(
        (source / ".gitignore").read_text() + "literature/*/ingest.yaml\n"
    )
    commit(source, ".gitignore")
    with native_session(source, monkeypatch):
        worker = create(source, native=True)
        assert not (worker / "literature/Demo/ingest.yaml").exists()
        edit(worker)
        result = workspaces.collect(source, "worker-a", by="fictional-native-lead")
        assert result["compilation"] == "required-at-canonical-acceptance"
        assert not result["native_task_completed"]
        assert private.read_text() == "private_source_path: fictional-private-input.pdf\n"
    git(source, "add", "-f", "literature/Demo/ingest.yaml")
    git(source, "commit", "-qm", "fictional incorrectly tracked private input")
    monkeypatch.delenv("HOMALG_TEST_NATIVE_PS")
    with pytest.raises(ValueError, match="Private/runtime"):
        create(source, "refuse-private-history", B)


def test_native_collect_preserves_review_and_source_ownership_guards(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with native_session(source, monkeypatch):
        worker = create(source, native=True)
        baseline = (source / A).read_bytes()
        (worker / A).write_text(
            node("A", extra="fidelity:\n  reviewed: {by: fictional-forged-review}\n")
        )
        with pytest.raises(ValueError, match="review/approval"):
            workspaces.collect(source, "worker-a", by="fictional-native-lead")
        assert (source / A).read_bytes() == baseline
        (worker / A).write_bytes(baseline)
        edit(worker)
        edit(worker, B)
        with pytest.raises(ValueError, match="outside its ownership"):
            workspaces.collect(source, "worker-a", by="fictional-native-lead")
        assert (source / A).read_bytes() == baseline


def test_native_collect_keeps_build_lock_and_task_identity(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with native_session(source, monkeypatch):
        worker = create(source, native=True)
        edit(worker)
        baseline = (source / A).read_bytes()
        lock = source / ".archon-horizon/cache/checks/workspace.lock"
        with lock.open("a+") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            with pytest.raises(ValueError, match="busy"):
                workspaces.collect(source, "worker-a", by="fictional-native-lead")
        assert (source / A).read_bytes() == baseline
        task = source / ".archon-horizon/tasks/items/Demo.STMT.1.yaml"
        task.write_text(task.read_text() + "objective: Changed fictional objective\n")
        with pytest.raises(ValueError, match="Registered task scope or objective"):
            workspaces.collect(source, "worker-a", by="fictional-native-lead")
        assert (source / A).read_bytes() == baseline


def test_worker_environment_does_not_route_git_to_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("HORIZON_GIT", "HORIZON_LEDGER_GIT_DIR", "HORIZON_LEDGER_WORK_TREE"):
        monkeypatch.setenv(name, "/fictional/canonical/" + name)
    monkeypatch.setenv("HORIZON_BIN", "/fictional/pinned/horizon")
    child = workspaces._env()
    assert not {"HORIZON_GIT", "HORIZON_LEDGER_GIT_DIR", "HORIZON_LEDGER_WORK_TREE"} & child.keys()
    assert child["HORIZON_BIN"] == "/fictional/pinned/horizon"


def test_git_add_race_never_commits_or_restores_external_bytes(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    real_git = workspaces._git
    before = git(source, "rev-parse", "HEAD")
    external = b"external author edited while Git was staging\n"

    def mutate(repo: Path, *args: str, **options: object) -> bytes:
        if args[0] == "add" and "GIT_INDEX_FILE" in options.get("env", {}):
            (source / A).write_bytes(external)
        return real_git(repo, *args, **options)

    monkeypatch.setattr(workspaces, "_git", mutate)
    with pytest.raises(ValueError, match="Staged tree contains bytes"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")
    assert (source / A).read_bytes() == external
    assert git(source, "rev-parse", "HEAD") == before


def test_dependency_aba_during_promotion_is_rejected(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (source / A).write_text(node("A", imports="import HomAlg.Demo.C"))
    commit(source, A)
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    real_git = workspaces._git
    original = (source / C).read_bytes()

    def mutate(repo: Path, *args: str, **options: object) -> bytes:
        if args[0] == "add" and "GIT_INDEX_FILE" in options.get("env", {}):
            (source / C).write_bytes(original + b"transient edit\n")
            (source / C).write_bytes(original)
        return real_git(repo, *args, **options)

    monkeypatch.setattr(workspaces, "_git", mutate)
    with pytest.raises(ValueError, match="Canonical input changed"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")
    assert (source / C).read_bytes() == original


def test_new_uncommitted_validation_context_is_stale(source: Path) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    (source / "schema/new-context.json").write_text("{}\n")
    with pytest.raises(ValueError, match="uncommitted additions"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")


def test_retire_releases_ownership_without_erasing_evidence(source: Path) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    before = (worker / A).read_bytes()
    result = workspaces.retire(
        source,
        "worker-a",
        by="fictional-integrator",
        reason="replace a stale draft with a fresh baseline",
    )
    assert result["status"] == "retired"
    assert (worker / A).read_bytes() == before
    assert list((worker.parent / "checks").glob("*/result.json"))
    create(source, "replacement")
    with pytest.raises(ValueError, match="cannot be checked"):
        check(source)
    with pytest.raises(ValueError, match="successful current check"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")


def test_replaced_integration_lock_refuses_promotion(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    real_git = workspaces._git
    head = git(source, "rev-parse", "HEAD")
    original = (source / A).read_bytes()

    def mutate(repo: Path, *args: str, **options: object) -> bytes:
        if args[0] == "add" and "GIT_INDEX_FILE" in options.get("env", {}):
            lock = source / ".archon-horizon/locks/run-policy.lock"
            replacement = lock.with_suffix(".replacement")
            replacement.write_bytes(b"")
            replacement.replace(lock)
        return real_git(repo, *args, **options)

    monkeypatch.setattr(workspaces, "_git", mutate)
    with pytest.raises(ValueError, match="lock was replaced"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")
    assert git(source, "rev-parse", "HEAD") == head
    assert (source / A).read_bytes() == original


def test_external_replacement_before_writer_returns_is_not_claimed(
    source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = create(source)
    edit(worker)
    assert check(source)["ok"]
    real_write = workspaces.atomic_bytes_with_receipt
    before = git(source, "rev-parse", "HEAD")
    external = {}

    def replace(path: Path, content: bytes, **options: object) -> dict:
        receipt = real_write(path, content, **options)
        if path == source / A:
            other = path.with_suffix(".external")
            other.write_bytes(content)
            other.replace(path)
            external["inode"] = path.stat().st_ino
        return receipt

    monkeypatch.setattr(workspaces, "atomic_bytes_with_receipt", replace)
    with pytest.raises(ValueError, match="no longer matches its write receipt"):
        workspaces.promote(source, "worker-a", by="fictional-integrator")
    assert (source / A).stat().st_ino == external["inode"]
    assert (source / A).read_bytes() == (worker / A).read_bytes()
    assert git(source, "rev-parse", "HEAD") == before
    record = json.loads((worker.parent / "record.json").read_text())
    assert record["status"] == "recovery-required"
