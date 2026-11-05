Prove chapter {chapter} of {doc_title} ({doc_key}) along the document's route (P-2).

Nodes: {node_list}. Write scope: {write_scope}.
Read comments first, then use horizon graph -p HomAlg frontier --type tex to
prioritize ready nodes that unlock later work. Preserve every locked statement
(P-1); use the source Proof and declared dependencies. Additional local helpers
must be Aux_/Bridge_ children of scoped parents, created through homalg new-node.
Build only via horizon check. Prune unused auxiliaries through homalg prune-check.
Parallel proof drafts require isolated checkouts, disjoint ownership and fixed
statement/dependency inputs under docs/PARALLEL_WORKFLOW.md. Preserve locks and
report any changed input before integration; a worker build is not a source
review or completion verdict. Coordinate canonical promotion and final checks.

For every node worked on but unfinished in this session, add a comment beginning
attempt: describing the approach, failure and next obstacle. Distinct sessions
count as separate attempts; duplicate comments do not. Suspected source proof
errors require homalg dispute open --kind proof and a local question for the
owner when the mathematical/source disagreement remains unresolved. Explained
formalization deviations follow the independent review policy in
docs/REVIEW_POLICY.md; do not request routine human review when that policy
authorizes an actual independent agent review. Never silently replace the route
or fabricate a human dispute decision. Do not send GitHub issues.
For a stable canonical proof batch needing review or lock renewal, freeze each
actual author's own nodes with homalg workflow prepare {task_id}
--author-session ACTUAL_AUTHOR_SESSION --node <NodeId> [--node ...]
--out build/<unique-author-handoff>.json. Inspect ready_for_review, validation,
skipped checks and pending_review_renewal, then run homalg workflow verify
build/<unique-author-handoff>.json. Dispatch actual independent source-fidelity
and required honesty reviewers; keep the frozen inputs unchanged during review.
After complete satisfactory reports, group by the actual reviewer and run
homalg workflow review-snapshot build/<unique-author-handoff>.json
--node <NodeId> [--node ...] --out build/<unique-review-snapshot>.json, then
homalg review-fidelity-batch <NodeId> [<NodeId> ...] --by ACTUAL_REVIEWER
--session ACTUAL_REVIEW_SESSION --author-session ACTUAL_AUTHOR_SESSION
--snapshot build/<unique-review-snapshot>.json with the exact snapshot order.
Do not fabricate common authorship or independence. Stop on stale or failed
registration and preserve recovery evidence. Single-node review-fidelity remains
compatible. These operations do not turn a retained gap into a proof.

Review any changed statements before relocking. Never fabricate human approvals,
hide sorry in anonymous examples, or package the desired conclusion as a hypothesis.

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
