State the {kind_group} of chapter {chapter} of {doc_title} ({doc_key}) faithfully in Lean.

Nodes, in source order: {node_list}. Write scope: {write_scope}.
You may create Aux_<Parent>_* and Bridge_<Parent>_* only for these parents,
through homalg new-node. Dispatch node-writer subagents for independent nodes.

1. Read every node's comments with horizon graph -p HomAlg get label:<NodeId>.
2. Read its reviewed source pages and Statement. Preserve the document's objects,
   hypotheses, generality and order (P-1). Mathlib is available only for notions
   inside literature/{doc_key}/document.yaml's foundation boundary. Record a
   counterpart under mathlib; do not substitute the counterpart for the source.
3. Fill the main declarations and decls. Each unresolved theorem is named and
   carries the source's natural-language proof in its docstring. No hollow definitions.
4. Build only with horizon check HomAlg.{doc_key}.<LocalId>.
5. Dispatch source-fidelity-reviewer and, for structures/classes/instances or
   field-extraction proofs, honesty-reviewer. Append dated, session-attributed
   blocks with Status, Verdict, comparison tables and severity-tagged evidence.
6. Only after the latest reviews are satisfactory, run homalg review-fidelity
   <NodeId> --by {login} --session "$ARCHON_HORIZON_SESSION". Foundation/deviating
   statements need a human lock; request it through the local inbox and continue
   other eligible work. Never write protected human fields yourself.
7. A suspected false statement goes through homalg dispute open --kind statement;
   unreadable pages go to the document-error inbox. Do not weaken the statement.
8. Record failed approaches as node comments. Never edit generated blueprint/.

Done when homalg stage-check {task_id} exits 0. Then set this task to done.
