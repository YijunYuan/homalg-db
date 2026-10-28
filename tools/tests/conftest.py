"""Isolated, small checkouts for tests that exercise file generation."""

import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Copy only authored fixtures and contracts, never the Mathlib cache."""
    for directory in ("schema", "taxonomy"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    for directory in ("HomAlg", "literature"):
        (tmp_path / directory).mkdir()
        for path in (ROOT / directory).glob("Fixture*"):
            destination = tmp_path / directory / path.name
            if path.is_dir():
                shutil.copytree(path, destination)
            else:
                shutil.copyfile(path, destination)
    for filename in ("HomAlg.lean", "lakefile.toml", "lean-toolchain"):
        shutil.copyfile(ROOT / filename, tmp_path / filename)
    from homalg.roots import generate_roots

    for relative, text in generate_roots(tmp_path).items():
        (tmp_path / relative).write_text(text)
    return tmp_path
