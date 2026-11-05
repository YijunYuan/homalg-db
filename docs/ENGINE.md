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

Task objectives are authored in this repository's `horizon/tasks/`. Installed
role and skill text comes from the fork's tracked descriptors and skills, not
from edits to a running workspace's `.claude/` or `.codex/` copies. After changing
those sources, test and install the updated fork, then use the supported resource
refresh at an idle boundary. An older published wheel does not acquire new
instructions merely because a source checkout changed.

`homalg doctor` verifies the fork version, required ignores, accidentally tracked
ignored files, and conflicting workspace build directories. It does not imply that
remote repository settings or paid model access have been configured.

## Stages and evidence

Claim the document before planning. `--no-claim` is restricted to synthetic
documents. Fill chapter ranges and `item_kinds`, then use:

```sh
homalg plan Hochschild1945
horizon task list
homalg workflow next Hochschild1945 --json
horizon run ACTUAL_READY_TASK --rounds 1
```

The stages are T (visual transcription), INV (page inventory), DAG (source
dependencies), CITED (external statements), STMT (formal statements) and PROOF.
Each task names explicit files. `homalg plan --advance` creates newly eligible
tasks without silently requeuing blocked work or broadening existing scopes.
An inventory must account for unnumbered items and footnotes as well as numbered
theorems. A paper without sections beneath its chapter entries is inventoried by
chapter; `new-node` then requires `--chapter` and no `--section`.

`homalg plan KEY --statement-frontier --statement-batch-size 4` enables persisted
node statement units with bounded independent author groups (size 1–16, default
4). `--statement-node NODE` restricts the selected primaries; `workflow next`
reports current ready work and local blockers without dispatching. Existing task
scopes/holds and chapter acceptance requirements remain intact. The native lead
fans out independent groups; a source or construction issue holds its actual
consumers. See [PARALLEL_WORKFLOW.md](PARALLEL_WORKFLOW.md) for the full protocol.

`homalg stage-check TASK` uses current source and compiled evidence. It refreshes
stale Lean facts through the shared build lock. A successful subprocess or an
agent's task-status edit alone is not completion evidence. Three sessions without
stage-relevant progress block the task and create a local inbox request. Progress
resets the counter; duplicate processing of the same session does not count twice.

The native lead runs the required stage check, performs the prescribed task-status
action, preserves its evidence and returns control to Horizon. It does not manually
invoke `homalg after-session` or add an extra `homalg plan --advance` to finish its
session. Horizon invokes the configured outer hook after the lead returns. The
outer coordinator then verifies the actual private/scope result, validation report,
stage evaluation and resulting task state before reporting final acceptance. A zero
hook process return code alone does not establish success: the hook records its
detailed result and may defer backup/status operations. Explicitly authorized
external recovery retains its separate protocol in
[PARALLEL_WORKFLOW.md](PARALLEL_WORKFLOW.md).

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

## Parallel preparation

Use [PARALLEL_WORKFLOW.md](PARALLEL_WORKFLOW.md) to coordinate disjoint draft
ownership, dependency-ready batches, frozen author handoffs and independent
review. A draft worker's checkout, ledger and build state must be isolated from
the live canonical workspace. Review registration remains attributable per node;
sharing a build/export operation does not supply a shared blanket verdict.
Recheck the final report/input snapshot and canonical dependency baseline before
guarded integration. Normal claim, scope, source-review and session gates remain.
The native lead owns decomposition and delegation and can request worker creation
with guarded `homalg workspaces create --native --task TASK` for its actual
active parent run/session and bound task. Native-only `workspaces collect ID
--by LEAD` stages uncompiled owned candidates after scope/baseline/dependency
checks; canonical compilation/export and all ordinary review/acceptance gates
follow. Checked workers may instead use `promote --native`. External calls remain
idle-only. The worker receives a public source projection and an isolated ledger,
without root runtime configuration, engine history or private state. Dispatch
independent ready units before joining; serialize canonical landing and finalization.
The outer coordinator supplies inputs and observes receipts instead of replacing
native execution with external authoring or acceptance.

## Builds, hooks and recovery

Mathematical task checks are scoped to their changed content and stage: local
`horizon check`, required fresh export and fidelity registration, the exact
`homalg stage-check`, then the configured outer hook. Run the full `make test`,
`make validate` and `make site` regression suite when tooling, schemas or site
implementation changes, not for each unchanged-tooling source/Lean task.
Source proof prose, DAG/comments/metadata quality, compiled-record freshness,
generated blueprint synchronization, independent review and final validation
remain mandatory. Reuse of unchanged infrastructure checks grants no approval
to new mathematical bytes.

During a run, use `horizon check [MODULE ...]`. A no-target check invokes
`homalg build-active`, which builds active claimed documents and runnable task
documents, including orphan auxiliary/cited nodes. Export and full validation use
the same `.archon-horizon/cache/checks/workspace.lock`; do not nest another lock
around the exporter.

Before each round, hooks regenerate the scoped blueprint and capture recoverable
private-source bytes. After the native lead returns, the engine invokes
`homalg after-session` to check its ledger diff, restore forbidden private changes,
regenerate local facts and status overlays, update task evidence and progress,
advance eligible planning, and attempt eligible backups/status updates. This
already includes advance planning; the native lead must not repeat that operation
as an additional finalization step.
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

The projection can lag nodes scaffolded after the round began. Check the authored
headers before interpreting an omitted graph node as missing source work. Use the
normal next-round refresh. If same-round graph visibility is needed, the native
lead may run `homalg blueprint-tex --active` followed by `horizon blueprint --json`
at a permitted boundary. Graph sync alone does not regenerate missing TeX or
guarantee a refreshed blueprint JSON. Do not repeat the full after-session
hook or advance planning just to refresh the view. A projected planned node is not
an implemented statement.

Inspect processes with `horizon ps`. Wait for a run before making guarded changes;
if necessary stop a specific run with `horizon ps --kill RUN`, then resume with
`horizon run --resume latest`. The fork's optional per-session ledger mode supports
disjoint workspaces/scopes with serialized landing; serial execution is the
default. See the fork's `docs/HOMALG.md` for concurrency and conflict recovery.

## Publication boundary

`homalg publish-status KEY` writes only schema-validated numeric progress to
`status/KEY` after checking current `origin/main` ownership. It is throttled and
does not publish page text, prompts or logs. `homalg backup` archives owned
discussion logs and pushes the actual source ledger to the private
`backup/<login>/work` branch when `.archon-horizon/vcs/workspace.git` exists.
It preserves the user's Git HEAD and index; a checkout without an engine ledger
retains the ordinary Git backup behavior. Remote names are resolved read-only
from the user's checkout, so the source ledger needs no configured remote.
The selected work-backup destination must have exactly one push URL, different
from every configured fetch or push URL of the public `origin`.
The private literature checkout is pushed separately through its own Git
directory and branch. Invalid or symlinked ledgers and inherited Git repository
or index redirection are refused rather than falling back to user Git.

Backup pushes are never forced. A divergent old backup branch returns
`backed_up: false`, `reason: non-fast-forward` and the failed `operation`, retaining
the local source commit and any private-source push already completed. Do not
rewrite an old backup branch or infer success from a hook exit code. Results
identify the actual `source` (`ledger` or `user-git`) and `source_commit`; inspect
them before a separately authorized recovery or retry. This backup-specific
routing does not alter claim, submission or numeric status publication.

`homalg sync-main` merges
current main with explicit owned-document and append-only conflict rules; it
does not rebase. Unsupported conflicts abort the merge and retain a local
request for review.

`homalg submit KEY` requires an idle engine, runs validation, prepares a document-scoped
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
