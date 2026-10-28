# CI and repository governance

The workflows separate inexpensive metadata and collaboration checks from Lean
builds. GitHub settings are applied separately using the governance command below.

## Checks and deployment

`validate.yml` produces the required `gate` check from four jobs:

- `classify` inspects the changed paths and fetches live PR labels. Claim and
  registration PRs skip Lean; fixture changes count as infrastructure. Progress
  branches under `status/` cannot be merged.
- `checks` validates metadata, applies current-main claim ownership and expiry,
  counts pending claim PRs, enforces document scope and append-only taxonomy, and
  blocks ordinary PRs while the latest main deployment is red. `repair` opts into
  repairing main. Infrastructure changes also run tests and build the site.
- `lean` runs only when classification returns `needs_lean=true`. It builds the
  selected document for formalization PRs and the whole library for multi-document
  or Mathlib/toolchain changes. Infrastructure triggers the whole-library job
  when it touches `HomAlg/`, `HomAlgExport/`, `tools/homalg/checks/`,
  `lakefile.toml`, `HomAlg.lean`, `tools/homalg/leanexport.py` or
  `tools/homalg/extract.py`. Other tool, site and documentation infrastructure
  changes still run tests and the site build, with Lean deliberately skipped.
  When enabled, the job regenerates Lean metadata, validates it, rejects
  uncommitted generated-data changes and posts a review summary for document PRs.
- `gate` requires successful classification and checks, and successful or
  deliberately skipped Lean work. Failure and cancellation cannot pass.

`owner-approval.yml` independently checks sensitive document fields, multiple
changed documents, taxonomy-maintenance changes and proof-route dispute
resolutions. The owner's latest decisive review must approve the exact current
head SHA; the owner's own PRs pass. Review submission/dismissal reruns this check
without rebuilding Lean. A merge group relies on its constituent PR approvals.
The workflow invokes `homalg pr-check --owner-only`, using the same policy API
that the main validator can call through its PR options.

`deploy.yml` validates and builds full data on pushes to `main`, daily at 03:17 UTC,
and by manual dispatch. It saves only `.lake/build` immediately after Lean's build,
checks generated-data freshness and size budgets, then deploys `site/dist` through
`github-pages`. The Vite build uses the relative base `./`. JavaScript, styles,
workers and data resolve relative to the served site, so the same build works at a repository
Pages path or a local preview root. A failed build leaves the previous site
online. Deployments are serialized without cancelling an earlier deployment. `release-data.yml` builds
a weekly validated snapshot and publishes a data archive containing LICENSE,
LICENSE-DATA and NOTICE in a dated GitHub Release.

Production infrastructure [PR #15](https://github.com/YijunYuan/homalg-db/pull/15)
merged as `34ca001157dcccb99eb5878aac4e77be500af79e`. Its
[Pages deployment](https://github.com/YijunYuan/homalg-db/actions/runs/40642971475)
and [data-release run](https://github.com/YijunYuan/homalg-db/actions/runs/40643093648)
both succeeded. The downloaded
[`data-2026-10-28` snapshot](https://github.com/YijunYuan/homalg-db/releases/tag/data-2026-10-28)
was checked for its SHA-256, archive entries, license files and absence of private
paths; [implementation evidence](IMPLEMENTATION.md#remote-publication-evidence)
records the exact values. This published infrastructure snapshot precedes the
final pilot formalization. Both production progress snapshots subsequently
passed live verification, including
[deployment 40665487067](https://github.com/YijunYuan/homalg-db/actions/runs/40665487067)
with the stable 27-proof-complete status. The actual `homalg submit` created
[pilot PR #16](https://github.com/YijunYuan/homalg-db/pull/16) at head
`e4b0cd6c8bc7b85e6a02903292d003855cfbcf85`. Its
[CI run 40666512164](https://github.com/YijunYuan/homalg-db/actions/runs/40666512164)
passed, and the standard REST squash endpoint accepted the exact head and merged as
`5b4771d924974ea59a9c4c1ec5bd5713af4e6482`. The main
[deployment 40667644896](https://github.com/YijunYuan/homalg-db/actions/runs/40667644896)
passed. Screenshot review found a graph-fit issue, repaired in
[PR #17](https://github.com/YijunYuan/homalg-db/pull/17) at
`c5489f42b97470d6424778a0b8134ed59c520d0a`. Its
[CI run 40670365185](https://github.com/YijunYuan/homalg-db/actions/runs/40670365185)
passed applicable checks with `needs_lean=false`; this is an intentional skip,
not failed Lean work. Superseded opening/label-event runs were cancelled.
[Deployment 40670763457](https://github.com/YijunYuan/homalg-db/actions/runs/40670763457)
then passed all 17 actual production browser assertions and visual review,
including the full expanded graph and every deviation explanation, with no
JavaScript, HTTP or request errors.

For PRs #16 and #17 the CLI's merge precheck reported `BLOCKED`, while GitHub
accepted a standard REST squash request with the exact expected head SHA.
No administrator/force option or rule change was used. The cause of the CLI
precheck result was not established, and these owner-authored merges do not
establish the untested non-owner governance behavior.

The final local infrastructure regression passed 375 Python and 31 frontend
tests; 24 tests in the separate Lean smoke/export and pilot suites passed.
[Implementation evidence](IMPLEMENTATION.md#verification-evidence) records the
18 context/setup skips, their follow-up coverage and the dependency warning.

Optional doc-gen4 publication is disabled after the bounded local cold build
timed out. The [measurement report](DOCGEN_MEASUREMENT.md) preserves the actual
logs and clock discrepancy; complete output size and GitHub runner timing remain
unverified. No documentation workflow, Release asset or declaration-page link
has been enabled.

Every workflow denies permissions by default and grants only the job permissions
it needs. Explicit Bash enables `pipefail`; a failed `lake build | tee` fails CI.
All referenced actions are pinned to upstream commit SHAs. There is no
`pull_request_target` workflow. The selected upstream tags are documented inline:
[checkout](https://github.com/actions/checkout),
[setup-uv](https://github.com/astral-sh/setup-uv),
[setup-node](https://github.com/actions/setup-node),
[lean-action](https://github.com/leanprover/lean-action),
[upload-pages-artifact](https://github.com/actions/upload-pages-artifact), and
[deploy-pages](https://github.com/actions/deploy-pages).

## Prepare and apply governance

Use an existing GitHub repository with the default branch `main` and an account
with repository administration permissions. The script never creates repositories
or opens pull requests. The checked-in `CODEOWNERS` names `@YijunYuan`.
Governance has been applied to the production and acceptance repositories;
the commands below reproduce it for another repository or reconcile changes.

Preview the complete plan without contacting GitHub or changing files:

```sh
make governance GOVERNANCE_ARGS='--repository OWNER/homalg-db'
```

Render actual ownership locally, inspect the diff, and commit/push it with the
workflows before enabling the rulesets:

```sh
python3 tools/scripts/governance.py --repository OWNER/homalg-db --write-codeowners
```

Apply an already-reviewed plan explicitly:

```sh
make governance GOVERNANCE_ARGS='--repository OWNER/homalg-db --apply'
```

`HOMALG_REPOSITORY=OWNER/homalg-db` can replace `--repository`.
`GOVERNANCE_OWNER_KIND=user` is the default. Organization mode requires
`--owner-kind org --owner-login MAINTAINER --team-id ID`; it verifies that the ID
belongs to `OWNER/homalg-maintainers` before writing. `HOMALG_OWNER` is always the
human maintainer's login, while CODEOWNERS uses the organization team.

The idempotent script creates or updates `main` and `status-branches` rulesets,
reads them back to verify their contents, enables squash-only auto-merge and
branch deletion after merge, restricts default workflow permissions to read,
sets Pages Source to GitHub Actions, sets `HOMALG_OWNER`, and creates or updates
the twelve specified labels. Existing resources are updated by identity. Network
failure can leave a partially applied plan; review the failure and rerun to finish.

The two required checks are `gate` and `owner-approval`. CODEOWNERS protects
infrastructure, schemas, the site, and relation review decisions while exempting
node paths, document metadata, and append-only taxonomy/relationship paths.
Those exemptions are checked by the metadata and collaboration policy commands. Personal repositories permit the repository administrator to
bypass in pull requests, as required to avoid blocking the sole owner's own PRs.
Add a second maintainer for meaningful independent code-owner review.

A registration-only document has no Lean node imports yet. Compiled existence
checks for its foundation names are deferred and explicitly reported as
`mathlib-decls-exist:DOC:no-node-modules` in skipped coverage. The first node
restores strict compiled lookup checks; a misspelt or unavailable foundation then
fails validation. Metadata schema and review-provenance checks remain active
during registration.

Remote acceptance must be exercised in a test repository: a contributor's
infrastructure PR must require owner review, an eligible formalization PR must
pass without it, and a claim PR must auto-merge after both required checks pass.
The local tests exercise these rules with temporary Git repositories and fake
GitHub responses. The [cold-start acceptance](COLD_START_ACCEPTANCE.md) records
actual submit/merge/deploy and production progress checks, but no real
two-account claim race or non-owner denial exercise has been performed.

The escalation fix `e219ce0` (originally `55234ff`), merged and deployed in PR #17,
makes an empty candidate list a successful no-op: it does not invoke the human
guard, create a GitHub client or prompt. A nonempty list still requires the
original human-session guard and per-item confirmation before publication.
Positive and negative regression cases cover both paths; an unattended empty
release flow gains no permission to publish unresolved issues.

## Local pre-commit hook

Install with `git config core.hooksPath .githooks`. The hook rejects staged PDF
paths, runs Ruff and fast metadata validation, and checks site formatting with the
locked Prettier dependency. The installed hook validates the whole repository
with `--fast`. The implemented `homalg validate --fast --changed` option selects
changes from the merge base with `origin/main` by default; `--pr-base` and
`--pr-head` select another comparison. Document-only changes narrow document
validation while retaining global reference context; shared changes select the
whole repository. Horizon ledger commits use a separate Git directory and do
not pass through this hook.

## Cache and runner policy

The workflows cache only the project's `.lake/build`, keyed by the toolchain and Lake
manifest. Mathlib cache downloads and `~/.elan` stay outside the GitHub cache.
Consider a self-hosted runner when a cold build exceeds three hours, routine
incremental PR builds exceed 45 minutes, a compressed cache exceeds 4 GB, a module
needs over 16 GB memory, or the library reaches roughly 8,000 modules. Set the
repository variable `LEAN_RUNNER=lean-large`; the Lean job honors
this runner override.

## Transient dependency-download retries

Lean setup retries at most three times in validation, deployment and snapshot
release jobs. Actual runs encountered TLS failures at the pinned toolchain's
upstream download endpoint before any repository check ran. Only the first two
setup attempts tolerate failure; the last attempt and every build/validation
step still fail normally. All attempts use the same immutable lean-action SHA,
toolchain and TLS verification. Cancelled superseded runs skip the aggregate
gate instead of producing an artificial gate failure.
