"""Publication cleanup is constrained by the previous and replacement manifests."""

from homalg.sitedata import collect_obsolete_artifacts


def test_cleanup_removes_only_obsolete_manifest_owned_shards(tmp_path):
    old = "documents/Fixture2000." + "0" * 16 + ".json"
    kept = "documents/Fixture2000." + "1" * 16 + ".json"
    unknown = "documents/Fixture2000." + "2" * 16 + ".json"
    for relative in (old, kept, unknown, "notes.json"):
        target = tmp_path / relative
        target.parent.mkdir(exist_ok=True)
        target.write_text("{}")
    previous = {
        "documents": [{"files": {"document": old, "search_shard": kept}}],
        "index_file": "notes.json",
    }
    current = {"documents": [{"files": {"document": kept}}]}
    assert collect_obsolete_artifacts(tmp_path, previous, current) == [old]
    assert not (tmp_path / old).exists()
    assert all((tmp_path / relative).is_file() for relative in (kept, unknown, "notes.json"))


def test_cleanup_refuses_traversal_and_symlink_files_or_directories(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "data"
    root.mkdir()
    name = "Fixture2000." + "0" * 16 + ".json"
    (outside / name).write_text("private")
    (root / "documents").symlink_to(outside, target_is_directory=True)
    (root / "search").mkdir()
    (root / "search" / name).symlink_to(outside / name)
    previous = {
        "documents": [
            {"files": {"document": f"documents/{name}", "search_shard": f"search/{name}"}}
        ],
        "search_index_file": f"../outside/{name}",
    }
    assert collect_obsolete_artifacts(root, previous, {}) == []
    assert (outside / name).read_text() == "private"
    assert (root / "search" / name).is_symlink()
