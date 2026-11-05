Inventory chapter {chapter}, section {section}, PDF pages {pages}, of {doc_title} ({doc_key}).

Write scope: {write_scope}. Read only reviewed page transcriptions. Account for
every theorem-like environment in source order, including unnumbered items, in
literature/{doc_key}/inventory.yaml. Every page must be explicitly complete; each
occurrence must be node, informal, or not-an-item with a reason. A node's source
label must agree with the inventory. Do not invent or silently omit source items.

Create planned nodes exclusively through homalg new-node, with correct chapter,
section, printed pages, label and existing tags (run homalg taxonomy find first).
Preserve the source's definitions and hypotheses (P-1), and its proof route (P-2).
Run homalg foundations draft {doc_key} if the boundary is empty. For each draft,
verify whether the source assumes it and supply source evidence before proposing
it; remove suggestions that are not part of this document's boundary. Follow
docs/REVIEW_POLICY.md: when independent-agent review is enabled, request an actual
independent reviewer to inspect and confirm each proposed foundation through
homalg foundations review with distinct --session and --author-session values.
The author must not approve their own proposals or write confirmation fields.
The separate early-review gate uses homalg plan --early-review-ok after its
prerequisites and independent reviews pass. With the policy disabled, retain
the documented human gates. Never invent human confirmations.

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

Inventory and foundation files are shared authored state; parallel preparation
does not authorize concurrent canonical writers or enlarge this task's scope.
