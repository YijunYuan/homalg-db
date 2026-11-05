Independently review and register the delivered Lean statements of these chapter
{chapter} nodes of {doc_title} ({doc_key}). Their authors delivered them in
earlier author units; this review unit carries the statement acceptance gate.

Nodes: {node_list}.
Write scope: {write_scope}.
Recorded author deliveries:
{handoff_list}

1. homalg workflow handoffs {task_id} --copy build/handoffs-{task_id} copies the
   deliveries and reports which are current. A stale delivery cannot be
   registered: leave its nodes unlocked and continue with the rest.
2. Dispatch source-fidelity-reviewer subagents at once, about four to six nodes
   each, never a node's own author. Each reviewer compares every assigned node with
   its reviewed source pages and the definitions it uses, then appends one dated
   block per node to literature/{doc_key}/reviews/<Local>.md with Status, Verdict,
   Session (the reviewer's actual session), Author-session (the node's author from
   its delivery) and a comparison table. For a node with a structure, class or
   instance, or a construction certificate, the same reviewer appends the honesty
   block in the same session. There is no separate honesty reviewer.
3. When a reviewer finds a mismatch, dispatch a node-writer under a new author
   session to fix it, deliver the node again with homalg workflow prepare, and have
   a different reviewer review the new bytes.
4. Register per actual reviewer: homalg workflow review-snapshot <copied delivery>
   --author-session <author> --node <NodeId> ... --out build/<snapshot>.json, then
   homalg review-fidelity-batch <NodeId> ... --by <short id such as source-r1>
   --session <reviewer session> --author-session <author> --snapshot
   build/<snapshot>.json. Several authors per reviewer: docs/REVIEW_COHORTS.md.
5. homalg stage-check {task_id}; when it exits 0, set this task to done. That
   records the in-session result; outer-session acceptance follows in the engine's
   hook. Nodes that fail review stay unlocked; the outer hook accepts the others.

Never invent an author or reviewer identity or a verdict. Do not run make
test/validate/site, homalg after-session or homalg plan --advance.
