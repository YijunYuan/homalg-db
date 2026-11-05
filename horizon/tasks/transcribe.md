Visually transcribe PDF pages {pages} of {doc_title} ({doc_key}).

Write scope: {write_scope}. Read the rendered images in references/{doc_key}/pages/.
Dispatch page-transcriber with a vision-capable model, preferably {transcriber_model},
at most five consecutive pages per dispatch. Never read text/ or use OCR as a source.
Keep every formula, quantifier, sign, subscript, condition and footnote; retain the
source's notation. Unreadable text stays marked % [illegible]. Include the required
source/pdf_page/retrieved/transcribed_by headers and only this page's LaTeX macros.
Parallel preparation may use explicitly assigned ignored staging only. Keep exact
PDF/PNG/TeX hashes and real author/reviewer identities. A staged review can be
reused at authorized import only for identical inputs after a complete actual
independent visual comparison; hash checking itself is not review. Follow
docs/PARALLEL_WORKFLOW.md and preserve the task's registered page scope.

Land the files with homalg transcription land {doc_key} --pages <range> --session
"$ARCHON_HORIZON_SESSION". Dispatch a separate transcription-fidelity-reviewer
to compare the images and delivered files. Record its five-level verdict with
homalg transcription review. An ambiguous source requires human adjudication;
do not resolve it or modify human evidence yourself.

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
