# Fix an existing node

Read the node, its source pages, current review history and local graph comments.
Confirm that the task authorizes its document and file. Keep the permanent id,
filename and namespace. A fix to an importing document must not edit the document
it imports.

```sh
horizon graph -p HomAlg get label:Hochschild1945.Thm_4_1
homalg status --doc Hochschild1945
```

Separate an implementation mistake from a possible source error. Fix transcription
mistakes by returning to the page image and updating the private transcription
through landing and independent review before extracting the corrected text.
For a suspected false statement or broken source proof:

```sh
homalg dispute open Hochschild1945.Thm_4_1 --kind proof \
  --reason 'Describe the exact source step and the obstruction.'
```

Preserve the printed claim and hypotheses. Agents can open a dispute; only humans
can confirm it or resolve it through withdrawal, a published erratum or an approved
proof deviation. Do not weaken a theorem, assume its conclusion or hide a gap in
a new definition.

For a proof repair, follow the source route and its declared proof dependencies.
For a type or definition change, update the source-to-Lean notes and obtain a new
fidelity review. The user override dated 2026-10-28 allows an independent agent
to review an explained deviation under the enabled policy, using distinct
identities and substantive evidence; it does not authorize agents to adjudicate
an unresolved dispute. Existing locks reopen when their source/type hashes differ;
changes to referenced definitions also require checking meaning-hash warnings.
Never hand-edit a review lock or a derived field.

```sh
horizon check HomAlg.Hochschild1945.Thm_4_1
homalg fix-deps Hochschild1945 --out /tmp/homalg-deps-review
homalg unused-imports --doc Hochschild1945
homalg validate --doc Hochschild1945
```

Inspect the dependency mirror before applying `homalg fix-deps Hochschild1945`.
It adds verified dependencies; it does not justify removing a source dependency.
Preserve directly imported declared dependencies even when Lean does not use one.
Use [review-fidelity.md](review-fidelity.md) after changing statements.

An obsolete auxiliary or cited node can be examined with `homalg prune-check
<NodeId>`. Deletion requires its explicit apply operation and a tombstone; never
rename or silently remove a merged source node. Record unfinished proof attempts
as graph comments starting `attempt:`, with the attempted route and precise
obstruction. Commit work to `hgit` during a run and publish only through
[submit.md](submit.md) once the engine is idle.
