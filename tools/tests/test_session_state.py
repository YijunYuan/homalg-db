"""Inside an isolated session checkout, unchanged nodes use the canonical compiled facts."""

import shutil
from pathlib import Path

from homalg.headers import parse_header
from homalg.runtime_state import document_state
from homalg.schemas import load_yaml

ROOT = Path(__file__).resolve().parents[2]
KEY = "Fixture2000"


def checkout(main: Path) -> Path:
    """The layout the engine creates: a source copy without build/ evidence."""
    (main / "build").mkdir(exist_ok=True)
    golden = ROOT / "tools/tests/golden/fixture-export.json"
    shutil.copyfile(golden, main / "build/lean-export.json")
    path = main / ".archon-horizon/session-worktrees" / ("c" * 32)
    shutil.copytree(main, path, ignore=shutil.ignore_patterns(".archon-horizon", "build"))
    return path


def approximate(state: dict) -> set[str]:
    return {node["id"] for node in state["nodes"] if node["approx"]}


def test_session_checkout_reads_canonical_facts_for_unchanged_closures(repo, monkeypatch):
    session = checkout(repo)
    # Outside an engine session the checkout's missing export stays approximate.
    monkeypatch.delenv("HOMALG_SESSION_MAIN_ROOT", raising=False)
    assert document_state(session, KEY)["approx"]
    monkeypatch.setenv("HOMALG_SESSION_MAIN_ROOT", str(repo))
    assert approximate(document_state(session, KEY)) == approximate(document_state(repo, KEY))
    assert not document_state(session, KEY)["approx"]
    # A node the session edited, and every node importing it, stays approximate.
    source = session / f"HomAlg/{KEY}/Def_1.lean"
    source.write_text(source.read_text() + "\n-- edited in the session\n")
    stale = approximate(document_state(session, KEY))
    assert {f"{KEY}.Def_1", f"{KEY}.Thm_1"} <= stale
    assert f"{KEY}.Def_2" not in stale
    # A later canonical change to an unchanged node is not borrowed either.
    canonical = repo / f"HomAlg/{KEY}/Def_2.lean"
    canonical.write_text(canonical.read_text() + "\n-- landed by another session\n")
    assert f"{KEY}.Def_2" in approximate(document_state(session, KEY))


def test_memoized_parsers_return_independent_copies():
    text = "a:\n  b: [1, 2]\n"
    first = load_yaml(text)
    first["a"]["b"].append(3)
    assert load_yaml(text) == {"a": {"b": [1, 2]}}
    source = (ROOT / f"HomAlg/{KEY}/Def_1.lean").read_text()
    header = parse_header(source)
    header.metadata["deps"]["statement"].append("Mutated.Node")
    assert "Mutated.Node" not in parse_header(source).metadata["deps"]["statement"]
