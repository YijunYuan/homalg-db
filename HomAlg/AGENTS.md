# Lean node instructions

Read the repository [AGENTS.md](../AGENTS.md), [CONVENTIONS.md](../docs/CONVENTIONS.md)
and the relevant [playbook](../docs/playbooks/write-node.md). A Horizon task's
explicit file scope is binding. Node files are flat:
`HomAlg/<DocKey>/<LocalId>.lean`, id `<DocKey>.<LocalId>`, declarations inside
`namespace <DocKey>`. Create nodes with `homalg new-node`; never rename merged ids.

The first module comment contains a fenced `yaml node` header followed by
Markdown sections. A planned header has this shape; use real registered values
and let the scaffold fill the required schema fields:

```yaml
id: Example2000.Thm_1
doc: Example2000
kind: theorem
title: A descriptive title
source: {label: Theorem 1, chapter: "1", pages: [1]}
tags: [cohomology]
concepts: {defines: [], uses: []}
deps: {statement: [], proof: []}
decls: []
mathlib: {relation: none, decls: []}
fidelity: {status: faithful}
```

Keep source hypotheses, generality, definitions and proof route. Never replace a
document item by its Mathlib counterpart. Record correspondence under `mathlib:`
and prove agreement in a `Bridge_*` node when useful. Mathlib may supply approved
foundations and elementary proof steps; unproved external results used by the
document require `Cited_*` nodes. Auxiliary nodes have an explicit parent and
reason. Never package a theorem's conclusion as a structure field and call a
projection its proof.

`## Statement` and `## Proof` reproduce reviewed source text with the permitted
transcription changes. Add ``[uses `NodeId`]`` after proof sentences that use a
dependency. Keep `## Description` editorial, concise and searchable. Explain
representative choices and deviations in `## Formalization notes`. A non-English
document also needs `## Statement (original)`. Every source page must have a
current satisfactory private transcription review. Never copy extracted text,
OCR output or whole private page files into a node.

The first main declaration's docstring starts `**<source.label>** (<author>).`.
Other main declarations name their part; auxiliary and bridge declarations name
their parent. Keep every declaration listed in `decls` present and correctly
namespaced. Planned nodes retain `decls: []`; definitions contain real data.
Every `sorry` belongs to a named theorem with source and a natural-language proof.

Inside a run, build through `horizon check HomAlg.<DocKey>.<LocalId>`. HomAlg build
and export commands share its workspace lock. Do not invoke `lake build` directly
during a run. Keep imports consistent with both dependency lists. Never edit
generated root modules, `nodes.json`, `blueprint/` or `hgraph/config.yaml` by hand.

A changed statement reopens its review. Use the five review statuses and fresh
compiled evidence before locking. The user's explicit override dated 2026-10-28
allows independent agent review for foundations, first-chapter checkpoints and
explained deviations when `horizon/review-policy.yaml` enables it. Use the review
commands in the playbook with actual, distinct author and reviewer sessions and
matching report provenance. Agent confirmations remain labelled as agent reviews.
Unresolved disputes still require a human decision: agents may open disputes but
must not confirm or resolve them, invoke human review options or manually write
protected confirmation fields. Questions and failed attempts belong in local
graph comments and the inbox. Formalization sessions commit only to `hgit`, never
the user's `.git`; submission happens after the engine is idle.
