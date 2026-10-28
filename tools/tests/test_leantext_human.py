"""Source lock context and human-command guard regressions."""

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from homalg.human import HumanApprovalRequired, record_human_change, require_human
from homalg.leantext import commands, sorry_count, statement_hashes
from homalg.review import lock_changes, review_blocks

SOURCE = """namespace Fixture2000
universe u
variable {R : Type u} [Ring R]
/-- **Theorem 1**. A synthetic statement. -/
@[simp] theorem first (x : R) : x = x := by
  rfl
section
variable [CommRing R]
/-- **Theorem 2**. An inner statement. -/
theorem inner (x : R) : x = x := by rfl
end
/-- **Theorem 3**. Another statement. -/
theorem last (x : R) : x = x := by rfl
end Fixture2000
"""


def test_statement_locks_include_context_but_ignore_proofs_and_attributes() -> None:
    """Binder context changes reopen statements; proof tactics and simp attributes do not."""
    initial = statement_hashes(SOURCE)
    assert set(initial) == {"Fixture2000.first", "Fixture2000.inner", "Fixture2000.last"}
    assert initial == statement_hashes(SOURCE.replace("@[simp] ", ""))
    assert initial == statement_hashes(SOURCE.replace("by rfl", "by\n  exact Eq.refl x"))
    changed = statement_hashes(SOURCE.replace("[Ring R]", "[CommRing R]"))
    assert all(initial[name] != changed[name] for name in initial)
    changed = statement_hashes(SOURCE.replace("variable [CommRing R]", "variable [Field R]"))
    assert initial["Fixture2000.inner"] != changed["Fixture2000.inner"]
    assert initial["Fixture2000.last"] == changed["Fixture2000.last"]


def test_definition_values_and_binder_defaults_are_in_interface() -> None:
    """Definition bodies matter, while theorem body separators skip binder defaults."""
    source = (
        "namespace Fixture2000\ndef value : Nat := 1\n"
        "theorem x (n : Nat := 1) : n = n := by rfl\nend Fixture2000"
    )
    original = statement_hashes(source)
    changed = statement_hashes(source.replace("Nat := 1\n", "Nat := 2\n"))
    assert original["Fixture2000.value"] != changed["Fixture2000.value"]
    assert commands(source)[1].statement.endswith(": n = n")


def test_one_command_context_does_not_leak() -> None:
    """`open ... in` affects precisely the following declaration's statement lock."""
    source = (
        "namespace Fixture2000\nopen Classical in\ntheorem a : True := by trivial\n"
        "theorem b : True := by trivial\nend Fixture2000"
    )
    original = statement_hashes(source)
    changed = statement_hashes(source.replace("open Classical in", "open Nat in"))
    assert original["Fixture2000.a"] != changed["Fixture2000.a"]
    assert original["Fixture2000.b"] == changed["Fixture2000.b"]


def test_latest_review_overrides_earlier_satisfactory_result() -> None:
    """Review history cannot be cherry-picked to obtain a statement lock."""
    blocks = review_blocks(
        "## source-fidelity — 2000-01-01 — first\nStatus: satisfactory\nVerdict: Good\n"
        "## source-fidelity — 2000-01-02 — second\nStatus: mismatch\nVerdict: Wrong assumptions\n"
    )
    assert blocks["source-fidelity"]["status"] == "mismatch"


def test_semantic_change_warns_and_source_context_change_errors() -> None:
    """The semantic closure hash catches changes that leave the root type unchanged."""
    name = "Fixture2000.first"
    authored = {
        "decls": [name],
        "fidelity": {
            "reviewed": {
                "decl_hashes": {
                    name: {
                        "statement_sha256": statement_hashes(SOURCE)[name],
                        "type_hash": "a",
                        "meaning_hash": "b",
                    }
                }
            }
        },
    }
    declarations = {name: {"type_hash": "a", "meaning_hash": "c"}}
    assert lock_changes(SOURCE, authored, declarations)[0]["severity"] == "warning"
    assert (
        lock_changes(SOURCE.replace("[Ring R]", "[Field R]"), authored, declarations)[0]["severity"]
        == "error"
    )


def test_sorry_literals_are_not_counted() -> None:
    """Only code tokens count, not source prose, string literals or names."""
    assert sorry_count('/-- sorry -/\ndef text := "sorry"\ntheorem «sorry» : True := by sorry') == 1


def test_human_guard_refuses_pipes_and_agent_sessions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An affirmative piped value or fabricated session environment cannot grant approval."""
    monkeypatch.setattr("homalg.human.sys.stdin", SimpleNamespace(isatty=lambda: False))
    with pytest.raises(HumanApprovalRequired, match="interactive"):
        require_human("test", tmp_path)
    monkeypatch.setattr("homalg.human.sys.stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setenv("ARCHON_HORIZON_SESSION", "")
    with pytest.raises(HumanApprovalRequired, match="interactive"):
        require_human("test", tmp_path)


def test_human_guard_refuses_active_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Guarded fields cannot race with an active session's scope rollback."""
    (tmp_path / ".archon-horizon").mkdir()
    (tmp_path / "config.yaml").write_text("workspace: {}")
    monkeypatch.delenv("ARCHON_HORIZON_SESSION", raising=False)
    monkeypatch.setattr("homalg.human.sys.stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("homalg.human.shutil.which", lambda _: "/bin/horizon")
    monkeypatch.setattr(
        "homalg.human.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, json.dumps({"processes": [{"pid": 42, "alive": True}]}), ""
        ),
    )
    with pytest.raises(HumanApprovalRequired, match="active"):
        require_human("test", tmp_path)


def test_human_change_is_immediately_recorded_in_ledger(tmp_path: Path) -> None:
    """The next session baseline can see the human change instead of reverting it."""
    ledger = tmp_path / ".archon-horizon/vcs/workspace.git"
    ledger.parent.mkdir(parents=True)
    subprocess.run(["git", "init", "--bare", str(ledger)], check=True, capture_output=True)
    prefix = ["git", "--git-dir", str(ledger), "--work-tree", str(tmp_path)]
    subprocess.run([*prefix, "config", "user.name", "Fixture Human"], check=True)
    subprocess.run([*prefix, "config", "user.email", "fixture@example.invalid"], check=True)
    path = tmp_path / "document.yaml"
    path.write_text("fixture: approved\n")
    record_human_change(tmp_path, "test", [path])
    result = subprocess.run(
        [*prefix, "show", "HEAD:document.yaml"], check=True, capture_output=True, text=True
    )
    assert result.stdout == "fixture: approved\n"


def test_multiline_strings_do_not_introduce_commands() -> None:
    """Command-looking text inside a raw string must never affect source scope."""
    source = (
        'namespace Fixture2000\ndef text := r#"\ndef fake := 1\n'
        'namespace False\n"#\nend Fixture2000'
    )
    assert [command.name for command in commands(source)] == ["Fixture2000.text"]


def test_same_line_docstring_is_attached_to_declaration() -> None:
    """Lean permits a declaration immediately after its docstring closing delimiter."""
    source = (
        "namespace Fixture2000\n/-- **Theorem 1**. By reflexivity. -/ "
        "theorem x : 1 = 1 := by rfl\nend Fixture2000"
    )
    assert commands(source)[0].docstring.startswith("**Theorem 1**")
