# Local formalization engine

HomAlgDB invokes the separately maintained `homalg-horizon` fork through its CLI
and versioned files. It does not import the fork's Python internals. The required
version is the first line of `horizon-version.txt`. The local source checkout is
`../homalg-horizon`; `UPSTREAM.md` there identifies the exact upstream revision and
the patch series. The [pinned release](https://github.com/YijunYuan/homalg-horizon/releases/tag/v0.1.5-homalg.1)
contains the wheel and source distribution. Its remote CI and release checks pass;
the downloaded wheel was installed in an isolated environment and contains the
dashboard and current review-policy instructions.

## Setup

Install the pinned engine in its own environment and put its executable on `PATH`.
Put this checkout's `tools/.venv/bin` on `PATH` as well, so hooks can call `homalg`.
Authenticate `gh`, configure the private literature URL, then run:

```sh
uv tool install 'https://github.com/YijunYuan/homalg-horizon/releases/download/v0.1.5-homalg.1/archon_horizon-0.1.5%2Bhomalg.1-py3-none-any.whl'
uv sync --project tools --locked --all-extras
export PATH="$PWD/tools/.venv/bin:$PATH"
homalg literature sync
homalg doctor
homalg horizon-init --engine codex
```

Use `--engine claude-code` for that harness. Optional `--model`, `--effort` and
`--transcriber-model` are explicit user choices. Initialization caches the GitHub
login, installs resources, and renders `config.yaml` from the repository template.
It preserves the public `.gitignore`; engine state, transcripts and private source
material must stay ignored. Each checkout has its own `.lake/build` directory.

`homalg doctor` verifies the fork version, required ignores, accidentally tracked
ignored files, and conflicting workspace build directories. It does not imply that
remote repository settings or paid model access have been configured.

## Stages and evidence

Claim the document before planning. `--no-claim` is restricted to synthetic
documents. Fill chapter ranges and `item_kinds`, then use:

```sh
homalg plan Hochschild1945
horizon task list
horizon run '*' --rounds 1
```

The stages are T (visual transcription), INV (page inventory), DAG (source
dependencies), CITED (external statements), STMT (formal statements) and PROOF.
Each task names explicit files. `homalg plan --advance` creates newly eligible
tasks without silently requeuing blocked work or broadening existing scopes.
An inventory must account for unnumbered items and footnotes as well as numbered
theorems. A paper without sections beneath its chapter entries is inventoried by
chapter; `new-node` then requires `--chapter` and no `--section`.

`homalg stage-check TASK` uses current source and compiled evidence. It refreshes
stale Lean facts through the shared build lock. A successful subprocess or an
agent's task-status edit alone is not completion evidence. Three sessions without
stage-relevant progress block the task and create a local inbox request. Progress
resets the counter; duplicate processing of the same session does not count twice.

Before theorem statements advance, independent review covers the first definitions
and foundation boundary. The owner-approved [review policy](REVIEW_POLICY.md)
allows agents to record this evidence and continue automatically. The optional
human workflow below requires an interactive terminal outside an agent session
and no active engine run:

```sh
homalg foundations list Hochschild1945
# Inspect each proposed entry before confirming its one-based index.
homalg foundations confirm Hochschild1945 1 --by YOUR_LOGIN
homalg review-fidelity Hochschild1945.Def_two_sided_module --human --by YOUR_LOGIN
homalg plan Hochschild1945 --early-review-ok --by YOUR_LOGIN
```

These are optional human-workflow examples, not required pilot steps under the
enabled policy. Agents use the commands in REVIEW_POLICY.md instead. They must
never simulate a human terminal or invent a human review record.

## Builds, hooks and recovery

During a run, use `horizon check [MODULE ...]`. A no-target check invokes
`homalg build-active`, which builds active claimed documents and runnable task
documents, including orphan auxiliary/cited nodes. Export and full validation use
the same `.archon-horizon/cache/checks/workspace.lock`; do not nest another lock
around the exporter.

Before each round, hooks regenerate the scoped blueprint and capture recoverable
private-source bytes. After a session, `homalg after-session` checks its ledger
diff, restores forbidden private changes, regenerates local facts and graph data,
updates task evidence and progress, and attempts eligible backups/status updates.
The hook's normal stdout is empty. Scope violations alone return
`{"violations":["path"]}` with exit code 4. The fork rolls back exactly those
paths, preserves allowed work, requeues the task, and asks the local human inbox
for attention. Snapshot recovery preserves preexisting staged, unstaged and
untracked private bytes rather than resetting the entire source repository.

`homalg blueprint-tex --active` derives `blueprint/src/content.tex` and
`hgraph/config.yaml` from node headers. Direct dependencies from other documents
become external stubs. Review locks, both dependency classes, declaration names,
and printed-to-PDF page mappings are retained. `horizon graph sync` imports this
projection; edit the headers, never the generated TeX.

Inspect processes with `horizon ps`. Wait for a run before making guarded changes;
if necessary stop a specific run with `horizon ps --kill RUN`, then resume with
`horizon run --resume latest`. The fork's optional per-session ledger mode supports
disjoint workspaces/scopes with serialized landing; serial execution is the
default. See the fork's `docs/HOMALG.md` for concurrency and conflict recovery.

## Publication boundary

`homalg publish-status KEY` writes only schema-validated numeric progress to
`status/KEY` after checking current `origin/main` ownership. It is throttled and
does not publish page text, prompts or logs. `homalg backup` commits and pushes
private source changes to the private repository. `homalg sync-main` prepares a
reviewable rebase and refuses conflicting ownership or human-field changes.

`homalg submit KEY` requires idle tasks, runs validation, prepares a document-scoped
commit in an isolated worktree, and creates a formalization PR. Configured engine
workspaces also run the lifecycle backup/log/status/escalation steps. Local inbox
escalation previews the proposed GitHub issue text for a human before posting.
These commands perform external writes when invoked; an autonomous mathematical
session uses the local inbox and must not invoke them opportunistically.

Use `homalg review-summary --doc KEY --base REV` to inspect findings, stored local
status changes, deviations and remaining `sorry` declarations without publishing.
The default comparison base is `GITHUB_BASE_SHA` or `origin/main`; a missing base
is reported explicitly. Historical global headlines cannot be reconstructed from
document-local `nodes.json` alone and are not fabricated.
