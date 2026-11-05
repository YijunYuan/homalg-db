Record the source's dependency structure for chapter {chapter} of {doc_title} ({doc_key}).

Nodes: {node_list}. Write scope: {write_scope}.
Read node comments and reviewed page transcriptions first. Transcribe definitions
into Statement and theorem proofs into Proof without changing their hypotheses,
generality, notation or proof route (P-1/P-2). Editorial references [uses `NodeId`]
must exactly match deps.proof; statement dependencies belong in deps.statement.
Create Aux_/Bridge_ nodes only for these parents through homalg new-node. Results
used but not proved by the source require Cited_ skeletons with complete source
metadata and used_at pages; never smuggle such a result into the foundation boundary.
Never edit generated blueprint/ or hgraph/config.yaml. Report unclear source
pages through the local inbox and suspected false statements through homalg dispute open.

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

Freeze dependency handoffs for downstream workers; a later DAG change requires
reassessing affected drafts.
