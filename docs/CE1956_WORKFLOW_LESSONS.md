# Cartan Eilenberg workflow lessons

Updated 2026-11-05. This record captures operational experience from registering
and processing `CartanEilenberg1956`, including the user's corrections to scope
and scheduling. Use it when changing the formalization workflow. The objective
is more faithful, compiled definitions and theorem statements per unit of time,
with independent review and source traceability preserved.

The governing execution contracts remain [PARALLEL_WORKFLOW.md](PARALLEL_WORKFLOW.md),
[REVIEW_POLICY.md](REVIEW_POLICY.md), and [CONVENTIONS.md](CONVENTIONS.md).
This record identifies observed failures, tested improvements and outstanding
work; it does not silently change protected commands or acceptance gates.

## Owner instructions that must survive handoffs

- Process the requested Cartan–Eilenberg book, not the earlier Hochschild pilot.
  Check the document key, registered PDF identity, claim and workspace before
  dispatching work. Registration and claim were completed through PRs 21 and 22.
- Formalize definitions and complete theorem statements. Formal theorem proofs
  are deferred. A named, source-documented theorem may contain `sorry`; a hollow
  definition, an arbitrary replacement proposition or an assumed conclusion
  does not satisfy this scope. Construction certificates may still need proof
  when they are necessary to provide genuine mathematical data.
- Use the dedicated Horizon `0.1.5+homalg.1` environment. Verify the actual
  executable inside native sessions as well as at the coordinator's shell.
- Ask about genuine ambiguity promptly, while continuing independent work.
  A problematic glyph or lemma must not automatically suspend an entire chapter.
- Parallelize useful authoring and independent review. Complete shared canonical
  acceptance through its normal coordinated boundary.
- Keep documentation consistent with delivered behavior. Distinguish local
  source changes from published code, Wiki pages and installed release wheels.
- Record accumulated experience here and use it to guide later improvements.
  Do not repeatedly stop book work for additional optimization rounds.
- Native Horizon owns formal book-task execution and its acceptance gates. The
  outer orchestrator coordinates Horizon and external subagents, prepares the
  next tasks concurrently, relays actual owner decisions and verifies outcomes.
  Preparation must not replace native execution or count as accepted progress.

## Keep execution inside the intended orchestrator

External operator sessions produced real source checks and receipts, but their
activity was absent from the native Horizon run log. Separately authored Lean
drafts were also absent there. Reporting that Chapter III had “started” without
distinguishing these activities from a native statement task left the owner
unable to verify progress in the expected dashboard.

The corrective instruction is to let native Horizon own formal task execution,
its internal parallel delegation and acceptance. While Horizon runs, external
subagents may prepare bounded downstream inputs, dependencies, handoffs and
documentation in disjoint scopes. These inputs retain their real authorship and
review status and enter native execution through normal checks. The outer
coordinator provides exact tasks and preserved inputs, monitors real process and
session state, relays questions and owner decisions, and inspects actual results.
Do not turn an accepted recovery mechanism into the default execution path
without the owner's agreement.

Preserve useful existing inputs with their real provenance. The three externally
written Chapter III code drafts remain uncompiled and mathematically unreviewed;
handoff is not acceptance. External authors stopped at their frozen inputs.
Standalone draft cache copies were cancelled, with partial destinations retained
and marked unusable as validated caches. Native execution resumed as run `0014`
on `CartanEilenberg1956.T.10`, explicitly a source task rather than a completed
Lean statement task.
This cancellation does not prohibit subsequently assigned bounded parallel
preparation. Keep Horizon supplied with ready inputs while its current task runs.

## Keep blockers local and keep code moving

The central scheduling failure was allowing a small source uncertainty to hold
an entire chapter while later chapters accumulated source preparation. Chapter
III had five canonically reviewed pages and fifteen pending pages; six damaged
glyph sites on three pages delayed its remaining transcription batches. Chapter
IV preparation continued, but neither chapter had formal Lean nodes at that
checkpoint. Describing this merely as “progressing Chapter IV” obscured the
distinction between source preparation and formalization.

Maintain a dependency-based work queue. For each unresolved issue, record its
exact affected pages or nodes, the decision needed, dependent work that must
wait, and available work that can proceed. Preserve the question while assigning
other ready definitions, statements, independent reviews or source sections.
Do not interpret an unanswered question as approval.

Prefer source sections or coherent definition groups as preparation units. A
coarse registered task may still require several units for final acceptance;
that does not prohibit preparing an unaffected unit in isolation. Do not claim
the coarse task is complete or bypass its prerequisites. If the scheduler cannot
represent useful smaller units, record that limitation for a scoped workflow
change while continuing the work its current contracts permit.

Keep a bounded amount of future transcription ready, then give freed capacity
to formal code and its missing interfaces. Hundreds of staged pages do not make
up for a stalled definition frontier. A useful dispatch names the exact files,
source span, prerequisite interfaces, actual author, independent reviewer and
next acceptance step. Reassess assignments when new evidence or an owner answer
unblocks a higher-priority item.

The Chapter III recovery provides a concrete parallel pattern: three original
authors repaired their own T8, T9 and T10 candidates concurrently; distinct
reviewers rotated across the batches. Already reviewed section 1 could be
inventoried concurrently. Only canonical imports and their final hooks needed
serialization.

## Source decisions and mathematical fidelity

Read scan images directly; do not use OCR or the PDF text layer as mathematical
evidence. Preserve literal source text, including readable errors. Record the
original wording and an adopted correction separately, with the actual decision
and precise location. Distinguish a damaged scan, a transcription mistake, an
unusual but readable notation, and a mathematical error.

Five mathematical repairs were explicitly adopted during this task: the p4
quotient target, the p13 principal-ideal assertion with its corrected hypotheses
and zero-ideal boundary, the restriction `n > 1` in Exercise I.6, the mixed
endpoint formula for simultaneous homotopy on p63, and replacement of the second
summand `T(Q',N)` by `T(N,Q')` in both III p50/PDF72 equations (6a) and (7a).
The fifth repair concerns only Theorem III.7.1's proof formulas; its same-sign
commutation statement, the partial-satellite definition and other nodes are
unaffected. The actual owner decision was relayed as `I-0034`; it does not itself
resolve the protected `I-0033` record, grant independent review, or certify any
completed Lean code or proof. Preserve literal source and the separate correction,
and do not repeatedly ask the owner to approve the same mathematics.

The later-printing decision is separate. The owner adopted the 1999 Princeton
printing for exactly six unclear glyph sites: three overbars on p40, the lower
vertical double stroke on p45, and two equality signs on p51. Keep the registered
1956 scan and its unreadable evidence. Annotate the adopted secondary witness,
printing and page locations instead of claiming the original scan became clear.
The earlier proposed tilde reading was superseded by the independently observed
overbars; retain that history rather than silently rewriting it.

Actual owner decisions and guarded human records are different things. Store the
decision once and route any required protected registration through its existing
guard. Never impersonate a human or invent a confirmation. A delayed registration
must block only the work that actually depends on it. Independently reviewed
routine foundations and definitions use the enabled agent-review policy.

Changed candidate pages need review of their actual new bytes and source inputs.
An unchanged page can retain a genuine prior complete review when source and
candidate identity still match; say explicitly that this is reused coverage.
Do not claim a fresh visual read that did not happen. Freeze author handoffs
before review, then freeze completed review evidence for registration.

An earlier satisfactory T5 review missed a module-side mismatch. The reviewer
preserved that report and withdrew its use as current acceptance evidence.
Give diagrams, module sides, variance and small relational symbols explicit
attention. Before reporting a new discrepancy, compare the exact bound TeX
bytes with the source; retain and correct a mistaken allegation as openly as a
missed error. More gate invocations do not replace careful comparison.

## Produce real formal content

Inventory scaffolds with `decls: []` are legitimate temporary planned nodes. They
are not completed definitions or statements. A long directory of comment-only
Lean files is a warning about the implementation frontier, not evidence that
formalization is nearly complete.

Group related source occurrences into coherent nodes. The Chapter IV first-half
draft contained 84 occurrences; independent review recommended grouping them and
retaining proof-local constructions as proof support or justified auxiliaries.
The occurrence count must not become an automatic quota of 84 primary files.
Preserve every source occurrence even when several belong to one node.

Determine section boundaries from the body, including the next page, rather
than only the contents list or running header. On printed p37, the running
header names section 2 while Propositions 1.3, 1.4 and 1.5 still precede its
body heading. Stopping section 1 at p36 would omit three statements even though
the next page had already been reviewed.

Preserve the book's mathematical objects and generality: variance, arbitrary
index families, grading, module sides, hypotheses and construction route all
matter. Approved elementary Mathlib support is useful, but a Mathlib replacement
does not by itself formalize the source definition. In particular, a satellite
construction needs genuine object and morphism data; choosing data from an
unproved existence assertion is not an acceptable shortcut.

Before allocating downstream writers, settle the shared interface or explicitly
freeze the provisional dependency. An API gap should become a small concrete
prerequisite task. Make necessary interface work visible rather than spending
many workers on downstream drafts that will all need revision.

### Statement acceptance does not establish every consumer's prerequisites

The native SprintIII honesty audit at source-ledger `1e3e20df69241aa0c47af784f91d25d7e49eb4a1`
found a concrete dependency boundary. `Prop_III_1_1` and `Prop_III_1_1a` each
contained six admitted comparison laws despite satisfactory STMT locks. Those
locks cover accepted statements; they do not prove the laws. First-satellite
functors need independence, identity, composition and additivity as construction
certificates. When consumed for that purpose, these laws become required proof
prerequisites. The existing concrete comparison constructors need no rewrite.

Chapter I exposes the same distinction. `Con_I_injective_step` and
`Con_I_injective_transfinite_extension` already provide the step quotient,
recursive stages and final embedding, but their required monomorphism,
transition/union and injectivity certificates remained admitted at that snapshot.
A sorry-free embedding does not establish injectivity of its target. Calling an
admitted injectivity theorem, or choosing a witness from admitted existence,
cannot certify a genuine injective copresentation.

Native SprintIII is repairing these prerequisites; this is ongoing work, not
completed construction or chapter acceptance. Native Horizon owns the scoped
repairs and fresh independent review, preserving existing statements, source
proof prose and authorship. Ordinary theorem proofs remain deferred when they
are not required to supply the constructed data or its defining laws. Before
dispatching a consumer, inspect the certificates it actually uses: a producer
node marked done does not by itself establish that the consumer is ready. Keep
unaffected connected-sequence work moving while these local prerequisites are
proved; neither broaden the task to all theorem proofs nor weaken its data checks.

## Parallel authorship and acceptance

Use disjoint ownership in isolated source checkouts, with separate build paths
and fixed dependencies. The author must not approve their own mathematics.
Preserve the real author and reviewer identities across external staging,
native sessions and coordinator imports; the coordinator is not a substitute
reviewer.

Batch operational work where the implemented contract permits it. Fresh batch
fidelity registration can share one build/export while retaining each node's
complete review and compiled hashes. Author preparation and final registration
remain distinct phases, each with its required fresh checks. A successful
worker compilation or promotion does not complete a task.

Coordinate canonical writers, generated roots, manifests, the private repository
and session finalization. Wait for the real outer hook, validation, scope result,
private-source checks and resulting task state. Do not infer completion from an
agent's final message, a subprocess exit alone or a task's early status update.
An external operator can be active even when `horizon ps` shows no native run;
track its actual process handle and shared lock as well.

**Keep finalization outside the native lead.** INV16 manually ran `after-session`
inside its session (219.68 s), then an additional `plan --advance` (207.49 s).
Both returned zero, but neither receipt establishes completion of the framework's
configured outer hook. Return after the prescribed in-session checks and task-status
action; let the engine finalize, then have the coordinator inspect the result.
The outer hook already advances eligible planning. These timings describe this
incident, not a performance benchmark or a reason to remove acceptance checks.

**Refresh compiled records after scaffolding.** INV16's initial full validation
failed on stale `nodes.json`. The supported `homalg export-lean --doc
CartanEilenberg1956 --json` refresh succeeded, and the subsequent full validation
returned zero with 275 warnings and 14 contextual skips. Preserve both attempts;
export success alone is not validation or statement completion. Planned-node TODO
warnings remain evidence of unfinished later stages.

**Treat the blueprint as a generated snapshot.** Nodes created after the round's
initial projection can remain absent from that view until the next refresh.
Check authored headers before interpreting the omission as missing work. Use the
normal next-round refresh, or supported projection commands when same-round graph
visibility is necessary; never hand-edit generated files or repeat finalization
merely to refresh the view. INV16's refreshed projection contained 42 Chapter III
planned nodes and zero new Lean declarations.

## Operational failures and their consequences

| Observed issue | Required operational response |
| --- | --- |
| A native login shell selected upstream Horizon instead of the dedicated fork | Pin the executable path and disable login-shell reordering; verify inside the actual session. The observed mismatch was upstream 0.1.5, not evidence of 0.2.0. |
| Legacy backup created a commit in the user's Git history before a network failure | Preserve the real incident. Route source operations explicitly through the separate ledger; test actual user HEAD, index and config preservation. |
| SSH transport failed while authenticated HTTPS worked | Use the scoped transport wrapper with existing authentication. Avoid persistent credential/config changes and do not claim a failed backup succeeded. |
| The private backup branch had different legacy ancestry | Preserve ancestry and use an audited unchanged-tree merge followed by an ordinary non-force push. Keep private backup history separate from public submission. |
| A T7 hook was interrupted after private-source changes had already committed | Preserve the failed receipt and partial state. Recover the exact interrupted boundary; do not blindly replay the importer. |
| A generic importer rejected a non-body `[illegible]` annotation on T11 | Inspect the actual scope of uncertainty and use a properly reviewed normal path. Do not erase uncertainty just to satisfy a parser. |
| A valid T8 review used a confidence string outside the importer's accepted vocabulary | The actual reviewer preserved the old report, normalized only the machine field and retained its secondary-witness qualification separately. Do not manufacture a stronger verdict. |
| The live draft-worker creation refused a source ledger containing root `config.yaml` | Retain the refusal and inspect the live-layout mismatch. This route remained unresolved at this checkpoint; synthetic worker acceptance did not prove compatibility with every live ledger. Do not drop tracking or weaken the guard merely to make creation pass. |
| A successful site log lost its tool exit receipt during context compaction | Preserve that log and repeat only the missing acceptance step with an explicit exit receipt. Do not claim success from the final log line alone. |
| Three speculative standalone Lake cache copies added setup work before any draft compilation | Avoid preparing large environments without a measured need. Those copies were cancelled when execution was returned to native Horizon; their incomplete caches confer no validation. |
| Updates repeatedly said “restart” after book work had already resumed | State whether a process is active, a batch ended, the next batch is being dispatched, or work is intentionally paused. Do not hide an additional optimization pause behind ambiguous progress wording. |

## Measured improvements and their limits

### Live Chapter III scheduling audit (2026-11-04)

Native run `0015` spent 1,988.77 seconds in INV.16 and produced 42 Chapter III
planned nodes with no declarations. Run `0016` spent 1,331.67 seconds in DAG.3
before interruption, still with zero Chapter III canonical declarations. Its
stage check and early task-status action passed, but that does not establish the
interrupted session's outer acceptance. Preserve its exact recovery boundary.

The phase receipts expose infrastructure work inside both mathematical tasks:

| Recorded phase | INV.16 | DAG.3 |
| --- | --- | --- |
| Full `make test` | 212.68 s | 223.49 s |
| `make site` | 18.93 s | 17.12 s |
| First `make validate`, failed on `nodes-json-fresh` | 134.88 s | 124.01 s |
| Successful `make validate` retry | 160.73 s | 189.89 s |
| Explicit compiled export | 35.62 s | 45.85 s |
| Exact stage checks | 9.21 s and 7.14 s | 90.95 s |

These intervals overlap; their sum is not elapsed session time or a proven
critical-path saving. `make test` includes Python/site regressions and npm setup;
`make validate` includes synthetic Lean smoke/export tests in addition to full
validation. Both freshness failures are preserved rather than relabelled success.
INV.16 additionally ran the duplicate finalization/planning recorded above.
Three DAG.3 scoped axiom-audit checks took 2.77, 3.12 and 2.02 seconds of compiler
time but waited 73.44, 60.09 and 32.42 seconds for the shared build lane.
Under the later bounded preparation authority recorded in I-0035/I-0036, that
run checked the three frozen Chapter III prototypes: 10 presentation-relative,
38 unary-interface and 29 induced-map authored declarations, with no transitive
`sorryAx` in their recorded audits. These separate receipts supersede the earlier
uncompiled observation for those exact bytes without rewriting its history.
They still establish no canonical adoption, independent source-fidelity verdict
or completed Chapter III formal node. Preserve and assess these usable inputs
instead of repeating already evidenced unchanged preparation.

Earlier chapters also had source-only stages; the difference is not that those
stages once counted as Lean code. Source-ledger comparisons show:

| Chapter | Inventory session | DAG session | Later real implementation |
| --- | --- | --- | --- |
| I | 17 min 19 s, 74 planned nodes | 14 min 22 s, zero declaration-bearing nodes | STMT.1: 38 nodes with 89 header-listed main declarations; two locks still blocked acceptance |
| II | 13 min 41 s, 82 planned nodes | 17 min 09 s, zero declaration-bearing nodes | Interrupted STMT.2 authored 53 nodes with 195 header-listed main declarations; the next session completed reviews |
| III | 33 min 09 s, 42 planned nodes | 22 min 12 s before interruption, zero declaration-bearing nodes | No canonical Chapter III statement implementation at this checkpoint |

Header-listed main declarations are not the count of all exported helpers,
constructors or projections. Chapter I/II DAG and statement reports left global
infrastructure suites outside those native sessions, whereas INV.16 and DAG.3
executed them internally. Chapter III also introduces genuine presentation and
comparison-map prerequisites for first satellites. These do not block the
connected-sequence definition, whose recorded statement dependencies are existing
Chapter I/II interfaces; its map definition follows that interface. Do not turn
the difficult first-satellite construction into an artificial whole-chapter order.

The corrected operating profile reserves full `make test`, `make validate` and
`make site` regressions for tooling/schema/site changes. Mathematical sessions
retain current scoped checks, required fresh export, independent fidelity review,
exact stage checks and the engine-owned final validation/hook. Source Statements,
complete source Proof prose, DAG annotations, node comments, metadata and generated
blueprint freshness remain obligations. Changing scheduling or check ownership
does not reduce their quality requirements.

Use native-owned isolated authoring and serial canonical collection/checks rather
than speculative large worker cache copies. Source-only collection explicitly
stages uncompiled candidates; no fidelity or completion follows from collection.
See the guarded native workflow in [PARALLEL_WORKFLOW.md](PARALLEL_WORKFLOW.md).
Dispatch independent ready work before joining, and keep housekeeping and source
questions local. The live acceptance experiment must demonstrate new genuine
compiled Chapter III content with independent review and the real outer receipt,
while unaffected work proceeds beside a local block. Source-only DAG progress,
prepared helpers and passing infrastructure tests cannot satisfy that experiment.

The tested workflow adds isolated drafts, frozen handoffs, batch fidelity
registration and read-only next-task recommendations with persisted proof mode.
One warm synthetic comparison on an earlier implementation, before the receipt
fix, measured two-node batch registration at 10.55 s versus 25.78 s for two
separate registrations. A later complete prepare/review/registration trial took
10.73 s for preparation and 12.77 s for registration, retaining a fresh
build/export in both phases. These measurements do not determine whole-book
throughput or compare the final installed version's live CE tasks.

A subsequent narrow implementation reused immutable status history within a
validation context and node/inventory reads within one planning call. Three
paired synthetic trials gave the following medians, with identical outputs:

| Operation and fixed workload | Before | After | Preserved result |
| --- | --- | --- | --- |
| Proposal construction, 156 nodes and 18 chapters | 61.822 s | 0.425 s | All 108 proposals; header parses reduced from 25,584 to 156 |
| Scope rule, 156 nodes and five status commits | 2.182 s | 0.262 s | All 156 findings; Git subprocesses reduced from 1,092 to 8 |

This reused inputs rather than approval or validation verdicts. Per-node scope,
claim, policy and time checks, task prerequisites and the three export snapshots
were preserved. The complete isolated checks passed: 542 Python tests, 38 site
tests and 19 Lean smoke/export tests. Context skips and existing warnings remain
explicit; the npm run also reported 12 moderate advisories with unchanged locks.
See [IMPLEMENTATION.md](IMPLEMENTATION.md) for exact revisions and evidence.

Measure real phase durations before choosing the next optimization. A 277-second
interval in an earlier hook included several operations; it was not a measured
planning duration. Record workload, cache state, invocation counts, output
equivalence and actual exits. Do not extrapolate microbenchmarks to CE task time.

## Progress reporting

Report these quantities separately, with the source of each count:

- Canonically reviewed source pages and unresolved source locations.
- Inventoried occurrences and planned nodes with no declarations.
- Genuine compiled definitions and complete compiled Lean theorem statements.
- Current independent fidelity approvals and reopened or pending reviews.
- Deferred formal proofs, necessary construction prerequisites and external
  obligations.
- Tasks accepted through the full session protocol, verified backups and public
  submission state.

Prefer a small verified increase in formal content to a large ambiguous task
count. “Statement complete” requires the whole mathematical claim, including
hypotheses and conclusions. A chapter is not formalized merely because its
transcription, inventory, definition subset or local compilation passed.

When the owner asks for status, answer the question directly and continue useful
work. Explain a local block in terms of its actual impact. Do not describe later
source preparation as later-chapter Lean formalization, and do not repeatedly
ask permission for an already authorized action.

## Next workflow improvements

Apply these incrementally while book work continues. A change is complete only
when its real acceptance condition is checked and its documentation matches.

| Priority | Improvement | Acceptance condition |
| --- | --- | --- |
| Done 2026-11-05 | Track blockers and ready work at page/node/definition-group granularity | One unanswered local source question leaves unrelated valid work dispatchable; no dependent result is falsely marked ready. |
| First | Make the formal-code frontier visible | Status separates planned headers, compiled definitions, full theorem statements and approved nodes. |
| First | Test the isolated-draft path against the actual live source-ledger layout | Reproduce the root runtime-config refusal in isolation and demonstrate safe creation without changing user Git, copying runtime/private state or weakening guards. |
| Next | Split preparation around stable mathematical interfaces and source sections | Independent workers produce usable checked code; a coarse stage's final gate remains intact. |
| Next | Normalize review interchange at handoff boundaries | Unsupported report fields are caught before canonical execution, while actual verdicts, qualifications and history are retained. |
| Next | Capture process, phase timing and exit receipts durably | Interrupted observation can resume the same live operation without restarting it or reconstructing missing evidence. |
| Later | Optimize remaining measured orchestration overhead | Equivalent-input measurements show improvement and unchanged prerequisite/validation coverage; unrelated ready mathematics continues. |

## Throughput audit and lane rollout (2026-11-05)

Between 2026-11-04 03:00 and 2026-11-05 00:53 UTC the engine ran one session at a
time. Of 21.6 wall-clock hours, native sessions ran 9.8 h, outer hooks 2.1 h and
the workspace sat idle 9.7 h, mostly two long gaps after interruptions and one
optimization pause, plus 5–16 minute gaps whenever a one-round run ended and the
coordinator relaunched. The one long run (`0018`, `--rounds 20`) was the most
productive period. Long runs are the default; one-round launches waste the gaps.

Within a typical four-node statement batch, writers finished in about five
minutes; preparation retries, reviewer start-up, four separate registrations and
the final checks filled the remaining 30 minutes, and the outer hook added 2.5–6
minutes, of which planning took 74–100 s and the fresh export 33–103 s. The hook's
export is deliberately not reused from in-session output: it is the outer check
that does not trust the session's own artefacts.

Blocking was coarser than the work. Three proof-only disputes (I.3.2, I.6.1,
II.4.5) held twelve nodes in three batches whose other nodes were already locked,
and the whole-chapter `SprintIII` task could never pass its stage check in one
session while overlapping every Chapter III unit. Responses now implemented:

- Node-level settlement narrows a failing unit to its passing primaries and
  releases the rest to the frontier; planning keeps disputed nodes out of
  batches. Tasks whose objectives were extended (for example the satellite
  prerequisite's certificate obligations) settle only when named explicitly.
- Concurrent lanes run several isolated sessions over one queue. Disputed units
  and private transcription run alone in the canonical workspace.
- Planning reuses parsed task files and the review policy while their file
  identity is unchanged.

The first end-to-end lane trial on a disposable copy of this workspace found two
defects that unit tests with absolute paths had hidden: the engine passed a
relative canonical root to sessions, and a relative `core.excludesFile` let the
shared mounts leak into session commits so every landing was refused. Later trials found two more:
concurrent sessions each rewrote the generated `nodes.json` and root import files,
so the second landing conflicted on them, and the hgraph parser's forked process
pool deadlocked inside the multithreaded lane process. Generated paths are now
declared in `workspace.session_generated` and never land from a session, and the
pool uses `spawn`. All four are fixed with regression tests. The final trial ran three real
statement units over two lanes with a scripted lead driving the actual native
worker, collection, `horizon check`, export, stage-check and ledger tooling: two
sessions ran concurrently, each landed and passed the real outer hook, and a
freed lane immediately claimed the third unit, which also landed, with no
conflicts. The scripted lead does no mathematics, so these trials validate
scheduling, isolation and landing, not authoring quality or Codex rate limits. Native draft workers needed explicit support for
isolated leads (control-plane paths in the canonical root, waiting for shared
locks, all lanes sharing one supervisor process).

## Separating authoring from review (2026-11-05)

A comparison with the owner's workspaces on the original Horizon, same model and
effort, showed similar session lengths and token use but two to four times the
declarations per session-hour there, with complete proofs. In CE statement
sessions, writers finished early and 55% of the session followed: repeated
full-document preparation and registration exports under the shared build lock,
three to six reviewer subagents, registration retries, and closing checks. Review
subagents used 57% of subagent compute, against 15–36% in the other workspaces.
Honesty review ran twice per node (registration required the registering
reviewer's own block), in source-only stages, and again as a closing audit;
janitor ran in almost every session because the planned queue exceeded a fixed
threshold.

Changes adopted with the owner: authoring and review run as separate units,
in-session checks are scoped to the unit and its dependency closure, author units
are larger (twelve primaries, four per writer), one reviewer writes both the
fidelity and the honesty block, source-only stages and statement units have no
closing honesty audit, and janitor runs only for concrete hygiene problems.
Docstrings keep the source's natural-language proof. The author handoff snapshot
became portable and scoped: it previously fingerprinted every node, tooling file
and absolute path, so any other lane's landing invalidated a pending delivery.

Three further defects surfaced while installing this change:

- **In-session statement checks always failed.** An isolated checkout holds only
  its own scoped export, so every dependency's compiled state was approximate and
  each statement unit's in-session stage check reported "statement interface is
  not current and reviewed" for all of its inputs. Leads then spent sessions
  refreshing full exports. Nodes whose source and import closure are
  byte-identical to the canonical workspace now use its compiled facts. Repeated
  YAML parsing (one call parsed every node header three times) is memoized, which
  halves a stage check.
- **Interrupted sessions held finished work.** Runs 0024–0026 were reaped before
  landing. Their preserved checkouts held reviewed locks for seven nodes that
  nothing would land. `horizon sessions land` now finishes the missed boundary
  steps with the normal conflict checks.
- **The critical path was deprioritized.** One session without evidence progress
  lowered `STMT.PrereqIII_Satellites` to priority `low`, behind every other
  task, although 12 waiting Chapter III nodes depend directly on its definitions.
  A task that other unaccepted statements depend on now keeps its priority. Three
  sessions without progress still block it for a decision.

## Evidence locations

The paths below identify local records. Ignored reports and private sources are
not public downloads. Preserve original failures and earlier judgments when
adding a later correction.

| Concern | Local evidence |
| --- | --- |
| Registration, claim, current scope and dispatch | CE checkout `build/ce1956/coordination.json` |
| Full workflow contracts and installation | Implementation checkout `build/workflow-integration/` and `build/workflow-docs/` |
| Backup defect, tests and independent review | Implementation checkout `build/backup-ledger-fix/` |
| Interrupted T7 and actual recovery | CE checkout `build/ce1956/operator-sessions/20261104T102134.661574Z-CartanEilenberg1956.T.7-e5ec56fc/` and `20261104T105559.144270Z-T7-recovery/` |
| Read-reuse measurements and independent checks | Implementation checkout `build/planning-read-optimization/` |
| Actual 13-file read-reuse installation | CE checkout `build/ce1956/workflow-read-optimization-20261104/integration-plan.json` and `integration-receipt.json` |
| Approved source witness and retained proposal | CE checkout `build/ce1956/source-recovery/proposal/adoption-20261104.json` and the frozen proposal beside it |
| Approved III p50 proof-formula repair, separate from witness glyphs | CE checkout `build/ce1956/errata/III_p50_partial_satellite_proof/decision.json`, SHA256 `c3cf7c06a74ac748fbc27abe915496507bcf73cfc7a4459f78326fddc7bb07b0`; relayed as `I-0034` |
| Candidate authorship, historical versions and new independent review | CE checkout `build/ce1956/pretranscribed/T8/`, `T9/`, `T10/` |
| Earlier source-review miss and retained acknowledgment | CE checkout `build/ce1956/pretranscribed/T5/I0026-review-followup-locate_wiki.json` |
| Live draft-worker refusal | CE checkout `build/ce1956/chapter1-statement-drafts/create.json` and `create.stdout` |
| Cancelled outside authoring setup and frozen inputs | CE checkout `build/ce1956/chapter3-drafts/workspace-provisioning.json` and each draft's `handoff.json` |
| Return to native Horizon execution | CE checkout `build/ce1956/native-T10-preparation/launch.json` and native run `0014` |
| First-section satellite design and inventory preparation | CE checkout `build/ce1956/chapter3-preflight/` |
| INV16 compiled-record refresh, repeated finalization and projection | CE checkout `build/ce1956/inv16/`: `make-validate.result.json`, `export-lean.result.json`, `make-validate-retry.result.json`, `after-session.result.json`, `plan-final.result.json` and `projection-audit.json` |
| Chapter comparison and live phase timings | CE checkout `.archon-horizon/runs/0005` through `0016`: native session `meta.json`, source-ledger start/end revisions and reports; `build/ce1956/dag3/*.result.json` and native run0016 `checks/*.json` |
| Later compilation of frozen Chapter III prototypes | CE checkout `build/ce1956/dag3/lean-preparation/{presentations,unary-interfaces,induced-maps}/handoff.json`, with original bytes, actual compiler/audit receipts and remaining source-review boundaries |
| Accepted comparison statements and missing construction certificates | CE checkout `build/ce1956/sprintIII-s19/honesty-frontier.md` and its `honesty-axioms.lean` check receipts; partial native audit at source-ledger `1e3e20df69241aa0c47af784f91d25d7e49eb4a1`, not final acceptance |

Append future experience as a concrete incident, its actual consequence, the
adopted response and evidence. Update the improvement table when a change passes
its acceptance check. Keep historical measurements and failures distinct from
the current operating rule.
