"""Fictional fixture reviews exercise atomic batch registration, never real approvals."""

import fcntl
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from homalg import leanexport, review
from homalg.cli import cli
from homalg.io import atomic_write_with_receipt, json_text
from homalg.nodeio import header_mapping, node_path, replace_header
from homalg.review_policy import valid_agent_review
from homalg.schemas import SchemaStore, load_yaml

IDS = ["Fixture2000.Thm_1", "Fixture2000.Lem_1"]
IDENTITY = {
    "by": "fictional-reviewer",
    "session": "fixture-review",
    "author_session": "fixture-author",
}
GOLDEN = Path(__file__).parent / "golden/fixture-export.json"


def report_path(repo: Path, node_id: str) -> Path:
    key, local = node_id.split(".")
    return repo / f"literature/{key}/reviews/{local}.md"


@pytest.fixture
def batch(repo: Path, monkeypatch: pytest.MonkeyPatch):
    policy = repo / "horizon/review-policy.yaml"
    policy.parent.mkdir(exist_ok=True)
    policy.write_text("schema_version: 1\nallow_independent_agent_reviews: true\n")
    for node_id in IDS:
        path = report_path(repo, node_id)
        path.parent.mkdir(exist_ok=True)
        path.write_text(
            "## source-fidelity — fictional independent review\n"
            "Session: fixture-review\nAuthor-session: fixture-author\n"
            "Status: satisfactory\nVerdict: Synthetic source comparison agrees.\n"
            "| Source | Lean |\n| --- | --- |\n| Fictional hypothesis | Same hypothesis |\n"
        )
    calls = []
    raw = json.loads(GOLDEN.read_text())

    def run(_repo, command):
        calls.append(command)
        return "" if command[1] == "build" else json_text(raw)

    # Only the external tool boundary is replaced: real export validation/merge runs.
    monkeypatch.setattr(leanexport, "run_tool", run)
    return repo, calls, raw


def originals(repo: Path) -> dict[Path, bytes]:
    return {node_path(repo, node_id): node_path(repo, node_id).read_bytes() for node_id in IDS}


def assert_unchanged(before: dict[Path, bytes]) -> None:
    assert all(path.read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize("by", ["run/session/reviewer", "a" * 40, "reviewer_1", "-reviewer"])
def test_bad_reviewer_identifier_rejected_before_freeze_or_build(batch, monkeypatch, by):
    repo, calls, _ = batch
    before = originals(repo)

    def unexpected(*args, **kwargs):
        pytest.fail("Invalid reviewer identifier must fail before expensive input freezing")

    monkeypatch.setattr(leanexport, "compilation_inputs", unexpected)
    with pytest.raises(ValueError, match="short reviewer identifier"):
        review.review_fidelity_batch(repo, IDS, **(IDENTITY | {"by": by}))
    assert not calls
    assert_unchanged(before)


def test_batch_builds_once_and_commits_every_compiled_hash(batch) -> None:
    repo, calls, _ = batch
    snapshot = review.freeze_fidelity_inputs(repo, IDS)
    stable = review.freeze_authoring_inputs(repo)
    locks = review.review_fidelity_batch(repo, IDS, snapshot=snapshot, **IDENTITY)
    assert [command[1] for command in calls] == ["build", "exe"]
    assert list(locks) == IDS
    for node_id, lock in locks.items():
        assert valid_agent_review(lock)
        assert lock["decl_hashes"]
        assert header_mapping(node_path(repo, node_id).read_text())["fidelity"]["reviewed"] == lock
    assert review.freeze_authoring_inputs(repo) == stable
    journal = next((repo / ".archon-horizon/cache/fidelity-transactions").glob("*.json"))
    assert json.loads(journal.read_text())["status"] == "committed"


@pytest.mark.parametrize("failure", ["status", "session", "author", "human", "honesty"])
def test_later_bad_report_or_protected_record_writes_nothing(batch, failure: str) -> None:
    repo, calls, _ = batch
    path = report_path(repo, IDS[1])
    text = path.read_text()
    if failure == "human":
        source = node_path(repo, IDS[1])
        text = source.read_text()
        metadata = header_mapping(text)
        metadata["fidelity"]["reviewed"] = {
            "kind": "human",
            "by": "fictional-human",
            "on": "2026-10-28",
            "status": "satisfactory",
            "decl_hashes": {},
        }
        source.write_text(replace_header(text, metadata, SchemaStore(repo / "schema")))
    elif failure == "honesty":
        path.write_text(
            text + "\n## honesty — latest\nStatus: mismatch\nVerdict: Hidden premise.\n"
        )
    else:
        old, new = {
            "status": ("satisfactory", "mismatch"),
            "session": ("Session: fixture-review", "Session: other-review"),
            "author": ("Author-session: fixture-author", "Author-session: other-author"),
        }[failure]
        path.write_text(text.replace(old, new))
    before = originals(repo)
    with pytest.raises(ValueError):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert_unchanged(before)
    assert calls == []


def test_missing_later_export_declaration_does_not_lock_first_node(batch) -> None:
    repo, calls, raw = batch
    next(item for item in raw["modules"] if item["module"] == "HomAlg.Fixture2000.Lem_1")[
        "decls"
    ] = []
    before = originals(repo)
    with pytest.raises(ValueError, match="main declaration"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert_unchanged(before)
    assert [command[1] for command in calls] == ["build", "exe"]


@pytest.mark.parametrize(
    "target",
    [
        "HomAlg/Fixture2000/Thm_1.lean",
        "HomAlg/Fixture2000/Def_1.lean",
        "lean-toolchain",
        "literature/Fixture2000/document.yaml",
        "literature/Fixture2000/reviews/Lem_1.md",
        ".lake/packages/local/Dependency.lean",
        "schema/common.schema.json",
    ],
)
def test_frozen_snapshot_rejects_source_dependencies_toolchain_and_reports(
    batch, target: str
) -> None:
    repo, calls, _ = batch
    path = repo / target
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("-- Fictional local dependency\n")
    snapshot = review.freeze_fidelity_inputs(repo, IDS)
    path.write_text(path.read_text() + "\n")
    before = originals(repo)
    with pytest.raises(ValueError, match="stale"):
        review.review_fidelity_batch(repo, IDS, snapshot=snapshot, **IDENTITY)
    assert_unchanged(before)
    assert calls == []


@pytest.mark.parametrize(
    "target",
    ["HomAlg/Fixture2000/Def_1.lean", "lean-toolchain", "literature/Fixture2000/reviews/Lem_1.md"],
)
@pytest.mark.parametrize("restore", [False, True])
def test_input_changes_during_export_even_aba_are_rejected(
    batch, monkeypatch, target, restore
) -> None:
    repo, _, raw = batch
    before = originals(repo)
    path = repo / target

    def mutate(_repo, command):
        if command[1] == "exe":
            old = path.read_bytes()
            path.write_bytes(old + b"\n")
            if restore:
                path.write_bytes(old)
        return json_text(raw)

    monkeypatch.setattr(leanexport, "run_tool", mutate)
    with pytest.raises(ValueError, match="changed"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert_unchanged(before)


def test_shared_workspace_lock_covers_export_and_all_header_writes(batch, monkeypatch) -> None:
    repo, calls, _ = batch
    observed = []

    def guarded_write(path, text):
        if path in originals(repo):
            lockpath = repo / ".archon-horizon/cache/checks/workspace.lock"
            with lockpath.open("a") as stream:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            observed.append(path)
        receipt = atomic_write_with_receipt(path, text)
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", guarded_write)
    review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert len(observed) == 2 and len(calls) == 2
    # The outer lock has been released when registration returns.
    with (repo / ".archon-horizon/cache/checks/workspace.lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize("write_then_fail", [False, True])
def test_later_write_failure_rolls_back_only_our_actual_writes(
    batch, monkeypatch, write_then_fail
) -> None:
    repo, _, _ = batch
    before = originals(repo)
    last = node_path(repo, IDS[-1])

    def fail(path, text):
        if path == last:
            if write_then_fail:
                receipt = atomic_write_with_receipt(path, text)
            raise OSError("Fictional disk failure")
        receipt = atomic_write_with_receipt(path, text)
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", fail)
    expected = "recovery-required" if write_then_fail else "rolled-back"
    with pytest.raises(ValueError, match=expected):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert node_path(repo, IDS[0]).read_bytes() == before[node_path(repo, IDS[0])]
    if write_then_fail:
        # A failed writer may have replaced the file, but supplied no success receipt.
        # Do not infer ownership from bytes alone or overwrite a possible other writer.
        assert header_mapping(last.read_text())["fidelity"].get("reviewed")
    else:
        assert_unchanged(before)
    journals = list((repo / ".archon-horizon/cache/fidelity-transactions").glob("*.json"))
    assert len(journals) == 1
    assert json.loads(journals[0].read_text())["status"] == expected


def test_concurrent_later_source_edit_is_preserved_and_first_lock_rolled_back(
    batch, monkeypatch
) -> None:
    repo, _, _ = batch
    before = originals(repo)
    first, second = [node_path(repo, node_id) for node_id in IDS]
    changed = before[second] + b"\n-- Independent concurrent edit\n"

    def edit(path, text):
        receipt = atomic_write_with_receipt(path, text)
        if path == first:
            second.write_bytes(changed)
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", edit)
    with pytest.raises(ValueError, match="rolled-back"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert first.read_bytes() == before[first]
    assert second.read_bytes() == changed


def test_concurrent_edit_to_written_node_is_never_overwritten_and_blocks_next_batch(
    batch, monkeypatch
) -> None:
    repo, _, _ = batch
    first = node_path(repo, IDS[0])
    other = originals(repo)[node_path(repo, IDS[1])]

    def edit(path, text):
        receipt = atomic_write_with_receipt(path, text)
        if path == first:
            path.write_text(text + "\n-- New independent edit after replacement\n")
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", edit)
    with pytest.raises(ValueError, match="recovery-required"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert first.read_text().endswith("-- New independent edit after replacement\n")
    assert node_path(repo, IDS[1]).read_bytes() == other
    with pytest.raises(ValueError, match="requires recovery"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)


def test_dependency_edit_between_header_writes_rolls_back_all_locks(batch, monkeypatch) -> None:
    repo, _, _ = batch
    before = originals(repo)
    dependency = repo / "HomAlg/Fixture2000/Def_1.lean"

    def edit(path, text):
        receipt = atomic_write_with_receipt(path, text)
        if path == node_path(repo, IDS[1]):
            dependency.write_text(dependency.read_text() + "\n-- Concurrent dependency edit\n")
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", edit)
    with pytest.raises(ValueError, match="rolled-back"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert_unchanged(before)
    assert "Concurrent dependency edit" in dependency.read_text()


@pytest.mark.parametrize("field", ["title", "statement", "proof", "code", "human-record"])
def test_author_delivery_fingerprint_retains_all_meaningful_source_and_human_fields(
    batch, field
) -> None:
    repo, _, _ = batch
    path = node_path(repo, IDS[0])
    original = path.read_text()
    expected = review.authoring_source_fingerprint(original)
    metadata = header_mapping(original)
    if field == "title":
        metadata["title"] += " changed"
        changed = replace_header(original, metadata, SchemaStore(repo / "schema"))
    elif field == "human-record":
        metadata["fidelity"]["reviewed"] = {
            "kind": "human",
            "by": "fictional-human",
            "on": "2026-10-28",
            "status": "satisfactory",
            "decl_hashes": {},
        }
        changed = replace_header(original, metadata, SchemaStore(repo / "schema"))
    elif field in {"statement", "proof"}:
        changed = original.replace(
            f"## {field.title()}\n", f"## {field.title()}\nChanged evidence.\n"
        )
    else:
        changed = original + "\n-- Changed Lean source\n"
    assert review.authoring_source_fingerprint(changed) != expected


def test_batch_cli_snapshot_and_registration_are_agent_only(batch) -> None:
    repo, calls, _ = batch
    runner = CliRunner()
    snapshot = repo / "build/fidelity-inputs.json"
    result = runner.invoke(
        cli, ["review-fidelity-snapshot", "--repo", str(repo), *IDS, "--out", str(snapshot)]
    )
    assert result.exit_code == 0, result.output
    assert calls == []
    args = [
        "review-fidelity-batch",
        "--repo",
        str(repo),
        "--json",
        *IDS,
        "--by",
        IDENTITY["by"],
        "--session",
        IDENTITY["session"],
        "--author-session",
        IDENTITY["author_session"],
        "--snapshot",
        str(snapshot),
    ]
    result = runner.invoke(cli, args + ["--human"])
    assert result.exit_code == 2
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.output
    assert set(json.loads(result.output)["data"]["locks"]) == set(IDS)
    assert len(calls) == 2


@pytest.mark.parametrize("bad_ids", [[], [IDS[0], IDS[0]], [IDS[0], "Fixture2001.Def_1"]])
def test_batch_rejects_empty_duplicate_or_cross_document_scope(batch, bad_ids) -> None:
    repo, calls, _ = batch
    before = originals(repo)
    with pytest.raises(ValueError):
        review.review_fidelity_batch(repo, bad_ids, **IDENTITY)
    assert calls == []
    assert_unchanged(before)


def test_self_review_and_policy_disable_are_rejected_before_export(batch) -> None:
    repo, calls, _ = batch
    before = originals(repo)
    with pytest.raises(ValueError, match="distinct"):
        review.review_fidelity_batch(repo, IDS, **(IDENTITY | {"author_session": "fixture-review"}))
    (repo / "horizon/review-policy.yaml").write_text(
        "schema_version: 1\nallow_independent_agent_reviews: false\n"
    )
    with pytest.raises(ValueError, match="disabled"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert calls == []
    assert_unchanged(before)


def test_path_dependency_and_selected_executable_are_bound(batch, tmp_path, monkeypatch) -> None:
    repo, calls, _ = batch
    dependency = tmp_path / "external-package"
    dependency.mkdir()
    source = dependency / "Imported.lean"
    source.write_text("def fictionalDependency := 1\n")
    (repo / "lake-manifest.json").write_text(
        json_text(
            {
                "packages": [{"type": "path", "name": "external", "dir": str(dependency)}],
            }
        )
    )
    binary = repo / "fake-bin/lake"
    binary.parent.mkdir()
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    monkeypatch.setenv("PATH", "fake-bin")
    snapshot = review.freeze_fidelity_inputs(repo, IDS)
    assert str(source) in snapshot["compilation"]["files"]
    assert snapshot["compilation"]["executables"]["lake"] == str(binary)
    binary.write_text("#!/bin/sh\nexit 1\n")
    with pytest.raises(ValueError, match="stale"):
        review.review_fidelity_batch(repo, IDS, snapshot=snapshot, **IDENTITY)
    assert calls == []


def test_export_artifact_modification_after_build_is_rejected(batch, monkeypatch) -> None:
    repo, _, _ = batch
    before = originals(repo)
    original = review.statement_hashes

    def mutate(source):
        value = original(source)
        path = repo / "literature/Fixture2000/nodes.json"
        path.write_text(path.read_text() + "\n")
        return value

    monkeypatch.setattr(review, "statement_hashes", mutate)
    with pytest.raises(ValueError, match="Compiled export changed"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert_unchanged(before)


def test_concurrent_thread_waits_until_batch_registration_finishes(batch, monkeypatch) -> None:
    import threading

    repo, _, _ = batch
    started = threading.Event()
    acquired = threading.Event()
    finished = threading.Event()
    observations = []

    def competitor():
        started.set()
        with leanexport.workspace_lock(repo):
            observations.extend(
                bool(
                    header_mapping(node_path(repo, node_id).read_text())["fidelity"].get("reviewed")
                )
                for node_id in IDS
            )
            acquired.set()
        finished.set()

    thread = threading.Thread(target=competitor)

    def register(path, text):
        if path == node_path(repo, IDS[0]):
            thread.start()
            assert started.wait(2)
            assert not acquired.wait(0.03)
        receipt = atomic_write_with_receipt(path, text)
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", register)
    review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert finished.wait(2)
    thread.join(2)
    assert observations == [True, True]


def test_frozen_author_delivery_detects_dependency_and_toolchain_changes(batch) -> None:
    repo, _, _ = batch
    before = review.freeze_authoring_inputs(repo)
    dependency = repo / "HomAlg/Fixture2000/Def_1.lean"
    original = dependency.read_text()
    dependency.write_text(original + "\n-- New dependency body\n")
    assert review.freeze_authoring_inputs(repo) != before
    dependency.write_text(original)
    assert review.freeze_authoring_inputs(repo) == before
    toolchain = repo / "lean-toolchain"
    toolchain.write_text(toolchain.read_text() + "\n")
    assert review.freeze_authoring_inputs(repo) != before


def test_policy_change_during_preflight_cannot_fall_back_to_legacy_review(
    batch, monkeypatch
) -> None:
    repo, calls, _ = batch
    before = originals(repo)
    original = review._prepare_review

    def change_policy(*args, **kwargs):
        result = original(*args, **kwargs)
        (repo / "horizon/review-policy.yaml").write_text(
            "schema_version: 1\nallow_independent_agent_reviews: false\n"
        )
        return result

    monkeypatch.setattr(review, "_prepare_review", change_policy)
    with pytest.raises(ValueError, match="changed"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert_unchanged(before)
    assert calls == []


@pytest.mark.parametrize(
    "destination", ["outside", "existing", "build-symlink", "escaping-symlink"]
)
def test_snapshot_cli_refuses_to_overwrite_or_escape_ignored_build(
    batch, tmp_path, destination
) -> None:
    repo, calls, _ = batch
    outside = tmp_path / "outside-output"
    outside.mkdir()
    build = repo / "build"
    if destination == "outside":
        target = node_path(repo, IDS[0])
    elif destination == "existing":
        build.mkdir(exist_ok=True)
        target = build / "previous.json"
        target.write_text("Earlier evidence\n")
    elif destination == "build-symlink":
        build.symlink_to(outside, target_is_directory=True)
        target = build / "snapshot.json"
    else:
        build.mkdir(exist_ok=True)
        (build / "escape").symlink_to(outside, target_is_directory=True)
        target = build / "escape/snapshot.json"
    before = target.read_bytes() if target.exists() else None
    result = CliRunner().invoke(
        cli, ["review-fidelity-snapshot", "--repo", str(repo), *IDS, "--out", str(target)]
    )
    assert result.exit_code == 2, result.output
    assert (target.read_bytes() if target.exists() else None) == before
    assert calls == []


def test_author_fingerprint_does_not_exclude_malformed_agent_records(batch) -> None:
    repo, _, _ = batch
    path = node_path(repo, IDS[0])
    source = path.read_text()
    metadata = header_mapping(source)
    metadata["fidelity"]["reviewed"] = {
        "kind": "agent",
        "by": "fictional-reviewer",
        "session": "fixture-review",
        "author_session": "fixture-author",
        "on": "2026-10-28",
        "status": "satisfactory",
    }
    # Deliberately malformed test input, not serialized through the strict writer.
    from homalg.documents import dump_metadata
    from homalg.headers import parse_header

    header = parse_header(source)
    opening = source.index("```yaml node", header.start) + len("```yaml node")
    closing = source.index("```", opening)
    malformed = source[:opening] + "\n" + dump_metadata(metadata) + source[closing:]
    assert review.authoring_source_fingerprint(malformed) != review.authoring_source_fingerprint(
        source
    )


def source_context(repo: Path) -> tuple[Path, Path, Path]:
    """Small, explicitly fictional source evidence for fingerprint tests."""
    directory = repo / "literature/.private/Fixture2000"
    (directory / "tex").mkdir(parents=True)
    page = directory / "tex/page-0002.tex"
    page.write_text("Fictional source sentence.\n")
    distant = directory / "tex/page-0099.tex"
    distant.write_text("Unrelated distant source.\n")
    manifest = directory / "transcription.yaml"
    manifest.write_text(
        json_text(
            {
                "schema_version": 1,
                "doc_key": "Fixture2000",
                "pdf_sha256": "0" * 64,
                "pages": {
                    "0002": {"status": "reviewed", "file_sha256": "1" * 64},
                    "0099": {"status": "todo"},
                },
            }
        )
    )
    return page, distant, manifest


@pytest.mark.parametrize(
    "target",
    [
        "literature/Fixture2000/inventory.yaml",
        "docs/fixtures/Fixture2000.md",
        "private-page",
        "private-manifest",
    ],
)
def test_context_inputs_bind_inventory_and_private_source(batch, target) -> None:
    repo, calls, _ = batch
    page, _, manifest = source_context(repo)
    path = {"private-page": page, "private-manifest": manifest}.get(target, repo / target)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]\n")
    frozen = review.freeze_fidelity_inputs(repo, IDS)
    delivery = review.freeze_authoring_inputs(repo, IDS)
    if target.endswith("inventory.yaml"):
        # The inventory binds the node's own pages, not unrelated entries or comments.
        data = load_yaml(path.read_text()) or {}
        data.setdefault("pages", {})["0001"] = {"complete": False, "items": []}
        path.write_text(json_text(data))
    else:
        path.write_text(path.read_text() + "\n# Changed input\n")
    assert (
        review.freeze_authoring_inputs(repo, IDS) != delivery
        if target != "private-manifest"
        else True
    )
    with pytest.raises(ValueError, match="stale"):
        review.review_fidelity_batch(repo, IDS, snapshot=frozen, **IDENTITY)
    assert calls == []


def test_append_only_taxonomy_does_not_invalidate_a_delivery(batch) -> None:
    repo, _, _ = batch
    delivery = review.freeze_authoring_inputs(repo, IDS)
    path = repo / "taxonomy/tags.yaml"
    path.write_text(path.read_text() + "\n# Appended tag elsewhere\n")
    assert review.freeze_authoring_inputs(repo, IDS) == delivery


def test_author_source_scope_ignores_distant_transcription_updates_but_final_snapshot_is_strict(
    batch,
) -> None:
    repo, _, _ = batch
    page, distant, manifest = source_context(repo)
    delivery = review.freeze_authoring_inputs(repo, IDS)
    frozen = review.freeze_fidelity_inputs(repo, IDS)
    assert 2 in delivery["context"]["source_pages"]["Fixture2000"]
    assert 99 not in delivery["context"]["source_pages"]["Fixture2000"]
    distant.write_text("New distant page bytes\n")
    data = json.loads(manifest.read_text())
    data["pages"]["0099"] = {"status": "transcribed"}
    manifest.write_text(json_text(data))
    assert review.freeze_authoring_inputs(repo, IDS) == delivery
    assert review.freeze_fidelity_inputs(repo, IDS) != frozen
    data["pages"]["0002"]["status"] = "transcribed"
    manifest.write_text(json_text(data))
    assert review.freeze_authoring_inputs(repo, IDS) != delivery
    assert "literature/.private/Fixture2000/tex/page-0002.tex" in frozen["context"]["files"]


def test_source_context_uses_printed_page_offset_and_local_import_dependencies(batch) -> None:
    repo, _, _ = batch
    document = repo / "literature/Fixture2000/document.yaml"
    data = json.loads(document.read_text())
    data["pdf"] = {"page_offset": 22}
    document.write_text(json_text(data))
    context = review.authoring_context_inputs(repo, [IDS[0]])
    assert context["source_pages"]["Fixture2000"] == [23, 24]
    assert "Fixture2000.Def_1" in context["node_ids"]
    assert any(name.endswith("page-0024.tex") for name in context["files"])


def test_workflow_snapshot_binds_actual_delivery_author(batch) -> None:
    repo, calls, _ = batch
    frozen = review.freeze_fidelity_inputs(repo, IDS, expected_author_session="fixture-author")
    assert frozen["expected_author_session"] == "fixture-author"
    # The reports could consistently name another author; the delivery still cannot.
    for node_id in IDS:
        path = report_path(repo, node_id)
        path.write_text(path.read_text().replace("fixture-author", "other-author"))
    with pytest.raises(ValueError, match="author session differs"):
        review.review_fidelity_batch(
            repo, IDS, snapshot=frozen, **(IDENTITY | {"author_session": "other-author"})
        )
    assert calls == []
    for node_id in IDS:
        path = report_path(repo, node_id)
        path.write_text(path.read_text().replace("other-author", "fixture-author"))
    fresh = review.freeze_fidelity_inputs(repo, IDS, expected_author_session="fixture-author")
    review.review_fidelity_batch(repo, IDS, snapshot=fresh, **IDENTITY)
    assert len(calls) == 2


@pytest.mark.parametrize("invalid", ["", " ", 1, False])
def test_snapshot_rejects_empty_or_non_string_author_binding(batch, invalid) -> None:
    repo, _, _ = batch
    with pytest.raises(ValueError, match="nonempty actual session"):
        review.freeze_fidelity_inputs(repo, IDS, expected_author_session=invalid)


def test_aba_of_later_node_between_writes_does_not_get_absorbed_into_our_snapshot(
    batch, monkeypatch
):
    repo, _, _ = batch
    before = originals(repo)
    first, second = [node_path(repo, node_id) for node_id in IDS]

    def edit_restore(path, text):
        receipt = atomic_write_with_receipt(path, text)
        if path == first:
            second.write_bytes(before[second] + b"\n-- Concurrent edit\n")
            second.write_bytes(before[second])
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", edit_restore)
    with pytest.raises(ValueError, match="rolled-back"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert_unchanged(before)


def test_rollback_does_not_own_an_external_same_bytes_replacement(batch, monkeypatch):
    repo, _, _ = batch
    before = originals(repo)
    first, second = [node_path(repo, node_id) for node_id in IDS]

    def replace_then_fail(path, text):
        if path == second:
            # Externally replace the first file with identical bytes and a new inode.
            temporary = first.with_suffix(".external")
            temporary.write_bytes(first.read_bytes())
            temporary.replace(first)
            raise OSError("Fictional later write failure")
        receipt = atomic_write_with_receipt(path, text)
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", replace_then_fail)
    with pytest.raises(ValueError, match="recovery-required"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert header_mapping(first.read_text())["fidelity"].get("reviewed")
    assert second.read_bytes() == before[second]


def test_context_rejects_unsupported_multi_import_header_instead_of_omitting_context(batch) -> None:
    repo, _, _ = batch
    path = node_path(repo, IDS[0])
    path.write_text(
        path.read_text().replace(
            "import HomAlg.Fixture2000.Def_1",
            "import HomAlg.Fixture2000.Def_1 HomAlg.Fixture2001.Def_1",
        )
    )
    # The repository's header contract currently requires one import per line.
    # This legal Lean spelling is rejected, never accepted with incomplete context.
    with pytest.raises(ValueError, match="header must follow imports"):
        review.authoring_context_inputs(repo, [IDS[0]])


def test_replaced_workspace_lock_fails_closed_at_nested_entry(batch) -> None:
    repo, _, _ = batch
    with pytest.raises(ValueError, match="lock identity changed"):
        with leanexport.workspace_lock(repo):
            path = repo / ".archon-horizon/cache/checks/workspace.lock"
            replacement = path.with_suffix(".replacement")
            replacement.write_text("")
            replacement.replace(path)
            with leanexport.workspace_lock(repo):
                pytest.fail("Nested entry accepted a replaced lock inode")


def test_replaced_workspace_lock_during_build_cannot_publish_locks(batch, monkeypatch) -> None:
    repo, _, raw = batch
    before = originals(repo)

    def replace_lock(_repo, command):
        if command[1] == "exe":
            path = repo / ".archon-horizon/cache/checks/workspace.lock"
            replacement = path.with_suffix(".replacement")
            replacement.write_text("")
            replacement.replace(path)
        return json_text(raw)

    monkeypatch.setattr(leanexport, "run_tool", replace_lock)
    with pytest.raises(ValueError, match="lock identity changed"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert_unchanged(before)
    assert not (repo / "build/lean-export-Fixture2000.json").exists()


def test_external_same_bytes_replace_before_writer_returns_is_not_our_receipt(batch, monkeypatch):
    repo, _, _ = batch
    before = originals(repo)
    first, second = [node_path(repo, node_id) for node_id in IDS]
    external_identity = []

    def interpose(path, text):
        receipt = atomic_write_with_receipt(path, text)
        if path == first:
            temporary = first.with_suffix(".external")
            temporary.write_bytes(first.read_bytes())
            temporary.replace(first)
            external_identity.append(first.stat().st_ino)
        return receipt

    monkeypatch.setattr(review, "atomic_write_with_receipt", interpose)
    with pytest.raises(ValueError, match="recovery-required"):
        review.review_fidelity_batch(repo, IDS, **IDENTITY)
    assert first.stat().st_ino == external_identity[0]
    assert second.read_bytes() == before[second]


def test_atomic_receipt_is_from_owned_fd_and_preserves_explicit_mode(tmp_path, monkeypatch):
    from homalg import io

    target = tmp_path / "target.txt"
    target.write_text("old\n")
    target.chmod(0o640)
    receipt = io.atomic_bytes_with_receipt(target, b"new\n")
    assert receipt == leanexport.file_fingerprint(target)
    assert target.stat().st_mode & 0o777 == 0o640
    receipt = io.atomic_bytes_with_receipt(target, b"executable\n", mode=0o755)
    assert receipt == leanexport.file_fingerprint(target)
    assert target.stat().st_mode & 0o777 == 0o755
    original_replace = io.os.replace
    external_identity = []

    def replace_then_external(source, destination):
        original_replace(source, destination)
        if destination == target:
            external = tmp_path / "external.txt"
            external.write_bytes(target.read_bytes())
            original_replace(external, target)
            external_identity.append(target.stat().st_ino)

    monkeypatch.setattr(io.os, "replace", replace_then_external)
    with pytest.raises(ValueError, match="ownership changed"):
        io.atomic_bytes_with_receipt(target, b"replacement\n")
    assert target.stat().st_ino == external_identity[0]
    assert target.read_bytes() == b"replacement\n"
