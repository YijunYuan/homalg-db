Formalize the cited results used in {doc_title} ({doc_key}).

Nodes: {node_list}. Write scope: {write_scope}.
Parallel drafts follow docs/PARALLEL_WORKFLOW.md: isolated checkouts, disjoint
explicit ownership, fixed dependency inputs and frozen handoffs. Every node
retains its actual independent reviewer and current report; batching does not
turn unresolved cited obligations into approved or proved background results.
Read comments and the exact source references. State every cited result faithfully,
with full cited.source metadata; use editorial formulations only when explicitly
marked. Keep each unresolved proof as a named theorem with its source and natural
language proof in the docstring. Attempt a proof and record failures as node comments;
Mathlib reuse is permitted for cited proofs. Never conceal remaining assumptions.
Use horizon check for local iteration. Once an actual author's canonical batch
is stable, run homalg workflow prepare {task_id} --author-session ACTUAL_AUTHOR_SESSION
--node <NodeId> [--node ...] --out build/<unique-author-handoff>.json. Select only
that author's nodes; never invent a shared author session. Inspect ready_for_review,
validation/skipped checks and pending_review_renewal. Verify the handoff with
homalg workflow verify build/<unique-author-handoff>.json before dispatching
source-fidelity-reviewer and honesty-reviewer where required. Freeze the inputs
through their complete independent per-node reports under literature/{doc_key}/reviews/.
After actual satisfactory reports exist, group by the real reviewer and run
homalg workflow review-snapshot build/<unique-author-handoff>.json
--node <NodeId> [--node ...] --out build/<unique-review-snapshot>.json.
Register the same ordered list with homalg review-fidelity-batch <NodeId> [<NodeId> ...]
--by ACTUAL_REVIEWER --session ACTUAL_REVIEW_SESSION
--author-session ACTUAL_AUTHOR_SESSION --snapshot build/<unique-review-snapshot>.json.
Follow docs/REVIEW_POLICY.md; retain distinct true identities and current evidence.
The single-node review-fidelity command remains compatible. Stop on failed or
stale inputs and retain the journal; never invent a verdict or human confirmation.
Do not send public messages during the run.

The native lead provisions isolated writers and lands their frozen handoffs
with `homalg workspaces create --native --task {task_id}` under its actual parent
run/session, normally without copying a build cache. Native-only `workspaces collect
ID --by LEAD` stages uncompiled source after scope/baseline/dependency checks; run
canonical checks/export and ordinary review/acceptance afterward. Checked workers
may use `promote --native`. Workers never collect or promote themselves.
External callers retain the idle-only workflow; do not start nested runs.

Use the mathematical-task validation profile in AGENTS.md: current scoped
checks, required fresh export and independent review, then this task's exact
stage check and the engine-owned outer hook. Do not repeat unchanged tooling/site
regression suites or synthetic Lean smoke tests. Full source Statement/Proof prose,
DAG annotations, metadata, generated-data freshness and blueprint synchronization
remain required. Dispatch all independent ready units before joining results;
keep an unresolved issue or housekeeping task local to its actual dependents.

When homalg stage-check {task_id} exits 0, set this task to done as prescribed.
Preserve the evidence, report the in-session result and return control to Horizon.
This does not complete outer-session acceptance. Do not manually invoke homalg
after-session or add an extra homalg plan --advance in this native session.
Horizon runs the configured outer hook after the lead returns; that hook evaluates
the session and advances eligible planning. The outer coordinator then verifies
its actual private/scope, validation, evaluation and resulting task-state records
before reporting final acceptance.
