# Write a source node

Read [CONVENTIONS.md](../CONVENTIONS.md), [../../HomAlg/AGENTS.md](../../HomAlg/AGENTS.md),
the task objective and the node's existing comments:

```sh
horizon graph -p HomAlg get label:Hochschild1945.Thm_4_1
```

For parallel work, the coordinator assigns an isolated draft checkout, explicit
node ownership and fixed dependencies as described in
[PARALLEL_WORKFLOW.md](../PARALLEL_WORKFLOW.md). Write only in that checkout's
assigned scope. Report a dependency change before continuing downstream work.
Do not share the canonical source tree, ledger or build directory with another
writer merely because the filenames are disjoint.

Open the page images and their reviewed transcriptions under
`references/<DocKey>/`. Use the exact `inventory.yaml` label and permanent id.
Create a node through the scaffold, inside the task's authorized scope:

```sh
homalg new-node Hochschild1945.Thm_4_1 --kind theorem --label 'Theorem 4.1' \
  --chapter 4 --pages 61,62,63 --tags hochschild-cohomology,separable-algebra
```

Check tag ids with `homalg taxonomy find <text>` before using this example.
Reuse vocabulary; append a new id only when existing entries do not fit.
`--section` is optional for articles whose sections are represented as chapters.
An auxiliary node also needs `--parent`, `--aux-kind lemma|technical|bridge` and
`--reason`. External results the document uses without proving belong to `Cited_*`
nodes; use the scaffold's `--cited-kind`, locator and source options.

Keep `decls: []` while the node is planned. Never add an arbitrary proposition,
placeholder structure or hollow definition merely to make a declaration exist.
The header records authored metadata: source, title, tags, concepts, dependencies,
Mathlib correspondence and fidelity. `deps.statement` lists nodes needed to state
the item; `deps.proof` lists the document's proof dependencies. Import each listed
node directly. Derived status, axiom, export and module fields do not belong here.

Fill the Markdown sections in the same module comment:

- `## Statement`: the reviewed source text, preserving hypotheses, quantifiers,
  construction and generality. For a non-English source, also preserve the exact
  original under `## Statement (original)`.
- `## Proof`: the source proof, including proof text preceding the statement or
  spanning pages. Add dependencies as bracketed editorial insertions
  ``[uses `NodeId`]`` after the sentences that use them.
- `## Description`: a short editorial description for search.
- `## Formalization notes`: the source-to-Lean dictionary and justified deviations.

Keep formulas faithful, including printed errors; report errors through `dispute`.
Use only standard LaTeX commands or expand local page macros before extraction.
Footnotes go after the relevant text with `[Footnote n]`. Do not copy whole private
pages into public files. The provenance check compares excerpt paragraphs with
the reviewed page spans.

Declare constants inside `namespace <DocKey>`. The first main declaration's
docstring starts `**<source.label>** (<author>).`; later main declarations name
their part. Preserve the source's construction and record Mathlib counterparts
under `mathlib:`. A `Bridge_*` node can prove agreement. A theorem may have a named,
documented `sorry` during the statement stage; a definition must contain real data.

```sh
horizon check HomAlg.Hochschild1945.Thm_4_1
homalg extract --doc Hochschild1945
homalg validate --fast --doc Hochschild1945
```

Use [review-fidelity.md](review-fidelity.md) to review compiled statements before
locking them. Under the user override dated 2026-10-28, an independent agent may
perform the enabled policy's foundation, first-chapter or explained-deviation
review with documented, distinct author/reviewer identities. Unresolved source
disputes still require a human decision. During proof work follow the document's route and record every
unfinished attempt in a node comment beginning `attempt:`. Report the node's
actual state, including planned declarations and any remaining named `sorry`.

Before independent review, deliver a frozen author handoff with actual identity,
source anchors, exact node/dependency inputs and the real check results. The
handoff does not claim a review that has not happened. After the independent
reports are complete, their final snapshot and registration belong to the
coordinated acceptance phase. Later edits invalidate the affected handoff.

For a registered task, freeze this actual author's subset after it is stable in
the canonical checkout:

```sh
homalg workflow prepare ACTUAL_TASK --author-session ACTUAL_AUTHOR_SESSION \
  --node ACTUAL_NODE_ID --out build/author-delivery-001.json
homalg workflow verify build/author-delivery-001.json
```

Read validation, skipped checks and pending lock renewals. Keep these inputs
unchanged while the real independent reviewer works. After its reports, use
`workflow review-snapshot --node ...` and `review-fidelity-batch` in the exact
snapshot order, as in [PARALLEL_WORKFLOW.md](../PARALLEL_WORKFLOW.md). Separate
actual authors and reviewers into their own deliveries/registration batches.
