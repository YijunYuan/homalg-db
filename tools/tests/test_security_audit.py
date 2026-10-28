"""Repository workflow boundaries must survive routine CI maintenance."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
audit = runpy.run_path(str(ROOT / "tools/scripts/audit_security.py"))["audit_workflow"]


def test_repository_workflows_have_minimal_credentials_and_pinned_actions():
    findings = [item for path in (ROOT / ".github/workflows").glob("*.yml") for item in audit(path)]
    assert findings == []
    from homalg.schemas import load_yaml

    owner = load_yaml((ROOT / ".github/workflows/owner-approval.yml").read_text())
    checkout = owner["jobs"]["owner-approval"]["steps"][0]
    assert checkout["with"]["ref"] == "${{ env.BASE }}"


def test_audit_rejects_mutable_actions_inline_event_code_and_broad_tokens(tmp_path):
    workflow = tmp_path / "unsafe.yml"
    workflow.write_text("""permissions: write-all
on: [pull_request_target]
env:
  OPENAI_API_KEY: forbidden
jobs:
  check:
    permissions: write-all
    env:
      GH_TOKEN: broad
    steps:
      - uses: actions/checkout@main
      - run: echo '${{ github.event.pull_request.title }}'
""")
    failures = audit(workflow)
    assert len(failures) == 8
    assert any("immutable hash" in item for item in failures)
    assert any("inline shell" in item for item in failures)
    assert any("model API" in item for item in failures)
