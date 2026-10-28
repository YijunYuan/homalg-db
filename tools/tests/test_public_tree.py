"""Publication preflight sees force-added private text and indirect symlink exposure."""

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "public_tree", ROOT / "tools/scripts/check_public_tree.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_private_paths_and_ordinary_public_assets():
    for value in (
        "references/X/page.png",
        "literature/X/text/page.tex",
        "literature/.private/a.txt",
        "literature/X/ingest.yaml",
        "x.PDF",
        ".env.local",
        "config.yaml",
    ):
        assert MODULE.private_path(value)
    for value in (
        "site/public/logo.png",
        "literature/X/reviews/Def_1.md",
        ".env.example",
        "horizon/config.example.yaml",
    ):
        assert not MODULE.private_path(value)


def test_git_force_add_and_symlink_cannot_hide_private_material(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text("references/\n")
    private = tmp_path / "references"
    private.mkdir()
    (private / "page.tex").write_text("Synthetic private content.\n")
    assert MODULE.check(tmp_path)["ok"]
    subprocess.run(["git", "add", "-f", "references/page.tex"], cwd=tmp_path, check=True)
    (tmp_path / "source-link").symlink_to(private / "page.tex")
    (tmp_path / "external-link").symlink_to(tmp_path.parent / "outside")
    result = MODULE.check(tmp_path)
    assert not result["ok"]
    assert {entry["path"] for entry in result["findings"]} == {
        "references/page.tex",
        "source-link",
        "external-link",
    }
