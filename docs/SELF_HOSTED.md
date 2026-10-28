# Dedicated Lean runners

The Lean jobs in `validate.yml`, `deploy.yml` and `release-data.yml` use the repository variable `LEAN_RUNNER`, falling back to `ubuntu-latest`. A single custom label such as `lean-large` must identify the intended runner. Registration and repository settings are operator actions; the local setup script neither registers a runner nor changes GitHub settings.

Use a dedicated Linux machine or ephemeral VM with Git, GitHub CLI, uv, Node >=22.12, npm and elan/Lake. Python is managed by uv. The pinned Lean toolchain and Mathlib revision come from `lean-toolchain` and `lake-manifest.json`. Start with 32 GB RAM and enough disk for the toolchain, Mathlib, build objects and separate checkout directories; adjust from measured resource use. The spec's migration signals are cold builds over three hours, routine PR builds over 45 minutes, compressed build caches over 4 GB, individual modules over 16 GB RAM or roughly 8,000 modules.

```sh
# Read-only prerequisite/resource checks in this checkout:
tools/scripts/bootstrap_runner.sh --check

# On the dedicated runner, after reviewing its checkout:
tools/scripts/bootstrap_runner.sh --warm
```

`--warm` installs locked Python extras and npm packages, downloads the matching Mathlib cache and builds the pinned project. It does not download or execute a runner registration script. Obtain the runner binary and its checksum from GitHub's repository runner setup page, verify them, register a dedicated `lean-large` label, and set `LEAN_RUNNER=lean-large`. Keep that label exclusive to machines intended for this repository. Remove the variable to return to hosted runners.

PR builds execute repository-controlled code, including Lake configuration and Python/Node dependencies. Use an ephemeral runner for each job where possible. A persistent runner must have a separate service account, no personal SSH keys or model API keys, no unrelated checkouts or private reference files, and isolated work directories for concurrent jobs. This project's collaborator-only PR policy does not make arbitrary checked-out code harmless. Do not attach a personal workstation to public PR execution.

The workflows turn off checkout credential persistence. Tokens are provided only to the steps that read PR metadata, post summaries or publish outputs. The site deployment job has Pages/OIDC permissions; Lean compilation does not receive a model key. GitHub caches for `.lake/build` are disabled when `LEAN_RUNNER` is set. Persistent runners can retain local build files under the service account, while ephemeral runners can restore a separate trusted seed keyed by both toolchain and Lake manifest. Never reuse stale objects across incompatible toolchains.

Before enabling a runner, run an infrastructure validation and a fixture build manually, verify the generated data and record cold/incremental duration, memory and disk consumption. Do not advertise a larger-runner speedup until those measurements exist. The local implementation environment is not evidence that a GitHub runner has been registered or tested.
