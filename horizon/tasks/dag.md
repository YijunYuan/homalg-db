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

Done when homalg stage-check {task_id} exits 0. Then set this task to done.
