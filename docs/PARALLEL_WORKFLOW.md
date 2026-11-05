# Parallel formalization workflow

This guide coordinates preparation, independent review and serial acceptance.
It preserves [source fidelity](CONVENTIONS.md) and the
[independent review policy](REVIEW_POLICY.md). Parallel work does not enlarge a
claim, task scope or foundation boundary.

## Implementation status

The commands below are implemented in the workflow optimization source tree.
Their integration checks and measured acceptance are recorded separately in
[IMPLEMENTATION.md](IMPLEMENTATION.md); command availability does not imply that
a published package contains this revision. Earlier acceptance records remain
historical evidence.

## Roles and boundaries

| Role | Owns | Required handoff | Does not establish |
| --- | --- | --- | --- |
| Outer coordinator | Owner scope and decisions, bounded future inputs, runtime observation | Exact task/input references and inspected runtime receipts | Native authorship, integration or independent mathematical approval |
| Native lead | Scoped decomposition, author/reviewer assignments and integration requests | Task scope, actual identities, frozen inputs and check results | Independent approval of its own mathematics |
| Horizon runtime | Worker/run lifecycle, canonical serialization and outer finalization | Durable phase receipts and resulting task state | Mathematical/source verdicts |
| Draft author | Assigned node files in an isolated checkout | Exact candidate bytes, dependencies, source anchors and unresolved issues | Permission to modify the canonical checkout or another worker's files |
| Independent reviewer | A substantive report on the exact supplied inputs | Actual author/reviewer identities, per-node verdicts, coverage and input hashes | Acceptance of later edits or a human decision |
| Integrator | Scoped promotion and guarded evidence registration | Actual transaction, build/export, scope and validation results | Broader ownership, proof completion or publication approval |

A reviewer must actually be a separate execution from the author. An operator
may orchestrate an authorized registration without becoming the reviewer; the
stored provenance must identify the person or agent that did the work.
A checker that verifies hashes is not a source-fidelity reviewer.

## Scheduling

1. Read the registered task and identify the dependency frontier. Prioritize
   definitions and constructions needed by later nodes.
2. Assign disjoint, explicit node ownership. Dispatch all independent ready units
   before joining their results; wait when a consumer needs an output and before
   ending the session. Parallelize only work whose required
   dependency inputs are fixed. A shared live source directory is not an isolated
   worker, even when the assigned filenames differ.
3. Prepare bounded batches. Stop growing a batch when its dependency boundary
   changes, an input is unresolved or a reviewer cannot cover it completely.
4. Complete required checks locally or after native collection in the canonical
   build lane, then freeze the authored inputs delivered for review.
   This author handoff precedes the independent report; it cannot freeze a report
   that has not yet been written. A snapshot identifies bytes; it does not grant
   review, approval or reusable compilation.
5. Obtain complete independent review, including recursive definitions and
   required honesty checks. Preserve source uncertainty and genuine
   mathematical disagreement instead of manufacturing a satisfactory verdict.
6. Freeze the completed reports together with their reviewed inputs for guarded
   registration. Integrate through the canonical boundary and recheck the
   dependency baseline. Any changed input invalidates the relevant handoff until
   the change has been assessed and the required review repeated.
7. Run the real stage and session completion checks. Record their actual outputs
   and resulting task state. A successful subprocess, compilation, promotion or
   review registration alone does not mean the task is done.

Preparation and review can overlap with other isolated work. Acceptance of a
shared canonical state must be coordinated and serialized. A newly approved
definition can unlock several writers; writing additional downstream drafts
against an unsettled definition usually increases rework.
Keep logical dependencies separate from shared-resource serialization. A shared
manifest requires one canonical writer, not sequential independent preparation.
A source question or housekeeping warning blocks only the work whose inputs or
safe execution depend on its resolution. Retain the question and continue other
ready work; no unanswered question supplies approval.

Mathematical sessions run current scoped checks, required fresh exports,
independent reviews, the exact stage check and the engine-owned final hook.
Changes to tooling, schemas or site implementation additionally require the full
`make test`, `make validate` and `make site` infrastructure regression suite.
Do not run that suite again for each unchanged-tooling mathematical task. This
division removes duplicate infrastructure tests, not source Statements/Proof
prose, DAG annotations, comments, metadata, generated-data freshness, blueprint
synchronization, review or final validation. Deferred formal proofs leave all
these obligations in place.

## Evidence and failure handling

Keep actual author and reviewer identities, source locations, complete coverage,
input hashes, unresolved regions and the result of every executed command.
Retain stdout, stderr and return code separately: some tools print version
information to stderr even on success. Do not reconstruct missing timings or
invent native-session metadata for an external operator.

A frozen input set must be checked again at registration. It cannot excuse a
stale report, changed source, altered dependency or replaced toolchain. Batch
registration keeps each node's report and compiled hashes distinct. It does not
convert a mixed or partial set of verdicts into a satisfactory batch.

Author preparation and final review registration are separate operations. A fresh
compile/export performed during preparation does not waive the fresh export at
review registration. Measure both phases and any worker checks rather than
describing the entire workflow as having only one compilation.

For a stable canonical batch with several actual authors, `workflow prepare-batch`
shares one fresh document export and the full ordinary preflight validation. It
publishes one immutable bundle containing a separate delivery for every author.
The authors JSON array explicitly assigns disjoint, nonempty task-scoped nodes:

```json
[
  {"author_session": "ACTUAL_AUTHOR_A", "node_ids": ["Example2000.Def_A"]},
  {"author_session": "ACTUAL_AUTHOR_B", "node_ids": ["Example2000.Def_B"]}
]
```

```sh
homalg workflow prepare-batch Example2000.STMT.1 \
  --authors build/actual-authors.json --out build/batch-handoff.json
homalg workflow verify build/batch-handoff.json --author-session ACTUAL_AUTHOR_A
# After that author's genuine independent reports exist:
homalg workflow review-snapshot build/batch-handoff.json \
  --author-session ACTUAL_AUTHOR_A --node Example2000.Def_A \
  --out build/author-a-review.json
```

Every delivery retains its own actual author, node list, source/dependency inputs
and compiled declarations. All receive the same complete validation findings;
an error is not hidden merely because another author owns the affected node.
Verification and review snapshots require an explicit author selection from a
bundle. Review registration groups nodes by the same real author/reviewer
provenance. The [typed cohort workflow](REVIEW_COHORTS.md) can register several
such groups together with one required fresh export, preserving every identity.
No preparation caches a
previous invocation's verdict or supplies review approval. Concurrent input
changes abort publication of the entire bundle; a later source correction needs
a fresh preparation. The original single-author commands remain compatible.

On a failed check, stop dependent work and preserve the recovery evidence.
Do not silently continue after a partial mutation, overwrite conflicting files,
restore the whole source tree to evade scope checks, or relabel old evidence as
a review of new bytes. Retain earlier judgments and explain corrections,
including withdrawn false positives.

Human-only confirmations and dispute resolutions retain their existing guards.
Parallel preparation, a snapshot or an agent verdict cannot create protected
human records. Publication and claim ownership remain separate gates.

## Isolated draft workers

External worker creation and promotion require an idle canonical workspace.
The native lead uses `create --native --task TASK` during its own single-session
run, normally without copying a large build cache. It receives authored candidates
with `collect ID --by LEAD`; this command is native-only, without a `--native`
flag. Checked workers may instead use `promote --native`. These paths verify the actual
active parent run/session and process ancestry, the bound task and explicit
scope, and excludes another active run. It retains build/dependency freshness,
ownership, protected-file and serial canonical integration checks. Workers must
return their handoffs to the lead; they cannot promote themselves. Do not nest
canonical runs or bypass the external idle guard.

Provision worker checkouts serially because creation updates the shared registry
under the canonical boundary lock. Start each independent author as soon as its
worker is ready, then provision the next worker while that author proceeds.
Concurrent creation or collection commands can collide on the same lock; source
authors remain parallel once their isolated workers exist.

Create workers from a clean public working tree matching the canonical
`.archon-horizon/vcs/workspace.git` HEAD. This is the source ledger, not the
user's `.git`. Ownership is limited to explicit Lean node files:

```sh
homalg workspaces create draft-a --author ACTUAL_AUTHOR_SESSION \
  --task Example2000.STMT.1 --file HomAlg/Example2000/Def_A.lean --copy-cache
homalg workspaces status draft-a --json
# Author only the assigned files in the returned checkout.
homalg workspaces check draft-a --by ACTUAL_CHECKER --timeout 1800
# At the authorized idle canonical boundary:
homalg workspaces promote draft-a --by ACTUAL_INTEGRATOR
```

Inside the authorized native lead session, add `--native` to `create` and
`promote` and bind the worker to that session's registered task. The runtime
constructs a public source projection with its own isolated ledger; runtime
configuration, engine history and private state are not worker source inputs.
Checks and source edits use the worker root. Canonical promotion remains serial.

For source-only native workers, use this sequence instead of copying the cache:

```sh
homalg workspaces create draft-a --native --task "$ARCHON_HORIZON_TASK" \
  --author ACTUAL_AUTHOR_SESSION --file HomAlg/Example2000/Def_A.lean
# Native workers author their isolated, disjoint files and return frozen handoffs.
homalg workspaces collect draft-a --by ACTUAL_NATIVE_LEAD
horizon check HomAlg.Example2000.Def_A
# Continue required canonical export, independent review and exact stage gates.
```

`collect` checks the actual native caller, task/scope, baseline and dependency
inputs before serially staging only owned candidate bytes. It deliberately does
not require worker compilation and records the candidate as uncompiled and not
accepted. This is the same pending-check state as an ordinary native source edit.
The lead must run current canonical checks and required fresh export, independent
fidelity review/registration, stage checks and the outer hook before acceptance.
Source isolation permits parallel authors while the canonical build uses one
serialized lane. Collection never supplies compiled evidence or a fidelity lock.
The external idle-only `promote` path still requires its current worker check.
Native source-only writers return durable candidate files without making Git
commits. In particular, they must not run the parent's inherited `hgit` wrapper:
its explicit ledger variables can still name the canonical root despite a worker
cwd. Collection records the actual author in the source-ledger commit. Read-only
worker Git inspection must explicitly use the worker's own ledger/root.
For worker shell commands, use the returned `author_commands` prefix, for example
`homalg workspaces exec --repo /absolute/canonical draft-a -- git status --short`.
It runs at the worker root with native routing, parent Git/ledger variables and
inherited lock claims removed, and holds the worker lock while the command runs.
`HORIZON_BIN` stays pinned. This prevents an inherited parent `hgit` route from
silently selecting canonical state; it does not authorize edits outside ownership.

Do not invoke Lean LSP/diagnostics against source-only worker paths: the language
server can bootstrap a cold Lake environment before reporting any diagnostics.
The lead can check an exact frozen candidate with the warm canonical
`horizon check --lean ABSOLUTE_CANDIDATE` lane while other authors continue.
This supplies candidate compilation evidence only; after collection the real
canonical module/export, source-fidelity and stage/session gates still apply.
Private `literature/<Doc>/ingest.yaml` remains outside the public worker snapshot
and public-context comparison, while the ordinary private-source gates retain
their responsibility for it. Force-tracking it in a source snapshot is refused.

Use a real registered task ID. With `--task` and no `--file`, ownership comes
from its explicit Lean leaf paths; supplied files must be a subset. The task's
objective and scope are bound and later changes prevent promotion. Without
`--task`, this is an unbound draft and changes no task state.
`--dependency PATH` can be repeated for additional explicit inputs.
`--copy-cache` copies independent Lake cache files; it does not create shared
hardlinks or symlinks. Imported package sources must be available for a worker
build. Source-only native workers defer compilation to the canonical build lane.

State lives under `.archon-horizon/draft-workspaces/ID/`. Each worker has its own
checkout, ledger, `.lake` and check lock. Its `.git` pointer resolves only to
its own ledger, preventing nested Git or Lake commands from finding the parent
repository. It does not inherit the live task queue,
private references, hooks or publication configuration. `record.json` retains
the author, source-ledger baseline, ownership and input hashes. Author identities
are recorded provenance, not cryptographic attestations.

`check` invokes the pinned Horizon's real `check` on the owned modules and
requires current source, dependency and toolchain inputs. It retains
`checks/<timestamp>/stdout.txt`, `stderr.txt` and `result.json`. Read the
returned `ok` and `check_current` fields; a subprocess return code alone is not
accepted evidence. A failed compilation returns exit 3. This check is not source
fidelity, an independent reviewer report or a formal task evaluation.

`promote` requires an idle canonical workspace unless the native lead satisfies
the `--native` checks above. It holds the native run-policy, boundary, check and
registry locks. It refuses changed owned files, stale
dependencies/check inputs, changed task metadata and writes outside ownership.
It copies only authorized node changes and commits through the source ledger,
preserving the user's Git and unrelated staged work.

The `promotion.json` journal preserves recovery information. Individual file
replacement is atomic, but multi-file promotion is a recoverable transaction,
not a filesystem-wide atomic event. On failure, only still-matching worker
writes are restored; external conflicts remain visible as `recovery-required`.
There is no automatic rebase, recovery or deletion command. Retain the worker
and journal for coordinated recovery rather than overwriting a conflict.
For a stale unintegrated draft with no recovery required, explicitly release
ownership at an idle boundary with `homalg workspaces retire ID --by OPERATOR
--reason TEXT`. Retirement preserves the checkout and all evidence; a new ID can
then acquire the paths. Promoted, already-retired and recovery-required workers
cannot be retired. Do not edit registry state to release a lease.
Promotion does not register fidelity, complete a task or run final session hooks.


## Delivering a task for independent review

After scoped authoring and any worker promotion, use the canonical checkout and
an existing registered `STMT`, `CITED` or `PROOF` task. Each formal node must have
real main declarations. Informal and pruned nodes are omitted from this delivery.
Use a new evidence path under this checkout's `build/`; evidence commands refuse
existing files and paths escaping that directory, including symlink escapes.

```sh
homalg workflow prepare Example2000.STMT.1 \
  --author-session ACTUAL_AUTHOR_SESSION \
  --node Example2000.Def_A --node Example2000.Def_B \
  --out build/delivery-001.json
homalg workflow verify build/delivery-001.json
# The actual independent reviewer now reads the frozen source and writes
# complete per-node reports with the real provenance and required honesty review.
homalg workflow review-snapshot build/delivery-001.json \
  --out build/review-inputs-001.json
homalg review-fidelity-batch Example2000.Def_A Example2000.Def_B \
  --by ACTUAL_REVIEWER --session ACTUAL_REVIEW_SESSION \
  --author-session ACTUAL_AUTHOR_SESSION --snapshot build/review-inputs-001.json
homalg stage-check Example2000.STMT.1
```

`prepare --node` can be repeated to select that actual author's formal nodes
from the registered task; omission selects all formal task nodes. The handoff
orders its selection by task path. Never invent a common author identity for
several authors. Read its exact `node_ids` before registration.

After review, repeated `review-snapshot --node` selects a subset within that
author's handoff, in the order to be passed to the batch command. Split these
snapshots and registration batches by actual reviewer provenance. Omission
selects the whole handoff. The direct snapshot command below is also available
when no author-handoff linkage is needed; it still requires current real reports.

`prepare` performs a fresh compilation/export and structural, dependency and
compiled checks without merging its export into committed `nodes.json`. This is
an author preflight, not full repository acceptance: derived-cache consistency
rules `nodes-json-fresh` and `nodes-json-stale` are explicitly deferred/reported
as skipped here, and remain required in the final stage/session checks. Regenerate
roots when authored module selection changes; do not run an extra export solely
to refresh committed caches before preparation. Inspect `ready_for_review`,
findings, deferred/skipped checks and `pending_review_renewal`.
Only well-formed existing agent locks within the task scope requiring renewal
are reported as pending independent review, including other same-task sub-batches.
Validation still covers the document. Human locks and other validation errors remain
errors. A failed delivery cannot be used by `verify` or `review-snapshot`.

`verify` checks the task objective/scope, formal node selection and normalized author
inputs. It performs no compilation and grants no approval. Write the actual
independent reports after that author handoff is stable. `review-snapshot`
verifies the handoff, binds completed reports and strict compilation inputs, then
verifies the author handoff again. It does not supply a missing review or repair
an unsatisfactory report. Changed author inputs require a fresh delivery and an
assessment of which reviews must be repeated.

After a successful stage check, the native lead performs the prescribed task-set
action, preserves its evidence and returns control to Horizon. It must not manually
invoke `homalg after-session` or add an extra `homalg plan --advance` as a session
finalization step. The engine runs the configured outer hook, including eligible
advance planning. The outer coordinator waits for that hook and verifies its actual
private/scope checks, validation, evaluation and resulting task state before
reporting final acceptance.

An explicitly authorized external recovery operator follows a separate protocol:
retain its actual session directory, identities, start/end ledger SHAs and required
private snapshot and run the same applicable completion checks. This exception
does not move engine finalization into a native lead session. Do not invent native
session metadata or infer completion from a hook exit code alone.

## Choosing the next task and proof scope

```sh
homalg plan Example2000 --proofs deferred
homalg workflow next Example2000 --json
# Select an actual ready task explicitly through the ordinary native runner.
```

For a dependency-based statement frontier, enable node units explicitly:

```sh
homalg plan Example2000 --proofs deferred --statement-frontier --statement-batch-size 4
homalg workflow next Example2000 --json
```

`--statement-frontier` persists independently executable statement units beside
the existing chapter acceptance stages. `--statement-node NODE` may be repeated
to restrict that frontier to explicit primary nodes. `--statement-batch-size`
persists a maximum of 1–16 independent node groups per native statement task;
the default is 4. Each group includes its primary node and relevant auxiliaries.
Only dependency-ready independent groups are batched. Registered scopes and
existing operator holds are preserved; a later sweep does not enlarge an active
batch or duplicate its owned primaries. The native lead dispatches its distinct
author groups concurrently and serializes canonical collection/acceptance.

The frontier checks the actual source pages, complete source prose, metadata,
statement dependencies and current compiled/review evidence. Local blockers do
not hold unrelated ready groups. A deferred proof dependency remains recorded;
it does not grant a missing construction certificate or supply data from an
unproved existence claim. Node-unit completion does not claim that the parent
chapter's inventory, DAG, statement coverage or full acceptance is complete.
Read `workflow next` as current evidence and recommendations; it still does not
dispatch a native run by itself. Use `--no-statement-frontier` for the ordinary
chapter scheduling mode without deleting registered units or their history.

`plan --proofs deferred|included` stores the selected mode in the plan overlay;
subsequent `plan --advance` inherits it unless explicitly overridden. Omission
with no previous mode keeps the existing `included` behavior. `deferred`
prevents creation of new `PROOF` tasks. It does not cancel, remove or rewrite
already registered proof tasks or relax any task's completion conditions.

`workflow next` is a read-only recommendation based on current planner
prerequisites and existing compiled evidence. It does not compile, create tasks,
change priorities/status, or dispatch a session. Read-only here permits normal
coordination lock files; it does not mutate authored manifests or task state. It lists `ready`,
`requires_plan`, `running` and `held` separately. Only already queued, currently
eligible tasks appear in `ready`; an eligible proposal in `requires_plan` still
needs ordinary planning. Existing blocked or otherwise held status is preserved.

The order favors ready definitions, cited interfaces and statements, followed by
DAG/inventory/source prerequisites, then proofs. Source batches nearest to
completing a chapter prerequisite come first. The command inherits the plan's
proof mode; `workflow next --proofs ...` overrides only this recommendation.
Use explicit task selection, especially when an old queue still contains proof
tasks that are now deferred.

## Registering reviewed nodes together

After actual independent reviews are complete, select unique node IDs from one
document with the same real author/reviewer provenance. Every selected node needs
its own current satisfactory report, including any required honesty review.
The commands below use one provenance group; when it differs, use separate
batches or the [typed cohort workflow](REVIEW_COHORTS.md). Its manifest retains
each genuine group instead of assigning a common author or reviewer.
The snapshot command freezes inputs and
does not compile, approve or modify a node lock. Its output must be a new file
below the local `build/` directory:

```sh
homalg review-fidelity-snapshot Example2000.Def_A Example2000.Def_B \
  --out build/review-inputs.json
homalg review-fidelity-batch Example2000.Def_A Example2000.Def_B \
  --by ACTUAL_REVIEWER --session ACTUAL_REVIEW_SESSION \
  --author-session ACTUAL_AUTHOR_SESSION --snapshot build/review-inputs.json
```

The batch command performs one fresh build/export for the document, validates all
selected reviews, then writes their separate locks under the shared workspace
lock. It returns the per-node locks in `data.locks`. It has no `--human` option;
the existing single-node command and human guards remain available separately.
`--snapshot` is optional at the CLI, but coordinated handoffs should supply it to
bind registration to the exact completed review inputs.

The version-1 `fidelity-input-snapshot` binds the repository, ordered node IDs,
reports and compilation inputs: local Lean sources, package/path dependency Lean
and configuration files, tool selection and available toolchain binaries,
schemas, HomAlg tooling, document/foundation metadata and policy. File fingerprints
include hashes and filesystem identity/times. Touching, replacing or changing a
file and restoring its old bytes can therefore invalidate the snapshot. Do not
manually rewrite the snapshot to make a stale handoff pass.

The context also binds taxonomy/schema metadata, inventory, synthetic source
fixtures and the relevant private TeX pages for selected nodes and their declared
dependencies/local import closure, using printed pages plus the PDF offset.
Author handoffs bind only the relevant page projection and top-level PDF identity
from the transcription manifest; unrelated future-page updates need not stale
that handoff. Final review snapshots bind the full relevant transcription
manifest's hash and filesystem identity, so any manifest change requires a new
final snapshot. Neither command rehashes the full PDF/PNG binaries: their
registered identity is the boundary, not a fresh binary-source verification.

A snapshot made through `workflow review-snapshot` also binds the handoff's actual
`expected_author_session`; batch registration must use that same author session.
The direct snapshot command has no author-handoff binding. Both are input records,
not approval records; the final batch command still checks all report/provenance
requirements. Compilation inputs remain conservative and repository-wide: do not
modify other canonical inputs concurrently with review/registration.

Author-delivery fingerprints are different: they normalize YAML serialization
and omit only a well-formed agent `fidelity.reviewed` envelope. Genuine human,
legacy and malformed review records remain bound. This permits later authorized
agent lock registration without pretending that arbitrary header edits preserve
the author's delivery. Final fidelity snapshots remain strict.

Transactions are recorded in
`.archon-horizon/cache/fidelity-transactions/*.json`. A transaction moves from
`prepared` to `committed`, `rolled-back` or `recovery-required`. On failure,
rollback restores only this batch's writes that still match the expected bytes;
it preserves conflicting external edits. An unfinished journal blocks subsequent
registration until recovery is assessed. These are recoverable multi-file
transactions, not a claim that several files change atomically to every observer.

The workspace lock coordinates cooperating build and registration commands. It
does not make the entire filesystem read-only. Input checks before and after
export and during registration reject detected concurrent edits. Do not run
uncoordinated writers against a frozen review set.

## Transcription boundary

Vision-only transcription may be prepared in explicitly assigned ignored
staging directories, at most five consecutive pages per dispatch. Keep all four
provenance headers and the actual author identity. The independent reviewer must
read every source image and the complete candidate text, including formulas,
footnotes and cross-page fragments. Clearly mark unreadable source symbols.

Staged candidates and their reviews are neither canonical page registrations nor
completed T tasks. Before authorized import, verify exact PDF, PNG and TeX hashes,
scope and genuine author/reviewer separation. Any review reused after import is
valid only for identical reviewed bytes and source inputs. The normal private
snapshot, landing, review, scope and session checks remain required.
Do not copy private page content into public reports or worker metadata.

## Measuring performance without reducing quality

Record measurements for a fixed, identified workload and toolchain:

- Actual elapsed time for preparation, compilation/export, review, registration
  and final validation; distinguish wall time from summed worker time.
- Number of build/export invocations, modules/nodes/pages covered, worker count,
  cache state and exact source/input revisions.
- Full successful and failed command records, test results, skipped coverage and
  recovery outcomes.
- Independent review coverage, stale-input refusals and unchanged scope,
  provenance, protected-field and finalization checks.

Report observed values only. One build/export per registration batch reduces
repeated invocation overhead; it does not promise a numerical speedup or fewer
source comparisons. Compare equivalent inputs and gates before attributing a
timing difference to batching. Synthetic tests, local warm-cache measurements,
real compilation and live workflow acceptance are different kinds of evidence.

## Documentation sources and refresh

| Concern | Authored rules |
| --- | --- |
| Repository entry points | `AGENTS.md`, `CLAUDE.md`, `HomAlg/AGENTS.md`, `README.md` |
| Mathematical and review policy | `docs/CONVENTIONS.md`, `docs/REVIEW_POLICY.md` |
| Runtime and acceptance | `docs/ENGINE.md`, `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION.md` |
| Focused author actions | `docs/playbooks/` |
| Generated task objectives | `horizon/tasks/*.md` |
| Installed agent and skill instructions | Horizon fork's `src/archon_horizon/subagents/descriptors/` and `src/archon_horizon/skills/` |
| Public manual | Separate HomAlgDB Wiki repository |

Change the authored rule sources, test them, then refresh installed resources
through the supported installation/update path. Do not patch a running
formalization checkout's installed `.claude/` or `.codex/` copies as a substitute
for updating the source templates. Keep pinned release claims accurate: source
changes are not evidence that an older published wheel contains them.
