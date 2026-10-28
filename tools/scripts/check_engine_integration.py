"""Exercise the installed fork and real HomAlg hooks in an isolated synthetic checkout."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from homalg.documents import dump_metadata
from homalg.io import atomic_write, json_text
from homalg.roots import generate_roots
from homalg.schemas import load_yaml


def main() -> int:
    """Run two null sessions with real exports and verify ledger, graph and hook output."""
    source = Path(__file__).resolve().parents[2]
    executable = shutil.which("horizon")
    if executable is None:
        raise RuntimeError("Put the pinned homalg-horizon fork on PATH first")
    environment = dict(os.environ)
    environment["PATH"] = str(source / "tools/.venv/bin") + os.pathsep + environment["PATH"]
    temporary = tempfile.mkdtemp(prefix="homalg-engine-smoke-")
    root = Path(temporary)

    def run(*command: str) -> str:
        result = subprocess.run(
            command, cwd=root, env=environment, capture_output=True, text=True, timeout=1800
        )
        if result.returncode:
            raise RuntimeError(f"{' '.join(command)}\n{result.stdout}\n{result.stderr}")
        return result.stdout

    try:
        for name in ("schema", "taxonomy", "horizon", "HomAlgExport", "docs/fixtures"):
            shutil.copytree(source / name, root / name)
        for name in ("HomAlg", "literature"):
            for key in ("Fixture2000", "Fixture2001"):
                shutil.copytree(source / name / key, root / name / key)
        for name in (
            ".gitignore",
            "lakefile.toml",
            "lake-manifest.json",
            "lean-toolchain",
            "AGENTS.md",
            "CLAUDE.md",
            "horizon-version.txt",
        ):
            shutil.copyfile(source / name, root / name)
        for relative, content in generate_roots(root).items():
            atomic_write(root / relative, content)
        (root / ".lake").mkdir()
        (root / ".lake/packages").symlink_to(source / ".lake/packages", target_is_directory=True)
        shutil.copytree(source / ".lake/build", root / ".lake/build")
        run("git", "init", "-q", "-b", "main")
        run("git", "config", "user.name", "HomAlg integration fixture")
        run("git", "config", "user.email", "fixture@example.invalid")
        run("git", "add", ".")
        run("git", "commit", "-qm", "Original synthetic integration fixture")
        original_head = run("git", "rev-parse", "HEAD").strip()
        private = root / "literature/.private"
        private.mkdir()
        run("git", "init", "-q", str(private))
        (root / "references").symlink_to("literature/.private", target_is_directory=True)
        config = load_yaml((root / "horizon/config.template.yaml").read_text())
        config["external_libraries"] = []
        config["harnesses"] = {"primary": {"kind": "null"}}
        atomic_write(root / "config.yaml", dump_metadata(config))
        atomic_write(
            root / ".archon-horizon/overlay/homalg.yaml", dump_metadata({"login": "fixture-user"})
        )
        run(executable, "--root", str(root), "init", "--update", "--no-interactive")
        run("homalg", "plan", "Fixture2000", "--no-claim")
        run(
            executable,
            "--root",
            str(root),
            "run",
            "Fixture2000.INV.1",
            "--rounds",
            "2",
            "--no-dashboard",
        )
        assert (root / ".git/HEAD").is_file()
        assert not (root / ".git.disabled").exists()
        assert run("git", "rev-parse", "HEAD").strip() == original_head
        ledger = root / ".archon-horizon/vcs/workspace.git"
        tracked = run("git", "--git-dir", str(ledger), "ls-tree", "-r", "--name-only", "HEAD")
        assert "HomAlg/Fixture2000/Def_1.lean" in tracked
        assert "literature/.private" not in tracked
        validation = json.loads(
            (root / ".archon-horizon/overlay/validate-Fixture2000.json").read_text()
        )
        assert validation["ok"], validation
        overlay = json.loads((root / ".archon-horizon/overlay/HomAlg.json").read_text())
        assert len(overlay) == 15
        record = load_yaml(
            (root / ".archon-horizon/tasks/items/Fixture2000.INV.1.yaml").read_text()
        )
        report = {
            "ok": True,
            "root_git_preserved": True,
            "validated_nodes": len(overlay),
            "task_status": record["status"],
            "attempts": record["metadata"]["homalg"]["attempts"],
        }
        atomic_write(source / "build/engine-integration.json", json_text(report))
        print(json_text(report), end="")
    except BaseException:
        print(f"Integration checkout retained for diagnosis: {root}")
        raise
    else:
        shutil.rmtree(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
