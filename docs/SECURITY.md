# Security review and maintenance

The October 28, 2026 local review covered the HomAlgDB workflows, the `homalg-horizon` fork workflows, browser dependencies, Python lock files and the implemented local data boundaries. It does not claim a penetration test or a configured remote repository.

## Workflow boundaries

Every workflow starts with `permissions: {}`. Jobs grant only their required categories: read access for data/checks, PR write access for classification and review comments, contents write for a release, and Pages/OIDC write for the deployment job. External actions are pinned to complete commit SHAs. Neither repository uses `pull_request_target`. Event values enter shell scripts through environment variables and quoted expansions. Checkout credential persistence is disabled throughout both repositories; `GH_TOKEN` is scoped to the individual step that uses it. Live PR checks use an environment-scoped Git credential helper for authenticated fetches, without persisting the token in checkout configuration.

The owner-approval workflow checks out the trusted PR base and uses its locked policy implementation to compare the explicit base/head Git objects. The PR cannot replace its own owner-review checker merely by modifying Python code. Sensitive workflow and policy files still require the configured CODEOWNERS/ruleset protection; see [CI.md](CI.md). Those protections must be installed on the real repository before treating CI as an enforcement boundary. Model API keys never enter CI or scheduled jobs.

Run the local invariant check after workflow edits:

```sh
uv run --project tools python tools/scripts/audit_security.py
uv run --project tools python tools/scripts/audit_security.py --repo ../homalg-horizon
```

The checker rejects mutable action references, broad permission aliases, persisted checkout credentials, job-wide tokens, model API keys, inline event interpolation and `pull_request_target`. It complements a human review of why each permission is needed; it does not prove that arbitrary scripts are safe. `actionlint` 1.7.7 also passed all six workflows during this review. Dedicated runner setup and its trust boundary are documented in [SELF_HOSTED.md](SELF_HOSTED.md).

## Dependency audit

Both npm lock files were checked with `npm audit` including development dependencies: zero known vulnerabilities were reported. The main site contains 627 resolved dependency entries; the dashboard reports 180. Both complete Python lock exports also reported zero known vulnerabilities with pip-audit 2.10.1. These are audit-time observations, not a guarantee against undisclosed or later advisories.

Audit Python dependencies from the committed lock, including optional server, ingestion and evolution extras:

```sh
uv export --project tools --locked --all-extras --all-groups --no-editable \
  --no-hashes --no-emit-project --format requirements-txt --output-file build/audit-requirements.txt
uv tool run --from pip-audit==2.10.1 pip-audit --disable-pip --no-deps \
  -r build/audit-requirements.txt --format json --output build/pip-audit.json
npm audit --prefix site
```

The no-deps audit consumes the complete exact-version export and does not install or resolve the application packages. Run the equivalent export from the fork root for its Python lock and `npm audit --prefix src/archon_horizon/frontend` for its dashboard. Dependabot tracks actions, Python and npm in the main repository. Review and test updates before merging them, and keep immutable action hashes when updating action versions.

## Data boundaries checked

The static site sanitizes authored Markdown before math rendering, disables remote Markdown images, and treats identifiers as links only through validated routes. Source text is escaped/highlighted; graph and list routes provide no arbitrary code execution facility. Imported model output is validated and remains unreviewed, and model calls require a local cost cap. See [EVOLUTION.md](EVOLUTION.md).

The local server binds to loopback by default. Its resource routing rejects path traversal and symlink escapes. The private Horizon reference viewer permits the configured top-level reference symlink while rejecting child escapes and sends private no-store responses. API mode uses parameterized SQLite queries and bounded dependency traversal. Existing tests cover these boundaries, malformed inputs and hostile Markdown.

Generated-file cleanup only removes a file explicitly referenced by the previous manifest, absent from the replacement manifest, matching a generated-shard path and contained under the output directory without symlink traversal. Unknown files are preserved. Large-index shards are data artifacts, not executable modules.
