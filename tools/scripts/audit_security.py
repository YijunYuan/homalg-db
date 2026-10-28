"""Check workflow security invariants locally without changing external settings."""

import argparse
import re
from pathlib import Path

from homalg.schemas import load_yaml

TOKEN_NAMES = {"GH_TOKEN", "GITHUB_TOKEN"}
MODEL_SECRET = re.compile(r"(?:OPENAI|ANTHROPIC|GEMINI|COHERE|MISTRAL)_API_KEY")


def audit_workflow(path: Path) -> list[str]:
    text = path.read_text()
    data = load_yaml(text)
    findings = []

    def finding(message):
        findings.append(f"{path.name}: {message}")

    if data.get("permissions") != {}:
        finding("workflow must deny permissions by default")
    events = data.get("on", {})
    if "pull_request_target" in events:
        finding("pull_request_target is outside the repository trust model")
    if MODEL_SECRET.search(text):
        finding("model API keys must not enter CI")
    if TOKEN_NAMES & set(data.get("env", {})):
        finding("scope GitHub tokens to the step that needs them")
    for name, job in data.get("jobs", {}).items():
        permissions = job.get("permissions", {})
        if not isinstance(permissions, dict):
            finding(f"{name}: broad permission aliases are forbidden")
        if TOKEN_NAMES & set(job.get("env", {})):
            finding(f"{name}: scope GitHub tokens to individual steps")
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if (
                uses
                and not uses.startswith("./")
                and not re.fullmatch(r"[^@]+@[a-f0-9]{40}|docker://[^@]+@sha256:[a-f0-9]{64}", uses)
            ):
                finding(f"{name}: action must be pinned to an immutable hash: {uses}")
            if (
                uses.startswith("actions/checkout@")
                and step.get("with", {}).get("persist-credentials") is not False
            ):
                finding(f"{name}: checkout must disable credential persistence")
            if re.search(r"\$\{\{\s*github\.event\.", step.get("run", "")):
                finding(f"{name}: pass event data through env, not inline shell interpolation")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    paths = sorted((args.repo / ".github/workflows").glob("*.y*ml"))
    if not paths:
        parser.error("No workflows found")
    findings = [finding for path in paths for finding in audit_workflow(path)]
    print(
        "\n".join(findings) if findings else f"Workflow security checks passed: {len(paths)} files."
    )
    return int(bool(findings))


if __name__ == "__main__":
    raise SystemExit(main())
