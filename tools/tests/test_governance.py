"""Governance contract tests without GitHub writes."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "governance.py"
spec = importlib.util.spec_from_file_location("governance", SCRIPT)
assert spec and spec.loader
governance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(governance)


class FakeGitHub:
    """Model create/update behavior to check idempotent resource management."""

    def __init__(self) -> None:
        self.rulesets: dict[int, dict[str, Any]] = {}
        self.labels: dict[str, dict[str, Any]] = {}
        self.pages: dict[str, Any] | None = None
        self.variable: dict[str, Any] | None = None
        self.writes: list[tuple[str, str]] = []

    def api(
        self,
        method: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
        **_: Any,
    ) -> Any:
        """Return stored resources and reject unexpected calls."""
        base = "repos/octocat/homalg-db"
        if method != "GET":
            self.writes.append((method, endpoint))
        if endpoint == base:
            return {"owner": {"type": "User"}, "archived": False}
        if endpoint == f"{base}/rulesets":
            if method == "GET":
                return list(self.rulesets.values())
            assert method == "POST" and payload
            key = len(self.rulesets) + 1
            self.rulesets[key] = {**copy.deepcopy(payload), "id": key}
            return self.rulesets[key]
        if endpoint.startswith(f"{base}/rulesets/"):
            key = int(endpoint.rsplit("/", 1)[1])
            if method == "PUT":
                assert payload
                self.rulesets[key] = {**copy.deepcopy(payload), "id": key}
            return self.rulesets[key]
        if endpoint == f"{base}/actions/permissions/workflow":
            return payload
        if endpoint == f"{base}/pages":
            if method != "GET":
                self.pages = payload
            return self.pages
        if "/actions/variables" in endpoint:
            if method != "GET":
                self.variable = payload
            return self.variable
        if endpoint == f"{base}/labels" and method == "GET":
            return list(self.labels.values())
        if "/labels" in endpoint:
            assert payload
            self.labels[payload["name"]] = payload
            return payload
        raise AssertionError((method, endpoint, payload))


def test_required_checks_and_exceptions() -> None:
    """Owner protection remains on infrastructure and relation review decisions."""
    plan = governance.build_plan("octocat/homalg-db")
    owners = plan["codeowners"].splitlines()
    assert "* @octocat" in owners
    assert "/literature/*/document.yaml" in owners
    assert "/HomAlg/" in owners
    assert owners[-1] == "/taxonomy/relations/_reviews.yaml @octocat"
    checks = plan["rulesets"][0]["rules"][-1]["parameters"]["required_status_checks"]
    assert {check["context"] for check in checks} == {"gate", "owner-approval"}
    assert plan["rulesets"][1]["conditions"]["ref_name"]["include"] == ["refs/heads/status/**"]
    assert plan["rulesets"][0]["bypass_actors"][0]["actor_id"] == 5


def test_org_mode_uses_team() -> None:
    """Organization ownership uses a team while HOMALG_OWNER remains a person."""
    plan = governance.build_plan("example/homalg-db", "org", "octocat", 42)
    assert "* @example/homalg-maintainers" in plan["codeowners"]
    assert plan["variable"]["value"] == "octocat"
    assert all(
        ruleset["bypass_actors"]
        == [{"actor_type": "Team", "actor_id": 42, "bypass_mode": "pull_request"}]
        for ruleset in plan["rulesets"]
    )


@pytest.mark.parametrize("repository", ["bad", "owner/repo/extra", "owner/repo;echo", "owner/a b"])
def test_repository_argument_is_validated(repository: str) -> None:
    """A repository argument must be a literal owner/name pair."""
    with pytest.raises(ValueError):
        governance.build_plan(repository)


def test_org_configuration_is_explicit() -> None:
    """Do not infer a human identity or team ID for an organization."""
    with pytest.raises(ValueError, match="org mode"):
        governance.build_plan("example/homalg-db", "org")
    with pytest.raises(ValueError, match="must equal"):
        governance.build_plan("octocat/homalg-db", owner_login="someone-else")


def test_applying_twice_updates_existing_resources() -> None:
    """Repeated setup must not duplicate rulesets, labels, Pages, or variables."""
    plan = governance.build_plan("octocat/homalg-db")
    github = FakeGitHub()
    governance.apply_plan(plan, github)
    assert len(github.rulesets) == 2
    assert len(github.labels) == 12
    first_writes = len(github.writes)
    governance.apply_plan(plan, github)
    assert len(github.rulesets) == 2
    assert len(github.labels) == 12
    assert all(method != "POST" for method, _ in github.writes[first_writes:])


def test_default_command_is_offline(monkeypatch: pytest.MonkeyPatch, capsys: Any) -> None:
    """Previewing governance must never invoke gh or render a file."""

    def forbidden(*_: Any, **__: Any) -> None:
        raise AssertionError("preview attempted a side effect")

    monkeypatch.setattr(governance.subprocess, "run", forbidden)
    monkeypatch.setattr(governance, "write_codeowners", forbidden)
    assert governance.main(["--repository", "octocat/homalg-db"]) == 0
    assert '"repository": "octocat/homalg-db"' in capsys.readouterr().out
