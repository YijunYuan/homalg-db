State the {kind_group} of chapter {chapter} of {doc_title} ({doc_key}) faithfully in Lean.

Nodes, in source order: {node_list}. Write scope: {write_scope}.
You may create Aux_<Parent>_* and Bridge_<Parent>_* only for these parents,
through homalg new-node. Dispatch node-writer subagents for independent nodes.
For parallel authorship follow docs/PARALLEL_WORKFLOW.md: assign an isolated draft
checkout and disjoint node ownership, using fixed dependencies. A shared live
checkout is not isolation. Freeze author handoffs before independent review and
freeze completed reports separately before coordinated registration. Preserve
actual per-node author/reviewer identities and recheck all reviewed inputs.
Source-only workers must not invoke Lean LSP/diagnostics, which can trigger cold
dependency bootstrap. For early typechecks, the lead may use the warm canonical
horizon check --lean ABSOLUTE_FROZEN_CANDIDATE lane while other authors continue.
Candidate compilation does not replace canonical checks after collection.

1. Read every node's comments with horizon graph -p HomAlg get label:<NodeId>.
2. Read its reviewed source pages and Statement. Preserve the document's objects,
   hypotheses, generality and order (P-1). Mathlib is available only for notions
   inside literature/{doc_key}/document.yaml's foundation boundary. Record a
   counterpart under mathlib; do not substitute the counterpart for the source.
   A synthetic document's source is docs/fixtures/{doc_key}.md, with page markers;
   it has no private PDF or page images.
3. Fill the main declarations and decls. In this STMT task, ordinary theorem
   result proofs may remain deferred as named `by sorry` proofs, with the source's
   natural-language proof in their docstrings, for the separate PROOF task.
   This permission does not cover certificates needed to provide the submitted
   construction's actual data, operations, well-definedness or required instances,
   even when packaged as a named theorem or inferred local instance. Native source
   and honesty reviewers determine the certificate's actual dependency and use;
   its syntactic declaration kind alone does not decide this. An unmet certificate
   blocks only dependent work. Definitions must contain their actual data and
   operations, never hollow placeholders. Unrelated theorem result proofs remain
   deferred.
4. Use horizon check on the scoped modules for local iteration. After metadata or
   import edits, run cheap current schema/import checks before expensive handoff
   preparation; retain any failure and still run the full fresh preparation.
   When a bounded
   author batch is stable in the canonical checkout, use homalg workflow prepare-batch
   {task_id} --authors build/<actual-authors>.json --out build/<unique-handoff>.json
   to share one fresh export/validation. The JSON array has one object per actual
   author with author_session and explicit disjoint node_ids; follow the example in
   docs/PARALLEL_WORKFLOW.md. A single author may instead use workflow prepare
   {task_id} --author-session ACTUAL_AUTHOR_SESSION --node <NodeId> [--node ...]
   --out build/<unique-handoff>.json. Never invent a shared author session. Read ready_for_review,
   validation/skipped checks and pending_review_renewal before continuing.
5. Run homalg workflow verify build/<unique-handoff>.json
   --author-session ACTUAL_AUTHOR_SESSION for each actual author, then dispatch
   source-fidelity-reviewer and, for structures/classes/instances or
   field-extraction proofs, honesty-reviewer. Keep the frozen inputs unchanged
   while they inspect every assigned node and append real dated, session-attributed
   blocks with Status, Verdict, comparison tables and severity-tagged evidence.
   When honesty review is required or included, each registering source reviewer
   must also perform and record their own honesty assessment under that same
   actual session. Preserve specialist reports separately; never relabel them.
6. Follow docs/REVIEW_POLICY.md. With several actual author/reviewer groups, use
   docs/REVIEW_COHORTS.md: write the strict actual-identity manifest, run
   homalg workflow review-snapshot-cohorts build/<unique-handoff>.json
   --cohorts build/<actual-cohorts>.json --out build/<unique-review-cohorts>.json,
   then homalg review-fidelity-cohorts --snapshot build/<unique-review-cohorts>.json.
   Every included author's complete delivery must be covered; a ready subset of
   whole author deliveries may proceed while others remain pending. Preserve all
   genuine required reviews and the whole task's eventual completion obligations.
   Use a short Login such as source-r1 (letters, digits and hyphens, no underscores);
   put the full actual reviewer identity in session. For a single identity group,
   after satisfactory reviews exist, use the compatible commands instead:
   homalg workflow review-snapshot build/<unique-handoff>.json
   --author-session ACTUAL_AUTHOR_SESSION
   --node <NodeId> [--node ...] --out build/<unique-review-snapshot>.json,
   grouping by the actual independent reviewer session. Register that exact
   ordered list with homalg review-fidelity-batch <NodeId> [<NodeId> ...]
   --by ACTUAL_REVIEWER --session ACTUAL_REVIEW_SESSION
   --author-session ACTUAL_AUTHOR_SESSION --snapshot build/<unique-review-snapshot>.json.
   Keep per-node reports and genuine author/reviewer separation. A failed or
   stale snapshot/registration stops this batch; preserve its evidence. The
   single-node review-fidelity command remains compatible, not the batch default.
   If no independent reviewer is available, use the local inbox. With the policy
   disabled retain documented human gates. Never write protected human fields
   or treat agent review as GitHub owner approval.
7. A suspected false statement goes through homalg dispute open --kind statement;
   unreadable pages go to the document-error inbox. Do not weaken the statement.
8. Record failed approaches as node comments. Never edit generated blueprint/.

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

After final integration and registration, retain gen-roots, extract, blueprint-tex
and graph sync. Use export-lean --doc {doc_key} with its default canonical output,
then one full validate --doc {doc_key} --export build/lean-export-{doc_key}.json
without --no-build, the exact stage check and actual source-ledger scope checks.
Stage-check reads that canonical path; exporting only to a custom archive can
cause it to repeat the export. Copy successful canonical output to ignored session
evidence if needed. Preserve full findings/skips: stage-check alone does not
replace that full supplied-export validation. Do not alter timestamps or suppress
an existing stale-input/identical-output refresh to avoid a check.

When homalg stage-check {task_id} exits 0, set this task to done as prescribed.
Preserve the evidence, report the in-session result and return control to Horizon.
This does not complete outer-session acceptance. Do not manually invoke homalg
after-session or add an extra homalg plan --advance in this native session.
Horizon runs the configured outer hook after the lead returns; that hook evaluates
the session and advances eligible planning. The outer coordinator then verifies
its actual private/scope, validation, evaluation and resulting task-state records
before reporting final acceptance. A successful worker check or registration is
not a substitute for these gates.
