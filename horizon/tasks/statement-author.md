Author the Lean statements of these chapter {chapter} nodes of {doc_title} ({doc_key}).
This is an author unit: a separate review unit reviews and registers them later.
Do not run independent review or fidelity registration here.

Nodes, in source order: {node_list}.
Write scope: {write_scope}. Create Aux_<Parent>_* or Bridge_<Parent>_* nodes only
for these parents, through homalg new-node.

For every node:
1. Read its comments (horizon graph -p HomAlg get label:<NodeId>), its reviewed
   source pages and its Statement and Proof sections. Preserve the document's
   objects, hypotheses, generality, variance, module sides and order (AGENTS.md
   P-1). Use Mathlib only inside the foundation boundary of
   literature/{doc_key}/document.yaml and record counterparts under mathlib.
2. Fill the main declarations and decls. Each theorem gets a named `by sorry`
   proof; its docstring states the result with its source label and page and gives
   the source's natural-language proof. Definitions contain their actual data and
   operations; a certificate needed for that data is proved, not deferred.
3. Record deps.statement and deps.proof with the matching explicit imports.

Dispatch one node-writer per author group listed below, all at once, each in an
isolated worker: homalg workspaces create --native --task {task_id} --author
<writer session> --file <its node files>. Collect each delivery with homalg
workspaces collect <id> --by <your session>; writers never collect themselves.

Checks stay scoped to this unit; the engine's outer hook validates the whole
document after the session:
- homalg validate --file <node file> ... catches header and metadata errors cheaply;
- horizon check <the unit's modules>;
- homalg workflow prepare-batch {task_id} --authors build/<authors>.json --out
  build/<handoff>.json, one entry per actual writer session with its node_ids
  (homalg workflow prepare for a single writer). Fix and prepare again until
  ready_for_review is true;
- homalg stage-check {task_id}; when it exits 0, set this task to done. That
  records the in-session result; outer-session acceptance follows in the engine's
  hook after you return.

A node you cannot deliver stays out of the handoff with a node comment explaining
why; do not mark the task done, the outer hook accepts the delivered nodes. A
suspected false statement goes through homalg dispute open --kind statement. For a
node with an open proof dispute eligible under docs/AGENT_PROOF_ERRATA.md, deliver
its statement first, then follow that route. Never edit generated blueprint/. Do not
run make test/validate/site, homalg after-session or homalg plan --advance.
