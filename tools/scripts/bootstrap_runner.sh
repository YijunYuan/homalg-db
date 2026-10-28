#!/usr/bin/env bash
# Check or warm an already registered, dedicated Linux Lean runner.
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd -- "$repo_dir"
mode="${1:---check}"
if [[ "$mode" != --check && "$mode" != --warm ]]; then
  echo 'Usage: tools/scripts/bootstrap_runner.sh [--check|--warm]' >&2
  exit 2
fi
for tool in git uv node npm lake gh; do
  if ! command -v "$tool" >/dev/null; then
    echo "Missing prerequisite: $tool" >&2
    exit 1
  fi
done
node -e 'const [major, minor] = process.versions.node.split(".").map(Number); if (major < 22 || (major === 22 && minor < 12)) { throw new Error("Node >=22.12 is required") }'
printf 'Runner checkout: %s\n' "$repo_dir"
printf 'Pinned toolchain: %s\n' "$(cat lean-toolchain)"
printf 'Configured Lean: %s\n' "$(lake env lean --version)"
printf 'Available memory (KiB): %s\n' "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)"
df -Pk "$repo_dir" | tail -n 1
if [[ "$mode" == --warm ]]; then
  uv sync --project tools --locked --all-extras --group dev
  npm ci --prefix site
  lake exe cache get
  lake build
fi
printf 'Prerequisites passed. Set the repository variable LEAN_RUNNER to this runner\047s dedicated label after reviewing docs/SELF_HOSTED.md.\n'
