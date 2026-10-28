"""Migration preflight and all-or-nothing publication against real metadata files."""

from pathlib import Path

import pytest

from homalg import migrations
from homalg.documents import dump_metadata
from homalg.schemas import load_yaml


def test_current_schema_noop_and_private_exclusion(repo: Path) -> None:
    """A current checkout is unchanged and private evidence is never a migration input."""
    private = repo / "literature/.private/Book2000"
    private.mkdir(parents=True)
    (private / "document.yaml").write_text("invalid private content")
    before = {path: path.read_bytes() for path, _ in migrations.inputs(repo)}
    result = migrations.migrate(repo, 1)
    assert result["changed"] == []
    assert all(path.read_bytes() == content for path, content in before.items())
    assert not any(".private" in value for value in result["checked"])


def test_unknown_migration_and_target_refused(repo: Path) -> None:
    """Unsupported versions cannot be silently relabeled as current."""
    with pytest.raises(ValueError, match="supports schema"):
        migrations.migrate(repo, 2)
    path = repo / "literature/Fixture2000/document.yaml"
    data = load_yaml(path.read_text())
    data["schema_version"] = 0
    path.write_text(dump_metadata(data))
    with pytest.raises(ValueError, match="no registered migration"):
        migrations.migrate(repo, 1)


def test_migration_preflight_dry_run_and_rollback(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit transform validates all files first and restores bytes after a failed write."""
    paths = [repo / "literature" / key / "document.yaml" for key in ("Fixture2000", "Fixture2001")]
    for path in paths:
        data = load_yaml(path.read_text())
        data["schema_version"] = 0
        path.write_text(dump_metadata(data))
    monkeypatch.setitem(migrations.MIGRATIONS, (0, 1), lambda _, data: data | {"schema_version": 1})
    originals = [path.read_bytes() for path in paths]
    assert len(migrations.migrate(repo, 1, dry_run=True)["changed"]) == 2
    assert [path.read_bytes() for path in paths] == originals
    real_write = migrations.atomic_write
    calls = 0

    def fail_second(path: Path, text: str) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated full disk")
        real_write(path, text)

    monkeypatch.setattr(migrations, "atomic_write", fail_second)
    with pytest.raises(OSError, match="full disk"):
        migrations.migrate(repo, 1)
    assert [path.read_bytes() for path in paths] == originals
    monkeypatch.setattr(migrations, "atomic_write", real_write)
    assert len(migrations.migrate(repo, 1)["changed"]) == 2
    assert all(load_yaml(path.read_text())["schema_version"] == 1 for path in paths)
